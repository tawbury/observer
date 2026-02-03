import asyncio
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Optional, Dict, Any

from observer.paths import snapshot_dir


class UniverseManager:
    """
    Universe manager responsible for:
    - Building a daily universe snapshot from previous trading day's close
    - Loading cached universe snapshots
    - Returning current day's universe list

    Notes:
    - Candidate symbol source is pluggable via `candidate_symbols` or by placing
      a file under `config/symbols/kr_all_symbols.(txt|csv)`.
    - Price filter uses previous trading day's close via ProviderEngine.fetch_daily_prices().
    - This implementation uses weekday-based previous trading day (Mon -> Fri). Holiday
      handling can be added later with an exchange calendar.
    """

    def __init__(
        self,
        provider_engine,
        universe_dir: Optional[str] = None,
        market: str = "kr_stocks",
        min_price: int = 4000,
        min_count: int = 100,
        candidate_symbols: Optional[Iterable[str]] = None,
    ) -> None:
        self.engine = provider_engine
        self.market = market
        self.min_price = int(min_price)
        self.min_count = int(min_count)
        # Default snapshot dir: data/universe (centralized in paths.py)
        self.universe_dir = universe_dir or str(snapshot_dir())
        Path(self.universe_dir).mkdir(parents=True, exist_ok=True)
        self._candidate_symbols = list(candidate_symbols) if candidate_symbols else None

    # ----------------------- Public APIs -----------------------
    def get_current_universe(self) -> List[str]:
        """Load today's universe list; falls back to last available snapshot, then file/candidates."""
        today = date.today()
        symbols = self._try_load_universe_list(today)
        if symbols is not None:
            return symbols
        # Fallback to most recent snapshot if today's not found
        latest = self._find_latest_snapshot()
        if latest:
            return self._load_universe_list_from_path(latest)
        # No snapshot: sync file-only candidates or built-in 20 symbols (no API)
        return self._load_candidates_from_file_sync()

    def load_universe(self, day: str | date | datetime) -> List[str]:
        """Load universe list for the given day (YYYY-MM-DD|date|datetime)."""
        dt = self._as_date(day)
        symbols = self._try_load_universe_list(dt)
        return symbols or []

    async def create_daily_snapshot(self, day: str | date | datetime) -> str:
        """
        Create daily universe snapshot JSON for `day` using previous trading day's close.
        Returns the written file path.
        """
        target_date = self._as_date(day)
        prev_trading = self._previous_trading_day(target_date)

        candidates = await self._load_candidates()
        if not candidates:
            raise ValueError("No candidate symbols available to build universe.")

        # Fetch previous close concurrently with bounded concurrency
        selected: List[str] = []
        sem = asyncio.Semaphore(10)  # Increased concurrency for faster processing
        processed_count = 0
        total_candidates = len(candidates)

        async def fetch_and_filter(sym: str) -> None:
            nonlocal processed_count
            async with sem:
                try:
                    # Check historical data for price filter (and suspension check)
                    # We use days=2 to get the most recent valid trading day
                    data = await self.engine.fetch_daily_prices(sym, days=2)
                    
                    # If data is empty or first item has 0 price, it might be suspended/delisted
                    close = self._extract_prev_close(data)
                    
                    if close is not None and close >= self.min_price:
                        # Optional: check current price only for potential strategy-specific filtering
                        # current_data = await self.engine.fetch_current_price(sym)
                        # ...
                        selected.append(sym)
                except Exception:
                    pass
                finally:
                    processed_count += 1
                    if processed_count % 100 == 0:
                        print(f"[PROGRESS] Universe build: {processed_count}/{total_candidates} processed...")

        await asyncio.gather(*(fetch_and_filter(s) for s in candidates))

        if len(selected) < self.min_count:
            raise ValueError(
                f"Universe size too small: {len(selected)} < {self.min_count}. Provide more candidates or lower threshold."
            )

        snapshot = {
            "date": target_date.isoformat(),
            "market": self.market,
            "filter_criteria": {
                "min_price": self.min_price,
                "prev_trading_day": prev_trading.isoformat(),
            },
            "symbols": sorted(selected),
            "count": len(selected),
        }

        path = self._snapshot_path(target_date)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        return path

    # ----------------------- Internals -----------------------
    def _snapshot_path(self, day: date) -> str:
        ymd = day.strftime("%Y%m%d")
        filename = f"{ymd}_{self.market}.json"
        return os.path.join(self.universe_dir, filename)

    def _try_load_universe_list(self, day: date) -> Optional[List[str]]:
        path = self._snapshot_path(day)
        if os.path.exists(path):
            return self._load_universe_list_from_path(path)
        return None

    def _load_universe_list_from_path(self, path: str) -> List[str]:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload.get("symbols", [])

    def _find_latest_snapshot(self) -> Optional[str]:
        if not os.path.isdir(self.universe_dir):
            return None
        files = [
            os.path.join(self.universe_dir, f)
            for f in os.listdir(self.universe_dir)
            if f.endswith("_" + self.market + ".json")
        ]
        if not files:
            return None
        files.sort(reverse=True)  # filename starts with YYYYMMDD
        return files[0]

    def _load_candidates_from_file_sync(self) -> List[str]:
        """
        Load candidate symbols from file only (sync, no API).
        Used when no today snapshot and no latest snapshot exist.
        Priority: config/symbols/kr_all_symbols.txt -> .csv -> built-in 20 symbols.
        """
        base_dir = os.environ.get("OBSERVER_CONFIG_DIR")
        if not base_dir:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config"))
        symbols_dir = os.path.join(base_dir, "symbols")
        txt_path = os.path.join(symbols_dir, "kr_all_symbols.txt")
        csv_path = os.path.join(symbols_dir, "kr_all_symbols.csv")
        result: List[str] = []

        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if s:
                        result.append(s)
            if result:
                return list(dict.fromkeys(result))

        if os.path.exists(csv_path):
            with open(csv_path, "r", encoding="utf-8") as f:
                header = f.readline()
                cols = [c.strip().lower() for c in header.split(",")]
                sym_idx = None
                for i, c in enumerate(cols):
                    if c in ("symbol", "code", "sym"):
                        sym_idx = i
                        break
                if sym_idx is None:
                    sym_idx = 0
                for line in f:
                    parts = [p.strip() for p in line.split(",")]
                    if parts and parts[0]:
                        result.append(parts[sym_idx])
            if result:
                return list(dict.fromkeys(result))

        # Built-in minimal fallback (20 symbols)
        return [
            "005930", "000660", "005380", "373220", "207940",
            "035420", "035720", "051910", "005490", "068270",
            "028260", "006400", "105560", "055550", "012330",
            "096770", "034730", "003550", "259960", "066570",
        ]

    def _as_date(self, day: str | date | datetime) -> date:
        if isinstance(day, datetime):
            return day.date()
        if isinstance(day, date):
            return day
        # Expect YYYY-MM-DD
        return datetime.fromisoformat(day).date()

    def _previous_trading_day(self, target: date) -> date:
        # Weekday-based previous trading day (Mon->Fri), holidays not handled yet
        wd = target.weekday()  # 0=Mon ... 6=Sun
        if wd == 0:
            return target - timedelta(days=3)
        if wd in (6,):
            # Sunday -> previous Friday
            return target - timedelta(days=2)
        return target - timedelta(days=1)

    async def _load_candidates(self) -> List[str]:
        """
        Load candidate symbols from multiple sources in priority order:
        1. API fetch from provider (most up-to-date)
        2. Cached file (kr_all_symbols.txt/csv) - updated from last API fetch
        3. Constructor-provided candidate_symbols
        4. Built-in fallback list (minimal)
        """
        # Priority 1: Try API fetch
        try:
            print("[INFO] Fetching stock list from KIS API...")
            api_symbols = await self.engine.fetch_stock_list(market="ALL")
            if api_symbols and len(api_symbols) > 100:
                print(f"[SUCCESS] Fetched {len(api_symbols)} symbols from API")
                # Cache to file for future use
                await self._cache_symbols_to_file(api_symbols)
                return list(dict.fromkeys(api_symbols))
            else:
                print(f"[WARNING] API returned insufficient symbols ({len(api_symbols)}), trying file...")
        except Exception as e:
            print(f"[WARNING] API fetch failed: {e}, falling back to file...")
        
        # Priority 2: Constructor-provided symbols
        if self._candidate_symbols is not None:
            print(f"[INFO] Using constructor-provided symbols ({len(self._candidate_symbols)})")
            return list(dict.fromkeys(self._candidate_symbols))
        
        # Priority 3: File-based candidates (config/symbols)
        symbols_dir = config_dir() / "symbols"
        txt_path = symbols_dir / "kr_all_symbols.txt"
        csv_path = symbols_dir / "kr_all_symbols.csv"
        result: List[str] = []

        if txt_path.exists():
            print(f"[INFO] Loading cached symbols from: {txt_path}")
            with open(txt_path, "r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if s:
                        result.append(s)
            print(f"[INFO] Loaded {len(result)} symbols from file")
            if result:
                return list(dict.fromkeys(result))
        
        if csv_path.exists():
            print(f"[INFO] Loading cached symbols from: {csv_path}")
            with open(csv_path, "r", encoding="utf-8") as f:
                header = f.readline()
                cols = [c.strip().lower() for c in header.split(",")]
                sym_idx = None
                for i, c in enumerate(cols):
                    if c in ("symbol", "code", "sym"):
                        sym_idx = i
                        break
                if sym_idx is None:
                    sym_idx = 0
                for line in f:
                    parts = [p.strip() for p in line.split(",")]
                    if parts and parts[0]:
                        result.append(parts[sym_idx])
            if result:
                return list(dict.fromkeys(result))
        
        # Priority 4: Built-in minimal fallback
        print("[WARNING] No API/file source available, using built-in fallback (20 symbols)")
        result = [
            "005930", "000660", "005380", "373220", "207940",
            "035420", "035720", "051910", "005490", "068270",
            "028260", "006400", "105560", "055550", "012330",
            "096770", "034730", "003550", "259960", "066570",
        ]
        result = list(dict.fromkeys(result))
        # 트리거 발동 시 캐시 파일 생성 (서버 등에서 API 미동작 시에도 kr_all_symbols.txt 생성)
        await self._cache_symbols_to_file(result)
        return result
    
    async def _cache_symbols_to_file(self, symbols: List[str]) -> None:
        """Cache fetched symbols to file for future fallback use."""
        try:
            symbols_dir = config_dir() / "symbols"
            symbols_dir.mkdir(parents=True, exist_ok=True)
            cache_path = symbols_dir / "kr_all_symbols.txt"
            with open(cache_path, "w", encoding="utf-8") as f:
                for sym in symbols:
                    f.write(f"{sym}\n")
            print(f"[INFO] Cached {len(symbols)} symbols to {cache_path}")
        except Exception as e:
            print(f"[WARNING] Failed to cache symbols to file: {e}")

    def _extract_prev_close(self, payload: Any) -> Optional[int]:
        """Extract close price from ProviderEngine.fetch_daily_prices() result.

        Provider returns a list of normalized daily contracts, each like:
        {
          "instruments": [{"symbol": ..., "price": {"close": int}, ...}], ...
        }
        Choose the first entry's close as most recent (API order dependent).
        """
        if not isinstance(payload, list) or not payload:
            return None
        first = payload[0]
        try:
            instruments = first.get("instruments")
            if not instruments:
                return None
            price = instruments[0].get("price", {})
            close = price.get("close")
            return int(close) if close is not None else None
        except Exception:
            return None
