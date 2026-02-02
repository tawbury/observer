"""
Track B Full Integration Test with Mock WebSocket

Track B 전체 파이프라인을 강제로 테스트합니다:
1. Track A 모의 데이터 생성 (Trigger 이벤트 포함)
2. TriggerEngine으로 Trigger 감지
3. SlotManager로 심볼 할당
4. Mock WebSocket으로 실시간 Tick 생성
5. Track B에서 Tick 로깅

실행:
  python test/test_track_b_integration.py --duration=60 --mode=full
  python test/test_track_b_integration.py --duration=30 --mode=triggers_only
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
import argparse

# Setup path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from trigger.trigger_engine import TriggerEngine, TriggerConfig, PriceSnapshot
from slot.slot_manager import SlotManager, SlotCandidate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("TrackBIntegrationTest")


# ============================================================================
# Mock Track A Snapshot Generator
# ============================================================================

class MockTrackAGenerator:
    """Simulates Track A snapshot generation with trigger events."""
    
    def __init__(self, symbols: List[str] = None):
        self.symbols = symbols or ["005930", "000660", "051910", "012330", "028260"]
        self.base_prices = {
            "005930": 70000,
            "000660": 95000,
            "051910": 156000,
            "012330": 64000,
            "028260": 41000,
        }
        self.tick_count = 0
    
    def generate_snapshot(self) -> List[PriceSnapshot]:
        """
        Generate a batch of snapshots (simulating 60-sec interval).
        Injects trigger events randomly.
        """
        snapshots = []
        now = datetime.now(timezone.utc)
        
        for symbol in self.symbols:
            base_price = self.base_prices.get(symbol, 50000)
            
            # Determine if this symbol should trigger
            trigger = self.tick_count % 5 == 0  # Trigger every 5 snapshots
            
            if trigger:
                # TRIGGER: Volume surge or volatility spike
                is_volume = self.tick_count % 10 < 5
                
                if is_volume:
                    # Volume surge: 5x normal volume
                    volume = 500000 + (self.tick_count % 100000)
                    price = base_price * 1.01  # 1% price movement
                else:
                    # Volatility spike: 5% price change
                    volume = 200000
                    price = base_price * 1.05
            else:
                # Normal movement
                variance = (self.tick_count % 10 - 5) * 500
                price = base_price + variance
                volume = 100000 + (self.tick_count % 50000)
            
            snapshot = PriceSnapshot(
                symbol=symbol,
                timestamp=now,
                price=float(int(price)),
                volume=int(volume),
                open=float(base_price),
                high=float(int(price) + 1000),
                low=float(int(price) - 1000),
            )
            snapshots.append(snapshot)
        
        self.tick_count += 1
        return snapshots


# ============================================================================
# Mock WebSocket Provider (from test_websocket_mock.py)
# ============================================================================

class MockKISWebSocketProvider:
    """Mock WebSocket provider for testing."""
    
    def __init__(self, symbols: set = None):
        self.subscribed_symbols: set = symbols or set()
        self.is_connected = False
        self.on_price_update: Optional[Callable[[Dict[str, Any]], None]] = None
        self._tick_task: Optional[asyncio.Task] = None
        self._tick_count = 0
        
        self.base_prices = {
            "005930": 70000,
            "000660": 95000,
            "051910": 156000,
            "012330": 64000,
            "028260": 41000,
        }
    
    async def connect(self) -> bool:
        log.info("📡 Mock WebSocket: Connecting...")
        await asyncio.sleep(0.05)
        self.is_connected = True
        log.info("✅ Mock WebSocket: Connected")
        self._tick_task = asyncio.create_task(self._generate_ticks())
        return True
    
    async def disconnect(self) -> None:
        log.info("📡 Mock WebSocket: Disconnecting...")
        self.is_connected = False
        if self._tick_task and not self._tick_task.done():
            self._tick_task.cancel()
            try:
                await self._tick_task
            except asyncio.CancelledError:
                pass
    
    async def subscribe(self, symbol: str) -> bool:
        self.subscribed_symbols.add(symbol)
        log.info(f"✅ Mock WebSocket: Subscribed {symbol}")
        return True
    
    async def unsubscribe(self, symbol: str) -> bool:
        self.subscribed_symbols.discard(symbol)
        log.info(f"✅ Mock WebSocket: Unsubscribed {symbol}")
        return True
    
    async def _generate_ticks(self) -> None:
        try:
            while self.is_connected and self._tick_count < 100:
                now = datetime.now(timezone.utc)
                time_str = now.strftime("%H%M%S")
                
                for symbol in list(self.subscribed_symbols):
                    base_price = self.base_prices.get(symbol, 50000)
                    variance = (self._tick_count % 5 - 2) * 100
                    price = base_price + variance
                    
                    if self.on_price_update:
                        price_data = {
                            "symbol": symbol,
                            "execution_time": time_str,
                            "timestamp": now.isoformat(),
                            "price": {
                                "close": int(price),
                                "change_rate": (variance / base_price) * 100,
                            },
                            "volume": {
                                "accumulated": 1000 + (self._tick_count % 2000),
                            },
                            "bid_ask": {
                                "bid_price": int(price - 50),
                                "ask_price": int(price + 50),
                            },
                            "source": "mock_websocket"
                        }
                        self.on_price_update(price_data)
                
                self._tick_count += 1
                await asyncio.sleep(0.5)  # 2Hz
        except asyncio.CancelledError:
            pass
    
    @property
    def subscription_count(self) -> int:
        return len(self.subscribed_symbols)


# ============================================================================
# Integration Test
# ============================================================================

async def run_integration_test(
    duration: int = 60,
    mode: str = "full"
):
    """
    Run full Track B integration test.
    
    Args:
        duration: Test duration in seconds
        mode: "full" (everything) or "triggers_only" (no WebSocket)
    """
    print("\n" + "="*70)
    print("🧪 TRACK B FULL INTEGRATION TEST")
    print("="*70)
    print(f"Mode: {mode}")
    print(f"Duration: {duration}s")
    print("="*70 + "\n")
    
    # Initialize components
    track_a_gen = MockTrackAGenerator()
    trigger_engine = TriggerEngine(TriggerConfig())
    slot_manager = SlotManager(max_slots=41, min_dwell_seconds=60)
    ws_provider = MockKISWebSocketProvider()
    
    # Setup logging
    scalp_log_file = Path(__file__).parent / "test_data" / "integration_scalp.jsonl"
    scalp_log_file.parent.mkdir(parents=True, exist_ok=True)
    scalp_log = open(scalp_log_file, "w", encoding="utf-8")
    
    # Stats
    stats = {
        "snapshots": 0,
        "triggers": 0,
        "allocated": 0,
        "ticks": 0,
        "logs": 0,
    }
    
    def on_price_update(data: Dict[str, Any]) -> None:
        """WebSocket callback - log scalp data."""
        stats["ticks"] += 1
        record = {
            "timestamp": data["timestamp"],
            "symbol": data["symbol"],
            "price": data["price"]["close"],
            "volume": data["volume"].get("accumulated"),
            "source": data["source"],
        }
        scalp_log.write(json.dumps(record, ensure_ascii=False) + "\n")
        stats["logs"] += 1
        
        if stats["logs"] % 20 == 1:
            log.debug(f"📝 Logged {stats['logs']} tick records")
    
    # Connect WebSocket
    if mode == "full":
        await ws_provider.connect()
        ws_provider.on_price_update = on_price_update
    
    try:
        # Main loop
        start_time = datetime.now(timezone.utc)
        last_trigger_check = start_time
        
        while (datetime.now(timezone.utc) - start_time).total_seconds() < duration:
            # Every 2 seconds, generate Track A snapshots and check triggers
            if (datetime.now(timezone.utc) - last_trigger_check).total_seconds() >= 2:
                # Step 1: Generate Track A snapshots
                snapshots = track_a_gen.generate_snapshot()
                stats["snapshots"] += len(snapshots)
                
                # Step 2: Detect triggers
                candidates = trigger_engine.update(snapshots)
                
                if candidates:
                    stats["triggers"] += len(candidates)
                    log.info(f"🎯 Detected {len(candidates)} trigger candidates")
                    
                    # Step 3: Allocate slots
                    now = datetime.now(timezone.utc)
                    for candidate in candidates:
                        result = slot_manager.assign_slot(
                            SlotCandidate(
                                symbol=candidate.symbol,
                                trigger_type=candidate.trigger_type,
                                priority_score=candidate.priority_score,
                                detected_at=now
                            )
                        )
                        
                        if result.success:
                            stats["allocated"] += 1
                            log.info(
                                f"✅ Slot {result.slot_id}: {candidate.symbol} "
                                f"(priority={candidate.priority_score:.2f})"
                            )
                            
                            # Step 4: Subscribe to WebSocket
                            if mode == "full":
                                await ws_provider.subscribe(candidate.symbol)
                            
                            # Unsubscribe replaced
                            if result.replaced_symbol and mode == "full":
                                await ws_provider.unsubscribe(result.replaced_symbol)
                
                last_trigger_check = datetime.now(timezone.utc)
            
            await asyncio.sleep(0.1)
        
        # Summary
        print("\n" + "="*70)
        print("📊 INTEGRATION TEST SUMMARY")
        print("="*70)
        print(f"Track A Snapshots: {stats['snapshots']}")
        print(f"Triggers Detected: {stats['triggers']}")
        print(f"Symbols Allocated: {stats['allocated']}")
        if mode == "full":
            print(f"WebSocket Ticks: {stats['ticks']}")
            print(f"Scalp Logs: {stats['logs']}")
        print(f"WebSocket Subscriptions: {ws_provider.subscription_count}")
        print("="*70)
        
        # Check scalp log
        scalp_log.flush()
        log_size = scalp_log_file.stat().st_size
        print(f"\n✅ Scalp log saved to: {scalp_log_file}")
        print(f"   Size: {log_size} bytes")
        print(f"   Records: {stats['logs']}")
        
        return stats["allocated"] > 0 and stats["logs"] > 0 if mode == "full" else stats["allocated"] > 0
    
    finally:
        scalp_log.close()
        if mode == "full":
            await ws_provider.disconnect()


async def main():
    parser = argparse.ArgumentParser(description="Track B Integration Test")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("--mode", choices=["full", "triggers_only"], default="full")
    
    args = parser.parse_args()
    
    success = await run_integration_test(
        duration=args.duration,
        mode=args.mode
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
