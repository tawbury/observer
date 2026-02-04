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
        min_count: int = 100,
        data_dir: Optional[str] = None,
    ) -> None:
        self.engine = provider_engine
        self.market = market
        self.min_price = int(min_price)
        self.min_count = int(min_count)
        
        # [Requirement] Environment-based unified path management
        from observer.paths import observer_data_dir
        self.base_path = Path(data_dir) if data_dir else observer_data_dir()
        self.universe_dir = self.base_path / "universe"
        
        # [Requirement] Hard-fail on directory creation issues with specific message
        try:
            self.universe_dir.mkdir(parents=True, exist_ok=True)
            # Explicit check for write permissions
            test_file = self.universe_dir / ".write_test"
            test_file.touch()
            test_file.unlink()
        except (PermissionError, OSError) as e:
            logger.critical(f"[FATAL] 권한 부족: 관리자에게 {self.base_path} 폴더의 쓰기 권한 부여 요청 필요. Error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.critical(f"[FATAL] Failed to initialize universe directory: {e}")
            sys.exit(1)
        
        # Initialize SymbolGenerator
        # This will also perform its own path check
        self.symbol_gen = SymbolGenerator(self.engine, base_dir=str(self.base_path))
        
        logger.info(f"UniverseManager initialized at {self.universe_dir}")
        print(f"[UniverseManager] initialized. universe_dir={self.universe_dir}")
        sys.stdout.flush()

    # ----------------------- Public APIs -----------------------
    def get_current_universe(self) -> List[str]:
        """Load today's universe list; falls back to last available snapshot."""
        today = date.today()
        symbols = self._try_load_universe_list(today)
        if symbols:
            return symbols
            
        # Fallback: Find the latest valid snapshot
        latest_snapshot = self._find_latest_snapshot()
        if latest_snapshot:
            logger.warning(f"Today's universe not found. Falling back to latest snapshot: {latest_snapshot}")
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
            raise ValueError("No candidate symbols available from any source.")

        # 2. Filter symbols by price
        selected: List[str] = []
        sem = asyncio.Semaphore(15) # Optimized concurrency
        processed_count = 0
        total_candidates = len(candidates)

        async def fetch_and_filter(sym: str) -> None:
            nonlocal processed_count
            async with sem:
                try:
                    # Filter uses previous trading day's close
                    data = await self.engine.fetch_daily_prices(sym, days=2)
                    close = self._extract_prev_close(data)
                    
                    if close is not None and close >= self.min_price:
                        selected.append(sym)
                except Exception as e:
                    logger.debug(f"Symbol {sym} filter failed: {e}")
                finally:
                    processed_count += 1
                    if processed_count % 100 == 0:
                        logger.info(f"Universe build: {processed_count}/{total_candidates} processed...")

        await asyncio.gather(*(fetch_and_filter(s) for s in candidates))

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
    def _get_tag(self) -> str:
        """Helper to get current time tag."""
        now = datetime.now()
        if now.hour < 12: return "AM"
        return "PM"

    async def _load_robust_candidates(self) -> List[str]:
        """Load symbols from today's collection or fallback to most recent valid file."""
        tag = self._get_tag()
        # A. Attempt today's generation
        try:
            logger.info(f"[{tag}] Generating/Loading today's symbol candidates...")
            print(f"[{tag}] Starting symbol candidate generation through SymbolGenerator...")
            sys.stdout.flush()
            await self.symbol_gen.generate_daily_symbols()
        except Exception as e:
            logger.warning(f"[{tag}] [RECOVERY] Today's symbol generation failed: {e}. Attempting history search...")

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
                        logger.warning(f"[{tag}] ⚠️ [RECOVERY] Today's data missing. Using past data from {file_date}")
                    
                    symbols = data.get("symbols", [])
                    print(f"[{tag}] Loaded {len(symbols)} robust candidates from {latest_file}")
                    sys.stdout.flush()
                    return symbols
            except Exception as e:
                logger.error(f"[{tag}] [RECOVERY] Failed to read latest symbol file {latest_file}: {e}")
        
        logger.error(f"[{tag}] ❌ [CRITICAL] No valid symbol file found in historical storage.")
        return []

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
        tag = self._get_tag()
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            return payload.get("symbols", [])
        except Exception as e:
            logger.error(f"[{tag}] [ERROR] Failed to load universe list from {path}: {e}")
            return []

    def _find_latest_snapshot(self) -> Optional[Path]:
        files = list(self.universe_dir.glob(f"*_{self.market}.json"))
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
        tag = self._get_tag()
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
