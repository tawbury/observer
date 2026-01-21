from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime, date, time, timedelta, timezone
from typing import Optional, Callable, List, Dict, Any

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore

from provider import KISAuth, ProviderEngine
from universe.universe_manager import UniverseManager

log = logging.getLogger("UniverseScheduler")


@dataclass
class SchedulerConfig:
    tz_name: str = "Asia/Seoul"
    hour: int = 5
    minute: int = 0
    min_price: int = 4000
    min_count: int = 100
    market: str = "kr_stocks"
    anomaly_ratio: float = 0.30  # 30% deviation from previous count triggers alert


class UniverseScheduler:
    def __init__(
        self,
        engine: ProviderEngine,
        config: Optional[SchedulerConfig] = None,
        on_alert: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> None:
        self.engine = engine
        self.cfg = config or SchedulerConfig()
        self.on_alert = on_alert
        self._tz = ZoneInfo(self.cfg.tz_name) if ZoneInfo else timezone(timedelta(hours=9))
        self._manager = UniverseManager(
            provider_engine=self.engine,
            market=self.cfg.market,
            min_price=self.cfg.min_price,
            min_count=self.cfg.min_count,
        )

    # ---------------------------------------------------------
    # Public
    # ---------------------------------------------------------
    async def run_forever(self) -> None:
        """Run the scheduler loop indefinitely."""
        while True:
            next_run = self._next_run_dt()
            now = datetime.now(self._tz)
            wait_s = (next_run - now).total_seconds()
            log.info("Next universe generation at %s (in %.0fs)", next_run.isoformat(), wait_s)
            if wait_s > 0:
                await asyncio.sleep(wait_s)
            await self._run_once_internal()

    async def run_once(self) -> Dict[str, Any]:
        """Run the universe generation once immediately (for smoke tests)."""
        return await self._run_once_internal()

    # ---------------------------------------------------------
    # Internals
    # ---------------------------------------------------------
    def _next_run_dt(self) -> datetime:
        now = datetime.now(self._tz)
        today_target = datetime.combine(now.date(), time(self.cfg.hour, self.cfg.minute), tzinfo=self._tz)
        if now < today_target:
            return today_target
        return today_target + timedelta(days=1)

    async def _run_once_internal(self) -> Dict[str, Any]:
        today = date.today()
        prev_day = self._previous_trading_day(today)
        meta: Dict[str, Any] = {
            "date": today.isoformat(),
            "market": self.cfg.market,
            "min_price": self.cfg.min_price,
            "min_count": self.cfg.min_count,
        }
        try:
            log.info("Creating universe snapshot for %s", today.isoformat())
            path = await self._manager.create_daily_snapshot(today)
            current_symbols = self._manager.load_universe(today)
            prev_symbols = self._manager.load_universe(prev_day)
            meta.update({
                "ok": True,
                "snapshot_path": path,
                "count": len(current_symbols),
                "prev_count": len(prev_symbols) if prev_symbols else None,
            })
            # Anomaly detection
            self._check_anomaly(len(current_symbols), len(prev_symbols) if prev_symbols else None)
            log.info("Universe snapshot created: %s (%d symbols)", path, len(current_symbols))
            return meta
        except Exception as e:
            log.error("Universe generation failed (%s). Falling back to previous snapshot.", e)
            # Fallback: reuse previous snapshot symbols for today
            try:
                prev_symbols = self._manager.load_universe(prev_day)
                if not prev_symbols:
                    raise RuntimeError("No previous universe available for fallback")
                # Write today's snapshot using previous symbols
                path = self._write_fallback_snapshot(today, prev_day, prev_symbols)
                meta.update({
                    "ok": True,
                    "snapshot_path": path,
                    "count": len(prev_symbols),
                    "fallback_from": prev_day.isoformat(),
                    "note": "fallback to previous snapshot",
                })
                # Alert on fallback
                self._emit_alert(
                    "universe_fallback",
                    {
                        "error": str(e),
                        "fallback_from": prev_day.isoformat(),
                        "target_date": today.isoformat(),
                        "count": len(prev_symbols),
                    },
                )
                log.warning("Fallback snapshot written: %s (from %s)", path, prev_day.isoformat())
                return meta
            except Exception as ee:
                meta.update({"ok": False, "error": f"fallback failed: {ee}"})
                self._emit_alert("universe_fatal", {"error": str(ee)})
                return meta

    def _check_anomaly(self, current: int, previous: Optional[int]) -> None:
        if previous is None:
            return
        if current < self.cfg.min_count:
            self._emit_alert(
                "universe_count_below_min",
                {"current": current, "min_count": self.cfg.min_count},
            )
            return
        # Deviation check
        if previous > 0:
            change = abs(current - previous) / previous
            if change >= self.cfg.anomaly_ratio:
                self._emit_alert(
                    "universe_count_anomaly",
                    {"current": current, "previous": previous, "ratio": round(change, 3)},
                )

    def _emit_alert(self, kind: str, payload: Dict[str, Any]) -> None:
        if self.on_alert:
            try:
                self.on_alert(kind, payload)
                return
            except Exception:
                pass
        # Default: log warning
        log.warning("ALERT[%s] %s", kind, payload)

    def _write_fallback_snapshot(self, target_day: date, prev_day: date, symbols: List[str]) -> str:
        # Build snapshot file path same as UniverseManager
        # Uses UniverseManager internals (directory and market)
        ymd = target_day.strftime("%Y%m%d")
        filename = f"{ymd}_{self._manager.market}.json"
        path = os.path.join(self._manager.universe_dir, filename)
        payload = {
            "date": target_day.isoformat(),
            "market": self._manager.market,
            "filter_criteria": {
                "min_price": self._manager.min_price,
                "prev_trading_day": prev_day.isoformat(),
                "fallback": True,
            },
            "symbols": sorted(symbols),
            "count": len(symbols),
        }
        os.makedirs(self._manager.universe_dir, exist_ok=True)
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return path

    def _previous_trading_day(self, d: date) -> date:
        wd = d.weekday()
        if wd == 0:
            return d - timedelta(days=3)
        if wd == 6:
            return d - timedelta(days=2)
        return d - timedelta(days=1)


# ---------------- CLI helper ----------------
async def _run_cli(run_once: bool = False) -> None:
    # Load .env if available (optional)
    try:
        from pathlib import Path
        env_path = Path.cwd() / ".env"
        if env_path.exists():
            try:
                from dotenv import load_dotenv  # type: ignore
                load_dotenv(env_path)
            except Exception:
                pass
    except Exception:
        pass

    # Prefer REAL_* env vars if set (like tests)
    app_key = os.getenv("KIS_APP_KEY") or os.getenv("REAL_APP_KEY")
    app_secret = os.getenv("KIS_APP_SECRET") or os.getenv("REAL_APP_SECRET")
    assert app_key and app_secret, "KIS_APP_KEY/SECRET missing"

    auth = KISAuth(app_key, app_secret, is_virtual=False)
    engine = ProviderEngine(auth, is_virtual=False)

    scheduler = UniverseScheduler(engine)
    try:
        if run_once:
            await scheduler.run_once()
        else:
            await scheduler.run_forever()
    finally:
        await engine.close()


def main():
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    parser = argparse.ArgumentParser(description="Universe Scheduler")
    parser.add_argument("--run-once", action="store_true", help="Run once immediately and exit")
    args = parser.parse_args()
    asyncio.run(_run_cli(run_once=args.run_once))


if __name__ == "__main__":
    main()
