"""
Track B Collector - Real-time WebSocket data collection for 41 slots

Key Responsibilities (Track A 독립형):
- Track A 데이터 없이도 자체 부트스트랩 심볼로 즉시 구독
- 41개 슬롯(WebSocket) 동적 관리 (SlotManager)
- 실시간 2Hz 체결 데이터 수집 및 스캘프 로그 저장
- config/scalp/YYYYMMDD.jsonl 로깅
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from zoneinfo import ZoneInfo

from shared.time_helpers import TimeAwareMixin
from shared.trading_hours import in_trading_hours

from provider import ProviderEngine
from trigger.trigger_engine import TriggerEngine
from slot.slot_manager import SlotManager, SlotCandidate
from slot.slot_manager import SlotManager, SlotCandidate
from paths import observer_asset_dir, observer_log_dir
from db.realtime_writer import RealtimeDBWriter

try:
    from paths import env_file_path
except ImportError:
    env_file_path = None  # type: ignore

log = logging.getLogger("TrackBCollector")


@dataclass
class TrackBConfig:
    tz_name: str = "Asia/Seoul"
    market: str = "kr_stocks"
    session_id: str = "track_b_session"
    mode: str = "PROD"
    max_slots: int = 41  # KIS WebSocket limit
    min_dwell_seconds: int = 120  # 2 minutes minimum slot occupancy
    daily_log_subdir: str = "scalp"  # under config/{subdir}
    trading_start: time = time(9, 30)  # Track B starts 30min after market open
    trading_end: time = time(15, 00)   # Track B ends 30min before market close (장마감 변동성 감지)
    trigger_check_interval_seconds: int = 30  # Trigger processing interval
    bootstrap_symbols: List[str] = field(
        default_factory=lambda: ["005930", "000660", "373220", "051910", "068270", "035720"]
    )
    bootstrap_priority: float = 0.95


class TrackBCollector(TimeAwareMixin):
    """
    Track B Collector - WebSocket-based real-time data collector.
    
    Features:
    - Track A 독립: 부트스트랩 심볼 기반 즉시 구독
    - Dynamic 41-slot WebSocket subscription management
    - 2Hz real-time price data collection
    - Scalp log partitioning by date
    """
    
    def __init__(
        self,
        engine: ProviderEngine,
        trigger_engine: Optional[TriggerEngine] = None,
        config: Optional[TrackBConfig] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.engine = engine
        self.trigger_engine = trigger_engine or TriggerEngine()
        self.cfg = config or TrackBConfig()
        self._tz_name = self.cfg.tz_name
        self._init_timezone()

        # Slot manager for 41 WebSocket subscriptions
        self.slot_manager = SlotManager(
            max_slots=self.cfg.max_slots,
            min_dwell_seconds=self.cfg.min_dwell_seconds
        )
        
        self._on_error = on_error
        self._running = False
        self._on_error = on_error
        self._running = False
        self._subscribed_symbols: Dict[str, int] = {}  # symbol -> slot_id
        
        # DB 실시간 저장
        self._db_writer = RealtimeDBWriter()
        
        self._setup_logger()

    def _setup_logger(self) -> None:
        """Setup specialized file logger for scalp strategy with hourly rotation"""
        try:
            from shared.hourly_handler import HourlyRotatingFileHandler
            
            log_dir = observer_log_dir() / self.cfg.daily_log_subdir
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # HourlyRotatingFileHandler로 정각 기준 시간별 로테이션
            # 파일명 형식: YYYYMMDD_HH.log
            handler = HourlyRotatingFileHandler(log_dir)
            handler.setFormatter(logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
            ))
            
            # Add handler to the module-level logger
            log.addHandler(handler)
            log.info(f"Scalp file logger initialized with hourly rotation: {log_dir}/YYYYMMDD_HH.log")
            
        except Exception as e:
            # Fallback to console/default logger if file setup fails
            log.error(f"Failed to setup scalp file logger: {e}")
        
    # -----------------------------------------------------
    # Scheduling
    # -----------------------------------------------------
    async def start(self) -> None:
        """
        Start Track B collector.
        
        Main loop:
        1. Start WebSocket provider (connect to KIS)
        2. Register price update callback
        3. 부트스트랩 심볼 기반 트리거 생성 (Track A 의존성 제거)
        4. Update slots based on trigger candidates
        5. Subscribe/unsubscribe WebSocket symbols
        6. Collect and log real-time data
        """
        log.info("TrackBCollector started (max_slots=%d)", self.cfg.max_slots)
        self._running = True

        # DB 연결 초기화
        db_connected = await self._db_writer.connect()
        if db_connected:
            log.info("✅ DB 연결 성공 - 실시간 저장 활성화")
        else:
            log.warning("⚠️ DB 연결 실패 - JSONL 파일만 저장됩니다")

        # Debug mode: bypass trading hours check for testing
        debug_mode = os.environ.get("TRACK_B_DEBUG", "").lower() in ("1", "true", "yes")
        if debug_mode:
            log.info("⚠️ 디버그 모드 활성화 - 장중 체크 우회")

        # CRITICAL: Register callback BEFORE starting WebSocket to avoid message loss
        log.info("콜백 등록 중...")
        self._register_websocket_callback()
        log.info(f"✅ 콜백 등록 완료. on_price_update: {self.engine.on_price_update}")

        # Now start WebSocket provider (callback is already registered)
        log.info("WebSocket 연결 시작...")
        await self._start_websocket()
        log.info("✅ WebSocket 연결 완료")

        try:
            while self._running:
                now = self._now()

                # 디버깅 로그 추가
                log.info(f"Track B 현재 시간: {now} (timezone: {now.tzinfo})")
                log.info(f"장중 시간: {self.cfg.trading_start} - {self.cfg.trading_end}")

                # 장 마감 시점이 지나면 즉시 수집을 종료하여 불필요한 로그 생성을 막는다
                if not debug_mode and now.time() > self.cfg.trading_end:
                    log.info("장 마감 시간을 초과했습니다. TrackBCollector를 종료합니다.")
                    self._running = False
                    break

                if not debug_mode and not in_trading_hours(now, self.cfg.trading_start, self.cfg.trading_end):
                    log.info("장중 시간 외 - 대기 중...")
                    await asyncio.sleep(60)
                    continue
                
                log.info("Inside trading hours, generating standalone triggers...")
                await self._check_triggers()
                
                # Wait before next check
                await asyncio.sleep(self.cfg.trigger_check_interval_seconds)
                
        except Exception as e:
            log.error(f"TrackBCollector error: {e}", exc_info=True)
            if self._on_error:
                self._on_error(str(e))
        finally:
            await self._stop_websocket()
    
    def stop(self) -> None:
        """Stop the collector"""
        log.info("TrackBCollector stopping...")
        self._running = False
    
    # -----------------------------------------------------
    # Trigger Detection & Slot Management
    # -----------------------------------------------------
    async def _check_triggers(self) -> None:
        """
        Track A 독립형 트리거 생성 및 슬롯 반영.

        Process:
        1. 부트스트랩 심볼 리스트로 SlotCandidate 생성
        2. SlotManager에 할당/교체/오버플로우 기록
        3. WebSocket 구독/해지 관리
        """
        try:
            candidates = self._generate_bootstrap_candidates()

            if not candidates:
                log.debug("No bootstrap candidates available")
                return

            log.info(f"🎯 Generated {len(candidates)} bootstrap candidates (Track A independent mode)")

            for candidate in candidates:
                result = self.slot_manager.assign_slot(candidate)

                if result.success:
                    log.info(
                        f"✅ Slot {result.slot_id}: {candidate.symbol} "
                        f"(priority={candidate.priority_score:.2f}, "
                        f"trigger={candidate.trigger_type})"
                    )

                    await self._subscribe_symbol(candidate.symbol, result.slot_id)

                    if result.replaced_symbol:
                        await self._unsubscribe_symbol(result.replaced_symbol)
                        log.info(f"🔄 Replaced {result.replaced_symbol} with {candidate.symbol}")

                elif result.overflow:
                    log.warning(f"⚠️ Overflow: {candidate.symbol} (priority={candidate.priority_score:.2f})")

        except Exception as e:
            log.error(f"Error checking triggers: {e}")

    def _generate_bootstrap_candidates(self) -> List[SlotCandidate]:
        """부트스트랩 심볼 기반 SlotCandidate 생성 (Track A 의존성 제거)."""
        now = self._now()
        candidates: List[SlotCandidate] = []

        base_priority = self.cfg.bootstrap_priority
        for idx, symbol in enumerate(self.cfg.bootstrap_symbols):
            priority = max(base_priority - (0.01 * idx), 0.0)
            candidates.append(
                SlotCandidate(
                    symbol=symbol,
                    trigger_type="bootstrap",
                    priority_score=priority,
                    detected_at=now
                )
            )

        return candidates
    
    # -----------------------------------------------------
    # WebSocket Management
    # -----------------------------------------------------
    async def _start_websocket(self) -> None:
        """Start WebSocket provider"""
        try:
            log.info("Starting WebSocket provider...")
            success = await self.engine.start_stream()
            if success:
                log.info("WebSocket provider started")
            else:
                log.error("WebSocket provider failed to start")
        except Exception as e:
            log.error(f"Failed to start WebSocket: {e}", exc_info=True)
            raise
    
    async def _stop_websocket(self) -> None:
        """Stop WebSocket provider"""
        try:
            log.info("Stopping WebSocket provider...")
            await self.engine.stop_stream()
            log.info("WebSocket provider stopped")
        except Exception as e:
            log.error(f"Failed to stop WebSocket: {e}", exc_info=True)
    
    def _register_websocket_callback(self) -> None:
        """Register callback for WebSocket price updates"""
        callback_count = [0]  # Mutable counter to track callback invocations
        
        def on_price_update(data: Dict[str, Any]) -> None:
            """Handle real-time price updates from WebSocket"""
            try:
                callback_count[0] += 1
                symbol = data.get('symbol', 'UNKNOWN')
                
                # Data validation: ensure required fields exist
                if not data or 'symbol' not in data:
                    log.warning("Invalid price update data (missing symbol): %s", repr(data)[:200])
                    return
                
                # Log every 100th callback to avoid spam (diagnostic)
                if callback_count[0] % 100 == 1:
                    log.info(f"📊 Price update callback #{callback_count[0]}: {symbol}")
                
                self._log_scalp_data(data)
            except Exception as e:
                log.error(f"Error handling price update: {e}", exc_info=True)
        
        # Set callback on provider engine
        self.engine.on_price_update = on_price_update
        log.info("✅ Price update callback registered - ready to receive WebSocket data")
    
    async def _subscribe_symbol(self, symbol: str, slot_id: int) -> None:
        """Subscribe to a symbol via WebSocket"""
        try:
            if symbol in self._subscribed_symbols:
                log.debug(f"Symbol {symbol} already subscribed")
                return
            
            success = await self.engine.subscribe(symbol)
            if success:
                self._subscribed_symbols[symbol] = slot_id
                log.info(f"📡 Subscribed: {symbol} (slot {slot_id})")
            else:
                log.warning(f"Failed to subscribe {symbol}: returned False")
        
        except Exception as e:
            log.error(f"Failed to subscribe {symbol}: {e}", exc_info=True)
    
    async def _unsubscribe_symbol(self, symbol: str) -> None:
        """Unsubscribe from a symbol via WebSocket"""
        try:
            if symbol not in self._subscribed_symbols:
                log.debug(f"Symbol {symbol} not subscribed")
                return
            
            success = await self.engine.unsubscribe(symbol)
            if success:
                del self._subscribed_symbols[symbol]
                log.info(f"📴 Unsubscribed: {symbol}")
            else:
                log.warning(f"Failed to unsubscribe {symbol}: returned False")
        
        except Exception as e:
            log.error(f"Failed to unsubscribe {symbol}: {e}", exc_info=True)
    
    # -----------------------------------------------------
    # Data Logging
    # -----------------------------------------------------
    def _log_scalp_data(self, data: Dict[str, Any]) -> None:
        """
        Log real-time scalp data to JSONL file and DB.
        
        File: config/scalp/YYYYMMDD_HH.jsonl (시간별 로테이션)
        DB: scalp_ticks 테이블
        
        Enhanced record format includes execution time, bid/ask, and volume details
        for scalp strategy analysis.
        
        Handles both H0STCNT0 format (volume=dict, bid_ask=dict) and JSON body format
        (volume=int, bid_price/ask_price at top level).
        """
        log_file: Optional[Path] = None
        try:
            now = self._now()
            hour_str = now.strftime("%Y%m%d_%H")
            
            # Scalp log path: config/scalp/YYYYMMDD_HH.jsonl (시간별 로테이션)
            base_dir = observer_asset_dir()
            log_dir = base_dir / self.cfg.daily_log_subdir
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / f"{hour_str}.jsonl"
            
            # Format compatibility: volume may be dict (H0STCNT0) or int (JSON body)
            vol = data.get("volume")
            if isinstance(vol, dict):
                vol_accumulated = vol.get("accumulated", 0)
                vol_trade_value = vol.get("trade_value")
            else:
                vol_accumulated = int(vol or 0) if vol is not None else 0
                vol_trade_value = None
            
            # Format compatibility: bid_ask may be absent (JSON body has top-level bid_price/ask_price)
            bid_ask = data.get("bid_ask") or {}
            if not bid_ask and ("bid_price" in data or "ask_price" in data):
                bid_ask = {"bid_price": data.get("bid_price"), "ask_price": data.get("ask_price")}
            
            # Safe price extraction (price may be None)
            price_data = data.get("price") or {}
            if not isinstance(price_data, dict):
                price_data = {}
            
            # Prepare enhanced record
            record = {
                "timestamp": now.isoformat(),
                "symbol": data.get("symbol", ""),
                "execution_time": data.get("execution_time"),  # HHMMSS from WebSocket
                "price": {
                    "current": price_data.get("close", 0),
                    "open": price_data.get("open"),
                    "high": price_data.get("high"),
                    "low": price_data.get("low"),
                    "change_rate": price_data.get("change_rate"),
                },
                "volume": {
                    "accumulated": vol_accumulated,
                    "trade_value": vol_trade_value,
                },
                "bid_ask": bid_ask,
                "source": "websocket",
                "session_id": self.cfg.session_id
            }
            
            # 1) 아카이브: 먼저 JSONL에 기록
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()  # Force flush to disk

            # 2) DB 쓰기는 선택적(best-effort). 실패 시 예외 전파하지 않고 done_callback에서 로그만
            if self._db_writer.is_connected:
                task = asyncio.create_task(
                    self._db_writer.save_scalp_tick(record, self.cfg.session_id)
                )
                def _on_db_done(t):
                    try:
                        t.result()
                    except Exception as e:
                        log.warning("DB 저장 실패 - JSONL 아카이브만 저장됨: %s", e)
                task.add_done_callback(_on_db_done)

            # Log every save for visibility (Korean output)
            symbol = data.get("symbol", "UNKNOWN")
            price = record["price"].get("current", 0)
            log.info(f"[저장] {symbol} @ {price:,}원 → {log_file}")
        
        except PermissionError as e:
            log.error("Permission denied writing scalp data: %s - %s", log_file or "N/A", e)
        except OSError as e:
            log.error("OS error writing scalp data: %s - %s", log_file or "N/A", e)
        except Exception as e:
            log.error(
                "Error logging scalp data: %s (type=%s) - data sample: %s",
                e, type(e).__name__, repr(data)[:300],
                exc_info=True
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collector statistics"""
        slot_stats = self.slot_manager.get_stats()
        return {
            "subscribed_symbols": len(self._subscribed_symbols),
            "slot_stats": slot_stats,
            "running": self._running
        }


# ---- CLI for Testing ----

async def main():
    """CLI for testing TrackBCollector"""
    import argparse
    from provider import KISAuth
    
    parser = argparse.ArgumentParser(description="Track B Collector Test CLI")
    parser.add_argument("--mode", choices=["PROD", "VIRTUAL"], default="VIRTUAL", help="KIS mode")
    parser.add_argument("--run-for", type=int, default=300, help="Run for N seconds (default: 300)")
    parser.add_argument("--bootstrap", default="005930,000660,373220", help="Comma-separated symbols for bootstrap")
    args = parser.parse_args()
    
    # Load .env if exists (Docker-compatible)
    if env_file_path is not None:
        env_file = env_file_path()
    else:
        env_file = Path(__file__).resolve().parents[3] / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
    
    # Setup
    is_virtual = args.mode.upper() == "VIRTUAL"
    auth = KISAuth(is_virtual=is_virtual)
    engine = ProviderEngine(auth=auth, is_virtual=is_virtual)
    trigger_engine = TriggerEngine()
    
    bootstrap_symbols = [s.strip().zfill(6) for s in args.bootstrap.split(',') if s.strip()]

    cfg = TrackBConfig(bootstrap_symbols=bootstrap_symbols)

    collector = TrackBCollector(
        engine=engine,
        trigger_engine=trigger_engine,
        config=cfg
    )
    
    print(f"🚀 Starting TrackBCollector (mode={args.mode}, duration={args.run_for}s)")
    print()
    
    # Run collector for specified duration
    try:
        collector_task = asyncio.create_task(collector.start())
        
        # Wait for specified duration
        await asyncio.sleep(args.run_for)
        
        # Stop collector
        collector.stop()
        await collector_task
    
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        collector.stop()
    
    finally:
        stats = collector.get_stats()
        print()
        print(f"📊 Final Stats: {stats}")
        await engine.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    asyncio.run(main())
