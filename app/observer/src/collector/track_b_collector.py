"""
Track B Collector - Real-time WebSocket data collection for 41 slots

Key Responsibilities:
- Monitor Track A data for trigger events (via TriggerEngine)
- Manage 41 WebSocket subscription slots (via SlotManager)
- Subscribe/unsubscribe symbols dynamically based on triggers
- Collect real-time 2Hz data from WebSocket
- Log scalp data to config/observer/scalp/YYYYMMDD.jsonl
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

from shared.timezone import ZoneInfo
from shared.time_helpers import TimeAwareMixin
from shared.trading_hours import in_trading_hours

from provider import ProviderEngine
from trigger.trigger_engine import TriggerEngine, PriceSnapshot, parse_track_a_jsonl
from slot.slot_manager import SlotManager, SlotCandidate
from paths import observer_asset_dir

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
    daily_log_subdir: str = "scalp"  # under config/observer/{subdir}
    trading_start: time = time(9, 30)  # Track B starts 30min after market open
    trading_end: time = time(15, 0)   # Track B ends before close
    track_a_check_interval_seconds: int = 60  # Check Track A for triggers every 60s


class TrackBCollector(TimeAwareMixin):
    """
    Track B Collector - WebSocket-based real-time data collector.
    
    Features:
    - Trigger-based symbol selection from Track A data
    - Dynamic 41-slot WebSocket subscription management
    - 2Hz real-time price data collection
    - Scalp log partitioning by date
    """
    
    def __init__(
        self,
        engine: ProviderEngine,
        trigger_engine: TriggerEngine,
        config: Optional[TrackBConfig] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.engine = engine
        self.trigger_engine = trigger_engine
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
        self._subscribed_symbols: Dict[str, int] = {}  # symbol -> slot_id
        
    # -----------------------------------------------------
    # Scheduling
    # -----------------------------------------------------
    async def start(self) -> None:
        """
        Start Track B collector.
        
        Main loop:
        1. Start WebSocket provider (connect to KIS)
        2. Register price update callback
        3. Monitor Track A data for triggers
        4. Update slots based on trigger candidates
        5. Subscribe/unsubscribe WebSocket symbols
        6. Collect and log real-time data
        """
        log.info("TrackBCollector started (max_slots=%d)", self.cfg.max_slots)
        self._running = True
        
        # Start WebSocket provider FIRST (before registering callbacks)
        await self._start_websocket()
        
        # Register WebSocket price update callback AFTER connection
        self._register_websocket_callback()
        
        try:
            while self._running:
                now = self._now()
                
                if not in_trading_hours(now, self.cfg.trading_start, self.cfg.trading_end):
                    log.info("Outside trading hours, waiting...")
                    await asyncio.sleep(60)
                    continue
                
                # Check Track A for triggers
                await self._check_triggers()
                
                # Wait before next check
                await asyncio.sleep(self.cfg.track_a_check_interval_seconds)
                
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
        Check Track A data for triggers and update slots.
        
        Process:
        1. Read latest Track A snapshots
        2. Feed to TriggerEngine
        3. Get trigger candidates
        4. Allocate/replace slots via SlotManager
        5. Update WebSocket subscriptions
        """
        try:
            # Read Track A snapshots from latest log file
            snapshots = await self._read_track_a_snapshots()
            if not snapshots:
                log.debug("No Track A snapshots available")
                return
            
            # Detect triggers
            candidates = self.trigger_engine.update(snapshots)
            
            if not candidates:
                log.debug("No trigger candidates detected")
                return
            
            log.info(f"🎯 Detected {len(candidates)} trigger candidates")
            
            # Process each candidate
            for candidate in candidates:
                slot_candidate = SlotCandidate(
                    symbol=candidate.symbol,
                    trigger_type=candidate.trigger_type,
                    priority_score=candidate.priority_score,
                    detected_at=candidate.detected_at
                )
                
                result = self.slot_manager.assign_slot(slot_candidate)
                
                if result.success:
                    log.info(
                        f"✅ Slot {result.slot_id}: {candidate.symbol} "
                        f"(priority={candidate.priority_score:.2f}, "
                        f"trigger={candidate.trigger_type})"
                    )
                    
                    # Subscribe to WebSocket if not already subscribed
                    await self._subscribe_symbol(candidate.symbol, result.slot_id)
                    
                    # Unsubscribe replaced symbol if any
                    if result.replaced_symbol:
                        await self._unsubscribe_symbol(result.replaced_symbol)
                        log.info(f"🔄 Replaced {result.replaced_symbol} with {candidate.symbol}")
                
                elif result.overflow:
                    log.warning(f"⚠️ Overflow: {candidate.symbol} (priority={candidate.priority_score:.2f})")
        
        except Exception as e:
            log.error(f"Error checking triggers: {e}", exc_info=True)
    
    async def _read_track_a_snapshots(self) -> List[PriceSnapshot]:
        """
        Read latest Track A snapshots from swing log file.
        
        Returns latest 10 minutes of data for trigger detection.
        """
        try:
            from datetime import timezone

            now = self._now().astimezone(timezone.utc)
            date_str = now.strftime("%Y%m%d")

            # Track A log path: config/observer/swing/YYYYMMDD.jsonl
            base_dir = observer_asset_dir()
            log_file = base_dir / self.cfg.daily_log_subdir.replace("scalp", "swing") / f"{date_str}.jsonl"

            if not log_file.exists():
                return []

            # Parse Track A JSONL using shared helper and keep last 10 minutes
            cutoff_time = now - timedelta(minutes=10)
            parsed = parse_track_a_jsonl(log_file)
            snapshots: List[PriceSnapshot] = []

            for snap in parsed:
                ts = snap.timestamp
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                ts_utc = ts.astimezone(timezone.utc)
                if ts_utc < cutoff_time:
                    continue

                snapshots.append(
                    PriceSnapshot(
                        symbol=snap.symbol,
                        timestamp=ts_utc,
                        price=float(snap.price or 0.0),
                        volume=int(snap.volume or 0),
                        open=snap.open,
                        high=snap.high,
                        low=snap.low,
                    )
                )

            return snapshots

        except Exception as e:
            log.error(f"Error reading Track A snapshots: {e}", exc_info=True)
            return []
    
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
        def on_price_update(data: Dict[str, Any]) -> None:
            """Handle real-time price updates from WebSocket"""
            try:
                log.debug(f"📊 Price update callback fired: {data.get('symbol')}")
                self._log_scalp_data(data)
            except Exception as e:
                log.error(f"Error handling price update: {e}", exc_info=True)
        
        # Set callback on provider engine
        self.engine.on_price_update = on_price_update
        log.info("✅ Price update callback registered")
    
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
        Log real-time scalp data to JSONL file.
        
        File: config/observer/scalp/YYYYMMDD.jsonl
        
        Enhanced record format includes execution time, bid/ask, and volume details
        for scalp strategy analysis.
        """
        try:
            now = self._now()
            date_str = now.strftime("%Y%m%d")
            
            # Scalp log path: config/observer/scalp/YYYYMMDD.jsonl
            base_dir = observer_asset_dir()
            log_dir = base_dir / self.cfg.daily_log_subdir
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / f"{date_str}.jsonl"
            
            # Prepare enhanced record
            record = {
                "timestamp": now.isoformat(),
                "symbol": data.get("symbol", ""),
                "execution_time": data.get("execution_time"),  # HHMMSS from WebSocket
                "price": {
                    "current": data.get("price", {}).get("close", 0),
                    "open": data.get("price", {}).get("open"),
                    "high": data.get("price", {}).get("high"),
                    "low": data.get("price", {}).get("low"),
                    "change_rate": data.get("price", {}).get("change_rate"),
                },
                "volume": {
                    "accumulated": data.get("volume", {}).get("accumulated", 0),
                    "trade_value": data.get("volume", {}).get("trade_value"),
                },
                "bid_ask": data.get("bid_ask", {}),  # {bid_price, ask_price}
                "source": "websocket",
                "session_id": self.cfg.session_id
            }
            
            # Write to file
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
        except Exception as e:
            log.error(f"Error logging scalp data: {e}", exc_info=True)
    
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
    
    collector = TrackBCollector(
        engine=engine,
        trigger_engine=trigger_engine
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
