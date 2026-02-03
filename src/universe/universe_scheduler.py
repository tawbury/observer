from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime, date, time, timedelta, timezone
from typing import Optional, Callable, List, Dict, Any
from zoneinfo import ZoneInfo

from provider import KISAuth, ProviderEngine
from universe.universe_manager import UniverseManager

log = logging.getLogger("UniverseScheduler")


@dataclass
class SchedulerConfig:
    tz_name: str = "Asia/Seoul"
    am_hour: int = 5
    am_minute: int = 0
    pm_hour: int = 16
    pm_minute: int = 5
    min_price: int = 4000
    min_count: int = 100
    market: str = "kr_stocks"
    anomaly_ratio: float = 0.30  # 30% deviation from previous count triggers alert

    # Optional legacy fields for backward compatibility with older runner logic
    hour: Optional[int] = None
    minute: Optional[int] = None

    def __post_init__(self):
        """Map legacy hour/minute to PM slot if provided directly (for testing/quick-runs)."""
        if self.hour is not None:
            self.pm_hour = self.hour
        if self.minute is not None:
            self.pm_minute = self.minute


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
        
        # Check Environment Variable at init
        self.data_dir = os.getenv("OBSERVER_DATA_DIR")
        if not self.data_dir:
            log.warning("[RECOVERY] OBSERVER_DATA_DIR not set. Using default path policies.")
        else:
            log.info("[INIT] OBSERVER_DATA_DIR detected: %s", self.data_dir)

    # ---------------------------------------------------------
    # Public
    # ---------------------------------------------------------
    async def run_forever(self) -> None:
        """Run the scheduler loop indefinitely."""
        # [INIT-CHECK] Immediate check on startup to prevent data gaps
        try:
            today = date.today()
            if not self._manager.load_universe(today):
                log.info("[INIT-CHECK] Today's snapshot missing. Starting immediate generation...")
                await self._run_once_internal()
            else:
                log.info("[INIT-CHECK] Today's snapshot exists. Waiting for next schedule.")
        except Exception as e:
            log.error("[INIT-CHECK] [ERROR] Startup generation check failed: %s", e)

        while True:
            next_run = self._next_run_dt()
            now = datetime.now(self._tz)
            wait_s = (next_run - now).total_seconds()
            
            tag = "AM" if next_run.hour < 12 else "PM"
            log.info("[%s] Next universe generation at %s (in %.0fs)", tag, next_run.isoformat(), wait_s)
            
            if wait_s > 0:
                await asyncio.sleep(wait_s)
            
            try:
                await self._run_once_internal()
            except Exception as e:
                # Catch-all to prevent the loop from dying
                log.error("[%s] [FATAL] Unexpected loop error: %s. Continuing to next schedule.", tag, e)
                await asyncio.sleep(60) # Prevent tight error loops

    async def run_once(self) -> Dict[str, Any]:
        """Run the universe generation once immediately (for smoke tests)."""
        return await self._run_once_internal()

    # ---------------------------------------------------------
    # Internals
    # ---------------------------------------------------------
    def _next_run_dt(self) -> datetime:
        """Find the closest next run time between AM and PM slots."""
        now = datetime.now(self._tz)
        
        # Candidate 1: Today AM
        am_today = datetime.combine(now.date(), time(self.cfg.am_hour, self.cfg.am_minute), tzinfo=self._tz)
        # Candidate 2: Today PM
        pm_today = datetime.combine(now.date(), time(self.cfg.pm_hour, self.cfg.pm_minute), tzinfo=self._tz)
        # Candidate 3: Tomorrow AM
        am_tomorrow = am_today + timedelta(days=1)
        
        if now < am_today:
            return am_today
        if now < pm_today:
            return pm_today
        return am_tomorrow

    async def _run_once_internal(self) -> Dict[str, Any]:
        tag = "AM" if datetime.now(self._tz).hour < 12 else "PM"
        today = date.today()
        # UniverseManager internals will use its own time-aware previous day logic
        
        meta: Dict[str, Any] = {
            "session": tag,
            "date": today.isoformat(),
            "market": self.cfg.market,
            "min_price": self.cfg.min_price,
            "min_count": self.cfg.min_count,
        }
        
        try:
            log.info("[%s] Starting scheduled universe snapshot for %s", tag, today.isoformat())
            path = await self._manager.create_daily_snapshot(today)
            
            current_symbols = self._manager.load_universe(today)
            # Find the MOST RECENT snapshot for comparison (might be yesterday PM or today AM)
            # UniverseManager._find_latest_snapshot implementation is robust
            latest_path = self._manager._find_latest_snapshot()
            prev_symbols = []
            if latest_path and str(latest_path) != str(path):
                prev_symbols = self._manager._load_universe_list_from_path(latest_path)

            meta.update({
                "ok": True,
                "snapshot_path": path,
                "count": len(current_symbols),
                "prev_count": len(prev_symbols) if prev_symbols else None,
            })
            
            log.info(
                "[%s] Universe summary | count=%d | snapshot=%s | prev_count=%s",
                tag,
                len(current_symbols),
                path,
                len(prev_symbols) if prev_symbols else 0,
            )
            
            # Anomaly detection (Log alert if size deviation is too high)
            self._check_anomaly(len(current_symbols), len(prev_symbols) if prev_symbols else None)
            return meta
            
        except Exception as e:
            log.error("[%s] [ERROR] Universe generation failed: %s", tag, e)
            # The UniverseManager.get_current_universe() already provides a fallback.
            # Here we just ensure we report the failure to the alert system.
            self._emit_alert(f"universe_failed_{tag}", {"error": str(e), "tag": tag})
            meta.update({"ok": False, "error": str(e)})
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
