"""
Track B Mock Testing Suite

강제로 Track B를 테스트하기 위한 도구:
1. Mock Track A 로그 생성
2. TriggerEngine 단위 테스트
3. SlotManager 단위 테스트
4. 통합 테스트 (Mock WebSocket)

실행:
  python test/test_track_b_mock.py --mode=full
  python test/test_track_b_mock.py --mode=triggers
  python test/test_track_b_mock.py --mode=slots
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any
import sys
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "app" / "observer" / "src"))

from trigger.trigger_engine import TriggerEngine, TriggerConfig, PriceSnapshot
from slot.slot_manager import SlotManager, SlotCandidate
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("TrackBMockTest")


# ============================================================================
# PART 1: Mock Track A Data Generation
# ============================================================================

def generate_mock_track_a_log(
    symbols: List[str] = None,
    num_snapshots: int = 30,
    duration_minutes: int = 15,
    trigger_indices: List[int] = None,
    output_file: Path = None
) -> Path:
    """
    Generate mock Track A swing log with optional trigger events.
    
    Args:
        symbols: List of stock symbols (default: test symbols)
        num_snapshots: Number of price snapshots to generate
        duration_minutes: Span of time for snapshots (default: 15 min)
        trigger_indices: Indices where to inject trigger events (e.g., [5, 15, 25])
        output_file: Output JSONL file path
    
    Returns:
        Path to generated log file
    """
    if symbols is None:
        symbols = ["005930", "000660", "051910", "012330", "028260"]
    
    if trigger_indices is None:
        trigger_indices = [5, 15, 25]  # Trigger at these snapshot indices
    
    if output_file is None:
        output_file = Path(__file__).parent / "test_data" / "mock_swing.jsonl"
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    now = datetime.now(timezone.utc)
    base_time = now - timedelta(minutes=duration_minutes)
    
    log.info(f"📝 Generating mock Track A log: {output_file}")
    log.info(f"   Symbols: {symbols}")
    log.info(f"   Snapshots: {num_snapshots} over {duration_minutes} minutes")
    log.info(f"   Trigger indices: {trigger_indices}")
    
    with open(output_file, "w", encoding="utf-8") as f:
        for i in range(num_snapshots):
            for symbol in symbols:
                # Time progression
                ts = base_time + timedelta(minutes=i * (duration_minutes / num_snapshots))
                
                # Base price (varies by symbol for realism)
                base_price = {
                    "005930": 70000,
                    "000660": 95000,
                    "051910": 156000,
                    "012330": 64000,
                    "028260": 41000,
                }.get(symbol, 50000)
                
                # Generate price with some variance
                price_variance = (hash(f"{symbol}_{i}") % 200 - 100) * 10  # ±1000
                price = base_price + price_variance
                
                # Volume - normal, except at trigger indices
                base_volume = 100000 + (i % 10) * 10000  # 100K-190K
                
                if i in trigger_indices:
                    # TRIGGER EVENT: Volume surge or volatility spike
                    trigger_type = "volume_surge" if i % 2 == 0 else "volatility_spike"
                    
                    if trigger_type == "volume_surge":
                        # 5x volume surge
                        volume = base_volume * 5
                        price = base_price + (base_price * 0.02)  # 2% up
                        log.info(f"🎯 TRIGGER at snapshot {i}: {symbol} VOLUME_SURGE")
                    else:
                        # Volatility spike: 5% price change
                        volume = base_volume * 3
                        price = base_price * 1.05  # 5% up
                        log.info(f"🎯 TRIGGER at snapshot {i}: {symbol} VOLATILITY_SPIKE")
                else:
                    volume = base_volume
                
                # Open/High/Low
                open_price = base_price
                high_price = max(price, base_price) + (hash(symbol + str(i)) % 1000)
                low_price = min(price, base_price) - (hash(symbol + str(i+1)) % 1000)
                
                record = {
                    "timestamp": ts.isoformat(),
                    "symbol": symbol,
                    "price": int(price),
                    "volume": int(volume),
                    "open": int(open_price),
                    "high": int(high_price),
                    "low": int(low_price),
                }
                
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    log.info(f"✅ Mock log created: {output_file}")
    return output_file


def load_mock_track_a_log(log_file: Path) -> List[PriceSnapshot]:
    """Load and parse mock Track A log."""
    snapshots = []
    
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            ts = datetime.fromisoformat(data["timestamp"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            
            snapshots.append(
                PriceSnapshot(
                    symbol=data["symbol"],
                    timestamp=ts,
                    price=float(data["price"]),
                    volume=int(data["volume"]),
                    open=float(data.get("open")),
                    high=float(data.get("high")),
                    low=float(data.get("low")),
                )
            )
    
    return snapshots


# ============================================================================
# PART 2: Unit Tests
# ============================================================================

def test_trigger_engine():
    """Test TriggerEngine trigger detection."""
    log.info("\n" + "="*60)
    log.info("TEST: TriggerEngine Trigger Detection")
    log.info("="*60)
    
    # Generate mock data with triggers
    log_file = generate_mock_track_a_log(
        num_snapshots=30,
        trigger_indices=[5, 15, 25],
    )
    
    # Load snapshots
    snapshots = load_mock_track_a_log(log_file)
    log.info(f"Loaded {len(snapshots)} snapshots")
    
    # Initialize trigger engine
    config = TriggerConfig(
        volume_surge_ratio=5.0,
        volatility_spike_threshold=0.05,
        min_priority_score=0.5,
    )
    engine = TriggerEngine(config=config)
    
    # Feed snapshots in batches (simulating 60-sec interval checks)
    batch_size = 6  # Each batch ~6 snapshots
    total_candidates = []
    
    for batch_idx in range(0, len(snapshots), batch_size):
        batch = snapshots[batch_idx:batch_idx + batch_size]
        candidates = engine.update(batch)
        
        if candidates:
            log.info(f"\n📊 Batch {batch_idx//batch_size}: {len(candidates)} candidates detected")
            for c in candidates:
                log.info(
                    f"   🎯 {c.symbol}: {c.trigger_type} "
                    f"(priority={c.priority_score:.2f})"
                )
                total_candidates.append(c)
        else:
            log.info(f"📊 Batch {batch_idx//batch_size}: No triggers")
    
    log.info(f"\n✅ Total candidates detected: {len(total_candidates)}")
    return len(total_candidates) > 0


def test_slot_manager():
    """Test SlotManager slot allocation and replacement."""
    log.info("\n" + "="*60)
    log.info("TEST: SlotManager Allocation & Replacement")
    log.info("="*60)
    
    manager = SlotManager(max_slots=5, min_dwell_seconds=120)
    
    # Simulate candidates arriving with different priorities
    now = datetime.now(timezone.utc)
    candidates = [
        SlotCandidate(symbol="005930", trigger_type="volume_surge", priority_score=0.95, detected_at=now),
        SlotCandidate(symbol="000660", trigger_type="volatility_spike", priority_score=0.90, detected_at=now),
        SlotCandidate(symbol="051910", trigger_type="volume_surge", priority_score=0.88, detected_at=now),
        SlotCandidate(symbol="012330", trigger_type="volatility_spike", priority_score=0.85, detected_at=now),
        SlotCandidate(symbol="028260", trigger_type="volume_surge", priority_score=0.92, detected_at=now),
        SlotCandidate(symbol="036570", trigger_type="volatility_spike", priority_score=0.87, detected_at=now),  # Would overflow
    ]
    
    for i, candidate in enumerate(candidates):
        result = manager.assign_slot(candidate)
        
        if result.success:
            log.info(
                f"✅ Slot {result.slot_id}: {candidate.symbol} "
                f"(priority={candidate.priority_score:.2f})"
            )
        elif result.overflow:
            log.warning(
                f"⚠️ OVERFLOW: {candidate.symbol} "
                f"(priority={candidate.priority_score:.2f})"
            )
        else:
            log.warning(
                f"❌ FAILED: {candidate.symbol} "
                f"(reason: {result.failure_reason})"
            )
    
    # Check stats
    stats = manager.get_stats()
    log.info(f"\n📊 Final Stats:")
    log.info(f"   Allocated slots: {stats['allocated_slots']}")
    log.info(f"   Available slots: {stats['available_slots']}")
    log.info(f"   Total allocations: {stats['total_allocations']}")
    log.info(f"   Total replacements: {stats['total_replacements']}")
    log.info(f"   Total overflows: {stats['total_overflows']}")
    
    return stats['allocated_slots'] > 0


def test_integration():
    """Integration test: Trigger → Slot Manager → Log."""
    log.info("\n" + "="*60)
    log.info("TEST: Integration - Trigger → Slot Manager → Logging")
    log.info("="*60)
    
    # Step 1: Generate mock Track A log
    log_file = generate_mock_track_a_log(
        num_snapshots=20,
        trigger_indices=[5, 10, 15],
    )
    
    # Step 2: Load and process with TriggerEngine
    snapshots = load_mock_track_a_log(log_file)
    engine = TriggerEngine()
    all_candidates = engine.update(snapshots)
    
    log.info(f"\n📊 Step 1: TriggerEngine detected {len(all_candidates)} candidates")
    
    # Step 3: Allocate slots
    manager = SlotManager(max_slots=10, min_dwell_seconds=120)
    allocated = []
    
    for candidate in all_candidates:
        result = manager.assign_slot(candidate)
        if result.success:
            allocated.append({
                "symbol": candidate.symbol,
                "slot_id": result.slot_id,
                "priority": candidate.priority_score,
                "trigger_type": candidate.trigger_type,
            })
    
    log.info(f"✅ Step 2: SlotManager allocated {len(allocated)} symbols to slots")
    for alloc in allocated:
        log.info(
            f"   Slot {alloc['slot_id']}: {alloc['symbol']} "
            f"({alloc['trigger_type']}, priority={alloc['priority']:.2f})"
        )
    
    # Step 4: Simulate logging
    scalp_log_file = Path(__file__).parent / "test_data" / "mock_scalp.jsonl"
    scalp_log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(scalp_log_file, "w", encoding="utf-8") as f:
        for alloc in allocated:
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "symbol": alloc["symbol"],
                "slot_id": alloc["slot_id"],
                "trigger_type": alloc["trigger_type"],
                "priority_score": alloc["priority"],
                "source": "mock_test",
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    log.info(f"✅ Step 3: Logged {len(allocated)} records to {scalp_log_file}")
    
    return len(allocated) > 0


# ============================================================================
# PART 3: CLI Interface
# ============================================================================

async def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Track B Mock Testing Suite")
    parser.add_argument(
        "--mode",
        choices=["full", "triggers", "slots", "integration"],
        default="full",
        help="Test mode to run"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("🧪 TRACK B MOCK TESTING SUITE")
    print("="*70)
    print(f"Mode: {args.mode}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("="*70 + "\n")
    
    results = {}
    
    try:
        if args.mode in ["full", "triggers"]:
            results["trigger_engine"] = test_trigger_engine()
        
        if args.mode in ["full", "slots"]:
            results["slot_manager"] = test_slot_manager()
        
        if args.mode in ["full", "integration"]:
            results["integration"] = test_integration()
        
        # Summary
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {test_name}")
        
        all_passed = all(results.values())
        print("="*70)
        if all_passed:
            print("✅ ALL TESTS PASSED")
        else:
            print("❌ SOME TESTS FAILED")
        print("="*70 + "\n")
        
        return 0 if all_passed else 1
    
    except Exception as e:
        log.error(f"❌ Test failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
