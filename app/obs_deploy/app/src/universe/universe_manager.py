import asyncio
import json
import os
from datetime import date, datetime, timedelta
from typing import Iterable, List, Optional, Dict, Any


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
        # Default snapshot dir inside obs_deploy config
        # From app/obs_deploy/app/src/universe -> app/obs_deploy/config
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "config"))
        self.universe_dir = universe_dir or os.path.join(base_dir, "universe")
        os.makedirs(self.universe_dir, exist_ok=True)
        self._candidate_symbols = list(candidate_symbols) if candidate_symbols else None

    # ----------------------- Public APIs -----------------------
    def get_current_universe(self) -> List[str]:
        """Load today's universe list; falls back to last available snapshot."""
        today = date.today()
        symbols = self._try_load_universe_list(today)
        if symbols is not None:
            return symbols
        # Fallback to most recent snapshot if today's not found
        latest = self._find_latest_snapshot()
        if latest:
            return self._load_universe_list_from_path(latest)
        return []

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
        sem = asyncio.Semaphore(5)

        async def fetch_and_filter(sym: str) -> None:
            async with sem:
                try:
                    data = await self.engine.fetch_daily_prices(sym, days=2)
                    # Expect most recent entries first; pick first item's close
                    close = self._extract_prev_close(data)
                    if close is not None and close >= self.min_price:
                        selected.append(sym)
                except Exception:
                    # Ignore per-symbol failures; continue
                    pass

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
        if self._candidate_symbols is not None:
            return list(dict.fromkeys(self._candidate_symbols))

        # Try file-based candidates: config/symbols/kr_all_symbols.(txt|csv)
        # From app/obs_deploy/app/src/universe -> app/obs_deploy/config
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "config"))
        symbols_dir = os.path.join(base_dir, "symbols")
        txt_path = os.path.join(symbols_dir, "kr_all_symbols.txt")
        csv_path = os.path.join(symbols_dir, "kr_all_symbols.csv")
        result: List[str] = []

        if os.path.exists(txt_path):
            print(f"[DEBUG] Loading candidates from: {txt_path}")
            with open(txt_path, "r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if s:
                        result.append(s)
            print(f"[DEBUG] Loaded {len(result)} candidates from file")
        elif os.path.exists(csv_path):
            # Minimal CSV reader without dependency
            with open(csv_path, "r", encoding="utf-8") as f:
                header = f.readline()
                cols = [c.strip().lower() for c in header.split(",")]
                sym_idx = None
                for i, c in enumerate(cols):
                    if c in ("symbol", "code", "sym"):
                        sym_idx = i
                        break
                if sym_idx is None:
                    # Fallback assume first column is symbol
                    sym_idx = 0
                for line in f:
                    parts = [p.strip() for p in line.split(",")]
                    if parts and parts[0]:
                        result.append(parts[sym_idx])
        else:
            # Built-in small fallback; may not satisfy min_count
            result = [
                "005930", "000660", "005380", "373220", "207940",
                "035420", "035720", "051910", "005490", "068270",
                "028260", "006400", "105560", "055550", "012330",
                "096770", "034730", "003550", "259960", "066570",
            ]

        # Deduplicate while preserving order
        return list(dict.fromkeys(result))

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
