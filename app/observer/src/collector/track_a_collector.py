from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Optional, Callable

from pathlib import Path
from zoneinfo import ZoneInfo

from shared.time_helpers import TimeAwareMixin
from shared.trading_hours import in_trading_hours

from provider import ProviderEngine, KISAuth
from universe.universe_manager import UniverseManager
from paths import observer_asset_dir

log = logging.getLogger("TrackACollector")


@dataclass
class TrackAConfig:
    tz_name: str = "Asia/Seoul"
    interval_minutes: int = 10
    market: str = "kr_stocks"
    session_id: str = "track_a_session"
    mode: str = "PROD"
    semaphore_limit: int = 20  # respect 20 req/sec
    daily_log_subdir: str = "swing"  # under config/observer/{subdir}
    trading_start: time = time(9, 0)
    trading_end: time = time(15, 30)


class TrackACollector(TimeAwareMixin):
    def __init__(
        self,
        engine: ProviderEngine,
        config: Optional[TrackAConfig] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.engine = engine
        self.cfg = config or TrackAConfig()
        self._tz_name = self.cfg.tz_name
        self._init_timezone()
        self._manager = UniverseManager(
            provider_engine=self.engine,
            market=self.cfg.market,
            min_price=4000,  # aligned with Task 6.1
            min_count=100,
        )
        self._on_error = on_error

    # -----------------------------------------------------
    # Scheduling
    # -----------------------------------------------------
    async def start(self) -> None:
        """Run every interval during trading hours."""
        log.info("TrackACollector started (interval=%dm)", self.cfg.interval_minutes)
        last_in_trading: Optional[bool] = None
        while True:
            now = self._now()
            in_trading = in_trading_hours(now, self.cfg.trading_start, self.cfg.trading_end)
            if in_trading:
                if last_in_trading is False:
                    log.info(
                        "Trading window open (%s-%s KST) - resuming collection",
                        self.cfg.trading_start,
                        self.cfg.trading_end,
                    )
                last_in_trading = True
                try:
                    await self.collect_once()
                except Exception as e:
                    log.exception("Track A collect_once failed: %s", e)
                    if self._on_error:
                        try:
                            self._on_error(str(e))
                        except Exception:
                            pass
                await asyncio.sleep(self.cfg.interval_minutes * 60)
            else:
                if last_in_trading is not False:
                    log.info(
                        "Outside trading hours (%s-%s KST) - sleeping 60s",
                        self.cfg.trading_start,
                        self.cfg.trading_end,
                    )
                last_in_trading = False
                # Sleep until next minute to re-check window quickly
                await asyncio.sleep(60)

    # -----------------------------------------------------
    # One-shot collection
    # -----------------------------------------------------
    async def collect_once(self) -> Dict[str, Any]:
        today = date.today().isoformat()
        # Load universe (fallback to last available if today's missing)
        symbols: List[str] = self._manager.get_current_universe()
        if not symbols:
            raise RuntimeError("Universe symbols unavailable for Track A")

        # Prepare JSONL path under config/observer/swing/YYYYMMDD.jsonl
        ymd = datetime.now().strftime("%Y%m%d")
        log_dir = observer_asset_dir() / self.cfg.daily_log_subdir
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{ymd}.jsonl"

        sem = asyncio.Semaphore(self.cfg.semaphore_limit)
        results: List[Dict[str, Any]] = []

        async def fetch(symbol: str) -> None:
            async with sem:
                try:
                    data = await self.engine.fetch_current_price(symbol)
                    results.append({"symbol": symbol, "data": data})
                except Exception as e:
                    # tolerate per-symbol failures
                    log.debug("Symbol %s fetch failed: %s", symbol, e)

        await asyncio.gather(*(fetch(s) for s in symbols))

        # Write JSONL records
        published = 0
        with open(log_path, "a", encoding="utf-8") as f:
            for item in results:
                sym = item["symbol"]
                payload = item["data"]
                inst = (payload.get("instruments") or [{}])[0]
                price = inst.get("price") or {}
                record = {
                    "ts": self._now().isoformat(),
                    "session": self.cfg.session_id,
                    "dataset": "track_a_swing",
                    "market": self.cfg.market,
                    "symbol": sym,
                    "price": {
                        "open": price.get("open"),
                        "high": price.get("high"),
                        "low": price.get("low"),
                        "close": price.get("close"),
                    },
                    "volume": inst.get("volume"),
                    "bid_price": inst.get("bid_price"),
                    "ask_price": inst.get("ask_price"),
                    "source": "kis",
                }
                import json
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                published += 1

        return {
            "ok": True,
            "symbols": len(symbols),
            "fetched": len(results),
            "published": published,
            "log_file": str(log_path),
        }


# ---------------- CLI helper ----------------
async def _run_cli(run_once: bool = False) -> None:
    import os
    from pathlib import Path

    # Load .env if available
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        try:
            from dotenv import load_dotenv  # type: ignore
            load_dotenv(env_path)
        except Exception:
            pass

    app_key = os.getenv("KIS_APP_KEY") or os.getenv("REAL_APP_KEY")
    app_secret = os.getenv("KIS_APP_SECRET") or os.getenv("REAL_APP_SECRET")
    assert app_key and app_secret, "KIS_APP_KEY/SECRET missing"

    auth = KISAuth(app_key, app_secret, is_virtual=False)
    engine = ProviderEngine(auth, is_virtual=False)

    collector = TrackACollector(engine)
    try:
        if run_once:
            result = await collector.collect_once()
            print(result)
        else:
            await collector.start()
    finally:
        await engine.close()


def main():
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    parser = argparse.ArgumentParser(description="Track A Collector (REST/Swing)")
    parser.add_argument("--run-once", action="store_true", help="Run single collection cycle and exit")
    args = parser.parse_args()
    asyncio.run(_run_cli(run_once=args.run_once))


if __name__ == "__main__":
    main()
