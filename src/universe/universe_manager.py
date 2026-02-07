import asyncio
import json
import os
import sys
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Optional, Dict, Any
import glob

from .symbol_generator import SymbolGenerator

logger = logging.getLogger("UniverseManager")


class UniverseManager:
    """
    Universe manager responsible for:
    - Building a daily universe snapshot using filtered symbols.
    - Loading cached universe snapshots.
    - Integrating with SymbolGenerator for high-availability symbol sourcing.
    - Implementing robust recovery for missing/corrupted data.
    """

    def __init__(
        self,
        provider_engine,
        market: str = "kr_stocks",
        min_price: int = 4000,
        min_count: int = 1000,
        data_dir: Optional[str] = None,
    ) -> None:
        self.engine = provider_engine
        # [Requirement] Market code management
        market_code = os.getenv("MARKET_CODE", "kr")
        self.market = f"{market_code}_stocks"
        self.min_price = int(min_price)
        self.min_count = int(min_count)
        
        # [Requirement] Environment-based unified path management
        from observer.paths import observer_data_dir, snapshot_dir
        self.base_path = Path(data_dir) if data_dir else observer_data_dir()
        
        # If data_dir is provided, we assume it's the base directory and snapshots go to base/universe
        # This aligns with SymbolGenerator's behavior.
        if data_dir:
            self.universe_dir = self.base_path / "universe"
        else:
            self.universe_dir = snapshot_dir()
        
        # [Requirement] Validate directory existence and write permission
        # NOTE: Directory creation is handled by K8s initContainer
        # App does NOT create directories - only validates existence
        try:
            if not self.universe_dir.exists():
                logger.critical(f"[FATAL] 디렉토리 없음: {self.universe_dir}. K8s initContainer가 생성해야 합니다.")
                sys.exit(1)
            
            # Explicit check for write permissions
            test_file = self.universe_dir / ".write_test"
            test_file.touch()
            test_file.unlink()
        except (PermissionError, OSError) as e:
            logger.critical(f"[FATAL] 권한 부족: 관리자에게 {self.universe_dir} 폴더의 쓰기 권한 부여 요청 필요. Error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.critical(f"[FATAL] Failed to initialize universe directory: {e}")
            sys.exit(1)
        
        # Initialize SymbolGenerator
        # This will also perform its own path check
        self.symbol_gen = SymbolGenerator(self.engine, base_dir=str(self.base_path))
        
        # [Requirement] Cleanup old universe files (14 days to cover 5 business days)
        self._cleanup_old_universe_files()
        
        # [Requirement] Setup logging to file
        self._setup_logger()
        
        logger.info(f"UniverseManager initialized at {self.universe_dir}")
        print(f"[UniverseManager] initialized. universe_dir={self.universe_dir}")
        sys.stdout.flush()

    def _setup_logger(self) -> None:
        """Setup file logger for UniverseManager and SymbolGenerator"""
        try:
            from observer.paths import observer_log_dir
            
            # logs/universe/YYYYMMDD.log
            today_str = datetime.now().strftime("%Y%m%d")
            log_dir = observer_log_dir() / "universe"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / f"{today_str}.log"
            
            handler = logging.FileHandler(log_file, encoding='utf-8')
            handler.setFormatter(logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
            ))
            
            # Attach to UniverseManager logger
            logger.addHandler(handler)
            
            # Attach to SymbolGenerator logger as well (tightly coupled)
            logging.getLogger("SymbolGenerator").addHandler(handler)
            
            logger.info(f"Universe file logger initialized: {log_file}")
            
        except Exception as e:
            logger.error(f"Failed to setup universe file logger: {e}")

    # ----------------------- Public APIs -----------------------
    def get_current_universe(self) -> List[str]:
        """Load today's universe list; falls back up to 7 days in reverse (Holiday support)."""
        today = date.today()
        
        # [Requirement] Scan up to 14 days reverse to find the most recent valid universe file
        # This handles weekends and long public holidays (e.g., Chu-seok).
        for i in range(15):  # 0 to 14 days
            scan_date = today - timedelta(days=i)
            date_str = scan_date.strftime("%Y%m%d")
            
            # Match both kr_stocks, k3_stocks, etc. using generalized pattern
            # But prioritize current MARKET_CODE if possible
            pattern = f"{date_str}*_stocks.json"
            files = list(self.universe_dir.glob(pattern))
            
            if files:
                files.sort(reverse=True)
                if i == 0:
                    logger.info(f"Today's universe found: {files[0].name}")
                else:
                    logger.warning(f"[FAILOVER] {i}일 전 유니버스({files[0].name})를 로드합니다 (공휴일 대응)")
                
                return self._load_universe_list_from_path(files[0])

        # Priority 4: Final Fallback - Find the absolute latest valid snapshot regardless of date
        latest_snapshot = self._find_latest_snapshot()
        if latest_snapshot:
            logger.warning(f"Universe data missing for last 14 days. Falling back to absolute latest snapshot: {latest_snapshot}")
            return self._load_universe_list_from_path(latest_snapshot)
            
        return []

    def load_universe(self, day: str | date | datetime) -> List[str]:
        """Load universe list for the given day."""
        dt = self._as_date(day)
        symbols = self._try_load_universe_list(dt)
        return symbols or []

    async def create_daily_snapshot(self, day: str | date | datetime) -> str:
        """
        Create daily universe snapshot using latest symbols from SymbolGenerator.
        Returns the written file path.
        """
        target_date = self._as_date(day)
        prev_trading = self._previous_trading_day(target_date)

        # 1. Load latest symbols via SymbolGenerator (Robust recovery inside)
        candidates = await self._load_robust_candidates()
        if not candidates:
            # Fallback check: even if load_robust_candidates returns empty, 
            # try to get absolute latest symbol file as a last resort
            logger.warning("No candidates from _load_robust_candidates. Checking local symbol storage.")
            latest_symbol_file = self.symbol_gen.get_latest_symbol_file()
            if latest_symbol_file:
                with open(latest_symbol_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    candidates = data.get("symbols", [])
            
            if not candidates:
                raise ValueError("No candidate symbols available from any source.")

        # 2. Filter symbols by price
        selected: List[str] = []
        failed_symbols: List[tuple] = []  # (symbol, error_type, error_msg)
        sem = asyncio.Semaphore(15)  # Optimized concurrency
        processed_count = 0
        total_candidates = len(candidates)

        async def fetch_and_filter(sym: str) -> None:
            nonlocal processed_count
            async with sem:
                try:
                    # Filter uses previous trading day's close
                    data = await self.engine.fetch_daily_prices(sym, days=2)
                    close = self._extract_prev_close(data, symbol=sym)

                    if close is not None and close >= self.min_price:
                        selected.append(sym)
                except Exception as e:
                    failed_symbols.append((sym, type(e).__name__, str(e)[:50]))
                    logger.debug("Symbol %s filter failed: %s", sym, e)
                finally:
                    processed_count += 1
                    if processed_count % 100 == 0:
                        logger.info("Universe build: %d/%d processed (selected=%d, failed=%d)...",
                                    processed_count, total_candidates, len(selected), len(failed_symbols))

        await asyncio.gather(*(fetch_and_filter(s) for s in candidates))

        # Log aggregated failure summary
        if failed_symbols:
            logger.warning("[DAILY] Universe build completed with %d/%d symbols failed. Sample failures: %s",
                           len(failed_symbols), total_candidates, failed_symbols[:5])

        # Check size constraint
        if len(selected) < self.min_count:
            logger.warning(f"Universe size ({len(selected)}) below min_count ({self.min_count}).")

        # 3. Save snapshot
        snapshot = {
            "metadata": {
                "date": target_date.isoformat(),
                "market": self.market,
                "filter_criteria": {
                    "min_price": self.min_price,
                    "prev_trading_day": prev_trading.isoformat(),
                },
                "generated_at": datetime.now().isoformat(),
                "count": len(selected),
            },
            "symbols": sorted(selected),
        }

        path = self._snapshot_path(target_date)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Daily snapshot created: {path} ({len(selected)} symbols)")
        print(f"[UniverseManager] Daily snapshot created: {path} (count={len(selected)})")
        sys.stdout.flush()
        return str(path)

    # ----------------------- Internals -----------------------

    async def _load_robust_candidates(self) -> List[str]:
        """Load symbols from today's collection or fallback to most recent valid file."""
        tag = "DAILY"
        
        # [Requirement] 1단계: 심볼 데이터가 아예 없으면 SymbolGenerator를 직접 await 하여 강제 생성
        should_collect, existing_symbol_path = self.symbol_gen.should_collect()
        if should_collect:
            logger.info(f"[{tag}] No valid symbols found. Forcefully executing SymbolGenerator...")
            symbol_file = await self.symbol_gen.execute()
            
            # [Requirement] 물리적 파일 존재 여부 확인 (Cold Start 검증)
            if not symbol_file or not Path(symbol_file).exists():
                logger.error(f"[{tag}] ❌ Symbol file generation failed or file not found on disk: {symbol_file}")
            else:
                logger.info(f"[{tag}] ✅ Symbol file verified on disk: {symbol_file}")
                
                # [Requirement] 연쇄 생성: 심볼 확보 직후 당일 유니버스 파일이 없으면 즉시 생성 트리거
                today_str = date.today().strftime("%Y%m%d")
                pattern = f"{today_str}_{self.market}.json"
                if not (self.universe_dir / pattern).exists():
                    logger.info(f"[{tag}] ⚡ Chain Reaction: Today's universe missing. Triggering immediate creation...")
                    await self.create_daily_snapshot(date.today())
        
        # A. Attempt today's generation
        try:
            logger.info(f"[{tag}] Generating/Loading today's symbol candidates...")
            print(f"[{tag}] Starting symbol candidate generation through SymbolGenerator...")
            sys.stdout.flush()
            await self.symbol_gen.generate_daily_symbols()
        except Exception as e:
            logger.warning("[%s] [RECOVERY] Today's symbol generation failed: %s (type=%s). Attempting history search...",
                           tag, e, type(e).__name__, exc_info=True)

        # B. Robust fallback: find most recent valid file (AM or PM)
        latest_file = self.symbol_gen.get_latest_symbol_file()
        if latest_file:
            logger.info(f"[{tag}] Using symbol source: {latest_file}")
            try:
                with open(latest_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    file_date = data.get("metadata", {}).get("date")
                    today_str = date.today().strftime("%Y%m%d")
                    if file_date != today_str:
                        logger.warning(f"[{tag}] [RECOVERY] Today's data missing. Using past data from {file_date}")

                    symbols = data.get("symbols", [])
                    print(f"[{tag}] Loaded {len(symbols)} robust candidates from {latest_file}")
                    sys.stdout.flush()
                    return symbols
            except json.JSONDecodeError as e:
                logger.error("[%s] [RECOVERY] Latest symbol file %s contains invalid JSON: line %d, col %d",
                             tag, latest_file, e.lineno, e.colno)
            except (IOError, OSError) as e:
                logger.error("[%s] [RECOVERY] Cannot read latest symbol file %s: %s (type=%s)",
                             tag, latest_file, e, type(e).__name__)
            except Exception as e:
                logger.error("[%s] [RECOVERY] Unexpected error reading latest symbol file %s: %s (type=%s)",
                             tag, latest_file, e, type(e).__name__, exc_info=True)
        
        logger.error(f"[{tag}] ❌ [CRITICAL] No valid symbol file found in historical storage.")
        return []

    def _cleanup_old_universe_files(self):
        """
        Delete universe files older than 14 days based on YYYYMMDD filename pattern.
        """
        tag = "DAILY"
        cutoff_date = (datetime.now() - timedelta(days=14)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Match any market identifier *_stocks.json
        files = list(self.universe_dir.glob("*_stocks.json"))
        
        deleted_count = 0
        for filepath in files:
            # Pattern: YYYYMMDD_market_stocks.json
            try:
                date_str = filepath.name.split("_")[0]
                if len(date_str) == 8:
                    file_date = datetime.strptime(date_str, "%Y%m%d")
                    if file_date < cutoff_date:
                        filepath.unlink()
                        deleted_count += 1
                        logger.info(f"[{tag}] Cleanup: Removed old universe file {filepath.name}")
            except (ValueError, IndexError, OSError) as e:
                logger.debug(f"[{tag}] Cleanup skip or error for {filepath.name}: {e}")
                continue
                
        if deleted_count > 0:
            logger.info(f"[{tag}] Cleaned up {deleted_count} old universe files (14-day policy).")

    def _snapshot_path(self, day: date) -> Path:
        ymd = day.strftime("%Y%m%d")
        filename = f"{ymd}_{self.market}.json"
        return self.universe_dir / filename

    def _try_load_universe_list(self, day: date) -> Optional[List[str]]:
        path = self._snapshot_path(day)
        if path.exists():
            return self._load_universe_list_from_path(path)
        return None

    def _load_universe_list_from_path(self, path: Path | str) -> List[str]:
        tag = "DAILY"
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            return payload.get("symbols", [])
        except Exception as e:
            logger.error(f"[{tag}] [ERROR] Failed to load universe list from {path}: {e}")
            return []

    def _find_latest_snapshot(self) -> Optional[Path]:
        # Generalized pattern to match any market identifier
        files = list(self.universe_dir.glob("*_stocks.json"))
        if not files:
            return None
        files.sort(reverse=True)
        return files[0]

    def _as_date(self, day: str | date | datetime) -> date:
        if isinstance(day, datetime): return day.date()
        if isinstance(day, date): return day
        try:
            return datetime.fromisoformat(day).date()
        except ValueError:
            # Handle YYYYMMDD compact format
            if len(str(day)) == 8:
                return datetime.strptime(str(day), "%Y%m%d").date()
            raise

    def _previous_trading_day(self, target: date) -> date:
        """
        Calculate target trading day based on execution time.
        - Before 09:00 AM: Market hasn't opened. Target 'Day before yesterday' or latest.
        - After 04:00 PM (16:00): Market closed today. Target 'Today'.
        - Otherwise (Daytime): Target 'Yesterday'.
        """
        now = datetime.now()
        current_date = now.date()
        
        # Adjust target based on current time
        effective_target = target
        if target == current_date:
            if now.hour < 9:
                # Before market open, target the day before yesterday's data
                effective_target = target - timedelta(days=1)
            elif now.hour >= 16:
                # After market close, today's data is the target
                return target

        # Standard previous weekday logic
        td = effective_target - timedelta(days=1)
        while td.weekday() >= 5: # Skip Sat(5), Sun(6)
            td -= timedelta(days=1)
        return td

    def _extract_prev_close(self, payload: Any, symbol: Optional[str] = None) -> Optional[int]:
        """Defensive extraction of close price with detailed error logging."""
        tag = "DAILY"
        if not isinstance(payload, list) or not payload:
            return None
        try:
            first_entry = payload[0]
            instruments = first_entry.get("instruments", [])
            if not instruments:
                return None
            
            price_data = instruments[0].get("price", {})
            close = price_data.get("close")
            
            if close is None:
                logger.debug(f"[{tag}] [DATA_GAP] Symbol {symbol}: 'close' field missing in price data.")
                return None
                
            return int(close)
            
        except (KeyError, IndexError, TypeError, ValueError) as e:
            logger.warning(f"[{tag}] [PARSING_ERROR] Symbol {symbol}: Unexpected data structure. Error: {type(e).__name__} - {e}")
            return None
        except Exception as e:
            logger.error(f"[{tag}] [UNEXPECTED_ERROR] Symbol {symbol}: {e}")
            return None
