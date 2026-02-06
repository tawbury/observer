from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Optional, Callable

import os
from pathlib import Path
from zoneinfo import ZoneInfo

from shared.time_helpers import TimeAwareMixin
from shared.trading_hours import in_trading_hours

from provider import ProviderEngine, KISAuth
from universe.universe_manager import UniverseManager
from observer.paths import observer_asset_dir, observer_log_dir
from db.realtime_writer import RealtimeDBWriter

log = logging.getLogger("SwingCollector")


@dataclass
class SwingConfig:
    tz_name: str = "Asia/Seoul"
    interval_minutes: int = 5
    market: str = f"{os.getenv('MARKET_CODE', 'kr')}_stocks"
    session_id: str = "track_a_session"
    mode: str = "PROD"
    semaphore_limit: int = 20  # respect 20 req/sec
    daily_log_subdir: str = "swing"  # under config/{subdir}
    trading_start: time = time(9, 0)
    trading_end: time = time(15, 30)


class SwingCollector(TimeAwareMixin):
    def __init__(
        self,
        engine: ProviderEngine,
        config: Optional[SwingConfig] = None,
        universe_dir: Optional[str] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.engine = engine
        self.cfg = config or SwingConfig()
        self._tz_name = self.cfg.tz_name
        self._init_timezone()
        self._manager = UniverseManager(
            provider_engine=self.engine,
            data_dir=universe_dir,
            market=self.cfg.market,
            min_price=4000,  # aligned with Task 6.1
            min_count=100,
        )
        self._on_error = on_error
        
        # DB 실시간 저장
        self._db_writer = RealtimeDBWriter()

        self._setup_logger()

        log.info("SwingCollector initialized: market=%s, interval=%dm, semaphore=%d",
                 self.cfg.market, self.cfg.interval_minutes, self.cfg.semaphore_limit)

    def _setup_logger(self) -> None:
        """Setup specialized file logger for swing strategy"""
        try:
            # logs/swing/YYYYMMDD.log
            today_str = self._now().strftime("%Y%m%d")
            log_dir = observer_log_dir() / self.cfg.daily_log_subdir
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / f"{today_str}.log"
            
            handler = logging.FileHandler(log_file, encoding='utf-8')
            handler.setFormatter(logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
            ))
            
            # Add handler to the module-level logger
            log.addHandler(handler)
            log.info(f"Swing file logger initialized: {log_file}")
            
        except Exception as e:
            # Fallback to console/default logger if file setup fails
            log.error(f"Failed to setup swing file logger: {e}")

    async def start(self) -> None:
        """Run every interval during trading hours with initial bootstrapping."""
        log.info("SwingCollector started (interval=%dm)", self.cfg.interval_minutes)
        
        # 0. DB 연결 초기화 (Best effort)
        db_connected = await self._db_writer.connect()
        if db_connected:
            log.info("✅ DB 연결 성공 - 실시간 저장 활성화")
        else:
            log.warning("⚠️ DB 연결 실패 - JSONL 파일만 저장됩니다")
        
        # [Requirement] Bootstrapping Sequence with Max Retry
        MAX_BOOTSTRAP_RETRIES = 10
        bootstrap_attempt = 0
        while True:
            bootstrap_attempt += 1
            log.info("Starting Bootstrapping Sequence (attempt %d/%d)...", bootstrap_attempt, MAX_BOOTSTRAP_RETRIES)
            try:
                # 1단계 (Symbol): SymbolGenerator.execute() 호출하여 최소 2,500개 확보
                # _load_robust_candidates 내에서도 symbol_gen.execute()가 호출되지만
                # 부트스트랩 시점에서 명시적으로 한번 더 확인/수집합니다.
                should_collect, _ = self._manager.symbol_gen.should_collect()
                if should_collect:
                    log.info("[Bootstrap-1] Starting symbol collection...")
                    await self._manager.symbol_gen.execute()

                # 심볼 확보 확인
                latest_symbols = self._manager.symbol_gen.get_latest_symbol_file()
                if not latest_symbols:
                    raise RuntimeError("No symbol files available after collection attempt.")

                # 2단계 (Universe): T-0 유니버스 즉시 생성 강제
                log.info("[Bootstrap-2] Creating immediate daily universe snapshot...")
                # create_daily_snapshot 내부에서 _load_robust_candidates를 통해 심볼 로드
                await self._manager.create_daily_snapshot(date.today())

                # 3단계 (Loop Ready): 유효한 유니버스 소스 확보 확인
                current_universe = self._manager.get_current_universe()
                if not current_universe:
                    log.warning("[Bootstrap-3] Universe still empty. Forcefully creating daily snapshot...")
                    await self._manager.create_daily_snapshot(date.today())
                    current_universe = self._manager.get_current_universe()

                if not current_universe:
                    raise RuntimeError("Failed to verify valid universe after snapshot creation.")

                log.info("[Bootstrap-3] Bootstrapping complete after %d attempt(s) (Symbols: %d). Entering main collection loop.",
                         bootstrap_attempt, len(current_universe))
                break  # 부트스트랩 성공 시 루프 탈출

            except Exception as e:
                if bootstrap_attempt >= MAX_BOOTSTRAP_RETRIES:
                    log.critical("Bootstrap failed after %d attempts. Last error: %s (type=%s)",
                                 bootstrap_attempt, e, type(e).__name__, exc_info=True)
                    raise RuntimeError(f"Bootstrap failed after {MAX_BOOTSTRAP_RETRIES} attempts") from e

                wait_time = min(60 * bootstrap_attempt, 300)  # Cap at 5 minutes
                log.error("Bootstrapping failed (attempt %d/%d): %s. Retrying in %ds...",
                          bootstrap_attempt, MAX_BOOTSTRAP_RETRIES, e, wait_time, exc_info=True)
                await asyncio.sleep(wait_time)

        # Main Loop
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
                    universe_count = len(self._manager.get_current_universe()) if self._manager else 0
                    log.exception("Track A collect_once failed: %s (universe_size=%d, interval=%dm)",
                                  e, universe_count, self.cfg.interval_minutes)
                    if self._on_error:
                        try:
                            self._on_error(str(e))
                        except Exception as callback_err:
                            log.warning("Error callback itself failed: %s", callback_err)
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
        # Load universe (with T-1 failover logic inside UniverseManager)
        while True:
            symbols = self._manager.get_current_universe()
            if symbols:
                break
            
            log.warning("당일 및 전일 유니버스 파일을 찾을 수 없습니다. 60초 후 재시도합니다.")
            log.info("Waiting for universe file (T-0/T-1)...")
            await asyncio.sleep(60)

        # Prepare JSONL path under data/assets/swing/YYYYMMDD.jsonl
        ymd = datetime.now().strftime("%Y%m%d")
        log_dir = observer_asset_dir() / self.cfg.daily_log_subdir
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{ymd}.jsonl"

        sem = asyncio.Semaphore(self.cfg.semaphore_limit)

        async def fetch(symbol: str) -> Optional[Dict[str, Any]]:
            async with sem:
                try:
                    data = await self.engine.fetch_current_price(symbol)
                    return {"symbol": symbol, "data": data}
                except Exception as e:
                    # tolerate per-symbol failures
                    log.debug("Symbol %s fetch failed: %s", symbol, e)
                    return None

        # Gather results and filter out None (failures)
        raw_results = await asyncio.gather(*(fetch(s) for s in symbols))
        results: List[Dict[str, Any]] = [r for r in raw_results if r is not None]

        # 1) 아카이브: 먼저 JSONL에 모두 기록 (저장 순서 보장)
        import json
        published = 0
        records_for_db: List[Dict[str, Any]] = []
        
        try:
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
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    published += 1
                    records_for_db.append(record)
            
            if published > 0:
                log.info(f"[저장] {published} items written to JSONL ({log_path})")
                
        except (IOError, OSError) as e:
            log.error(f"[파일 시스템 오류] JSONL 쓰기 실패 (path: {log_path}): {e}")
            if self._on_error:
                self._on_error(f"File write failed: {log_path} | {e}")
            # JSONL 쓰기 실패하더라도 일단 계속 진행 (메모리상의 records_for_db는 DB 저장이 가능할 수 있음)

        # 2) DB 쓰기는 선택적(best-effort). 실패해도 예외 전파하지 않고 로그만 남김
        db_saved = 0
        if self._db_writer.is_connected and records_for_db:
            for record in records_for_db:
                try:
                    saved = await self._db_writer.save_swing_bar(record, self.cfg.session_id)
                    if saved:
                        db_saved += 1
                except Exception as e:
                    log.warning("DB 저장 실패 - JSONL 아카이브만 저장됨: %s", e)

        if published > 0 or db_saved > 0:
            log.info(f"[완료] Swing list updated: JSONL={published} | DB={db_saved}")


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
            log.debug("Loaded .env from %s", env_path)
        except ImportError:
            log.warning("dotenv package not installed, skipping .env load")
        except Exception as e:
            log.warning("Failed to load .env from %s: %s (type=%s)", env_path, e, type(e).__name__)
    else:
        log.debug(".env file not found at %s", env_path)

    app_key = os.getenv("KIS_APP_KEY") or os.getenv("REAL_APP_KEY")
    app_secret = os.getenv("KIS_APP_SECRET") or os.getenv("REAL_APP_SECRET")
    assert app_key and app_secret, "KIS_APP_KEY/SECRET missing"

    auth = KISAuth(app_key, app_secret, is_virtual=False)
    engine = ProviderEngine(auth, is_virtual=False)

    collector = SwingCollector(engine)
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
