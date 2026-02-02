"""
Simple Force-Test for Track B without needing Market Hours

The simplest way to test Track B components:
1. Create a mock Track A snapshot with obvious triggers
2. Run TriggerEngine to detect them
3. Run SlotManager to allocate slots
4. Verify behavior

실행:
  python test/test_track_b_simple.py
"""

import sys
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("TrackBSimpleTest")

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from trigger.trigger_engine import TriggerEngine, TriggerConfig, PriceSnapshot
from slot.slot_manager import SlotManager, SlotCandidate


def test_trigger_engine_direct():
    """
    Test TriggerEngine directly with explicit trigger events.
    """
    log.info("="*70)
    log.info("TEST 1: TriggerEngine Direct Testing")
    log.info("="*70)
    
    # Create engine with DEFAULT config
    config = TriggerConfig()
    log.info(f"TriggerEngine Config: {config}")
    
    engine = TriggerEngine(config=config)
    
    # Create explicit trigger events
    now = datetime.now(timezone.utc)
    
    # Test Case 1: Volume Surge (5x increase)
    log.info("\n📝 Test 1A: Volume Surge (5x volume increase)")
    
    # First, build history with baseline volume
    engine = TriggerEngine(config=config)
    baseline_snapshots = []
    for i in range(10):  # 10 snapshots for history
        baseline_snapshots.append(
            PriceSnapshot(
                symbol="005930",
                timestamp=now - timedelta(minutes=i),
                price=70000,
                open=70000,
                high=70100,
                low=69900,
                volume=100000  # Consistent baseline
            )
        )
    
    # Add baseline history first
    engine.update(baseline_snapshots)
    
    # Check history was added
    history = engine.get_history("005930", minutes=10)
    log.info(f"📊 History length after baseline: {len(history)}")
    if history:
        avg_volume = sum(h.volume for h in history) / len(history)
        log.info(f"📊 Average volume in history: {avg_volume}")
    
    # Now add trigger snapshot
    trigger_snapshots = [
        # TRIGGER: 5x volume surge
        PriceSnapshot(
            symbol="005930",
            timestamp=now,
            price=70500,
            open=70000,
            high=70500,
            low=69900,
            volume=1000000  # 10x to ensure trigger
        ),
    ]
    
    candidates = engine.update(trigger_snapshots)
    
    # Debug: Check final history and calculation
    final_history = engine.get_history("005930", minutes=10)
    log.info(f"📊 Final history length: {len(final_history)}")
    if final_history:
        # Find the trigger snapshot (last one with high volume)
        trigger_snap = None
        for snap in final_history:
            if snap.volume == 1000000:
                trigger_snap = snap
                break
        
        if trigger_snap:
            # Manually calculate volume surge
            total_volume = sum(h.volume for h in final_history)
            avg_volume = total_volume / len(final_history)
            surge_ratio = trigger_snap.volume / avg_volume
            log.info(f"📊 Manual calculation:")
            log.info(f"   - Trigger volume: {trigger_snap.volume}")
            log.info(f"   - Average volume: {avg_volume}")
            log.info(f"   - Surge ratio: {surge_ratio}")
            log.info(f"   - Threshold: {engine.cfg.volume_surge_ratio}")
            log.info(f"   - Should trigger: {surge_ratio >= engine.cfg.volume_surge_ratio}")
    
    log.info(f"📊 Candidates detected: {len(candidates)}")
    for c in candidates:
        log.info(f"   - {c.symbol}: {c.trigger_type} (priority={c.priority_score:.3f})")
    
    if candidates:
        log.info("✅ PASS: Volume surge detected")
    else:
        log.warning("❌ FAIL: Volume surge NOT detected")
    
    # Test Case 2: Volatility Spike (5% price move)
    log.info("\n📝 Test 1B: Volatility Spike (5% price increase)")
    
    engine2 = TriggerEngine(config=config)
    snapshots2 = [
        # Baseline
        PriceSnapshot(
            symbol="000660",
            timestamp=now,
            price=95000,
            open=95000,
            high=95100,
            low=94900,
            volume=100000
        ),
        # TRIGGER: 5% price jump
        PriceSnapshot(
            symbol="000660",
            timestamp=now,
            price=100000,  # 5.26% up
            open=95000,
            high=100000,
            low=94900,
            volume=100000
        ),
    ]
    
    candidates2 = engine2.update(snapshots2)
    log.info(f"📊 Candidates detected: {len(candidates2)}")
    for c in candidates2:
        log.info(f"   - {c.symbol}: {c.trigger_type} (priority={c.priority_score:.3f})")
    
    if candidates2:
        log.info("✅ PASS: Volatility spike detected")
    else:
        log.warning("❌ FAIL: Volatility spike NOT detected")


def test_slot_manager_direct():
    """
    Test SlotManager directly with manual candidates.
    """
    log.info("\n" + "="*70)
    log.info("TEST 2: SlotManager Direct Testing")
    log.info("="*70)
    
    manager = SlotManager(max_slots=5, min_dwell_seconds=120)
    
    now = datetime.now(timezone.utc)
    
    # Create 6 candidates (1 should overflow)
    candidates = [
        SlotCandidate("005930", "volume_surge", 0.95, now),
        SlotCandidate("000660", "volatility_spike", 0.90, now),
        SlotCandidate("051910", "volume_surge", 0.88, now),
        SlotCandidate("012330", "volatility_spike", 0.85, now),
        SlotCandidate("028260", "volume_surge", 0.92, now),
        SlotCandidate("036570", "volatility_spike", 0.87, now),  # Should overflow
    ]
    
    log.info(f"\n📝 Allocating {len(candidates)} candidates to {manager.max_slots} slots")
    
    results = []
    for candidate in candidates:
        result = manager.assign_slot(candidate)
        results.append(result)
        
        if result.success:
            log.info(f"✅ Allocated: {candidate.symbol} to slot {result.slot_id}")
        else:
            log.warning(f"⚠️ Overflow: {candidate.symbol}")
    
    stats = manager.get_stats()
    log.info(f"\n📊 Stats:")
    log.info(f"   - Allocated slots: {stats['allocated_slots']}")
    log.info(f"   - Available slots: {stats['available_slots']}")
    log.info(f"   - Total overflows: {stats['total_overflows']}")
    
    # Verify results
    allocated_count = sum(1 for r in results if r.success)
    overflow_count = sum(1 for r in results if r.overflow)
    
    log.info(f"\n📊 Verification:")
    log.info(f"   - Expected allocated: 5, Got: {allocated_count}")
    log.info(f"   - Expected overflow: 1, Got: {overflow_count}")
    
    if allocated_count == 5 and overflow_count == 1:
        log.info("✅ PASS: Slot allocation working correctly")
    else:
        log.warning("❌ FAIL: Slot allocation mismatch")


def main():
    log.info("\n")
    log.info("╔" + "="*68 + "╗")
    log.info("║  TRACK B FORCE-TEST SUITE (Without Market Hours)  ".center(68) + "║")
    log.info("╚" + "="*68 + "╝")
    
    try:
        test_trigger_engine_direct()
        test_slot_manager_direct()
        
        log.info("\n" + "="*70)
        log.info("✅ ALL TESTS COMPLETED")
        log.info("="*70)
        
    except Exception as e:
        log.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
