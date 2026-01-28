"""
Test SlotManager overflow file creation

This test verifies that SlotManager creates overflow ledger files
in the correct location: app/observer/config/system/overflow_YYYYMMDD.jsonl
"""
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# Add app/observer/src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app" / "observer" / "src"))

from slot.slot_manager import SlotManager, SlotCandidate
from paths import system_log_dir


def test_overflow_file_creation():
    """Test that overflow ledger is created in correct location"""
    print("=" * 60)
    print("SlotManager Overflow File Creation Test")
    print("=" * 60)
    
    # Create SlotManager with only 3 slots
    manager = SlotManager(max_slots=3, min_dwell_seconds=10)
    
    # Expected overflow file path
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    date_str = now.strftime("%Y%m%d")
    expected_path = system_log_dir() / f"overflow_{date_str}.jsonl"
    
    print(f"\n📁 Expected overflow file: {expected_path}")
    print(f"📁 System log directory: {system_log_dir()}")
    
    # Fill all slots
    print("\n🔧 Filling 3 slots...")
    symbols = ["005930", "000660", "373220"]
    for i, symbol in enumerate(symbols):
        candidate = SlotCandidate(
            symbol=symbol,
            trigger_type="volume_surge",
            priority_score=0.9 - (i * 0.1),
            detected_at=now
        )
        result = manager.assign_slot(candidate)
        print(f"  Slot {i+1}: {symbol} - {'✅ Assigned' if result.success else '❌ Failed'}")
    
    # Try to assign 4th symbol (should overflow)
    print("\n⚠️ Attempting to add 4th symbol (should trigger overflow)...")
    overflow_candidate = SlotCandidate(
        symbol="035720",
        trigger_type="volume_surge",
        priority_score=0.5,  # Lower priority than existing ones
        detected_at=now
    )
    result = manager.assign_slot(overflow_candidate)
    
    print(f"  Result: {'Overflow' if result.overflow else 'Assigned'}")
    print(f"  Overflow flag: {result.overflow}")
    
    # Check if overflow file was created
    print(f"\n📊 Checking overflow file existence...")
    if expected_path.exists():
        file_size = expected_path.stat().st_size
        print(f"  ✅ Overflow file created: {expected_path}")
        print(f"  📏 File size: {file_size} bytes")
        
        # Read and display content
        with open(expected_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"  📄 Lines in file: {len(lines)}")
            if lines:
                print(f"\n  First entry:")
                print(f"  {lines[0].strip()}")
    else:
        print(f"  ❌ Overflow file NOT created at {expected_path}")
        print(f"  ⚠️ This indicates a path configuration issue")
    
    # Display stats
    stats = manager.get_stats()
    print(f"\n📈 SlotManager Stats:")
    print(f"  Total allocations: {stats['total_allocations']}")
    print(f"  Total replacements: {stats['total_replacements']}")
    print(f"  Total overflows: {stats['total_overflows']}")
    print(f"  Allocated slots: {stats['allocated_slots']}")
    print(f"  Available slots: {stats['available_slots']}")
    
    # Verify the test
    print("\n" + "=" * 60)
    if expected_path.exists() and result.overflow and stats['total_overflows'] > 0:
        print("✅ TEST PASSED: Overflow file created successfully")
        return True
    else:
        print("❌ TEST FAILED: Overflow file not created or wrong behavior")
        return False


if __name__ == "__main__":
    success = test_overflow_file_creation()
    sys.exit(0 if success else 1)
