"""
Slot Manager - 41-slot management for Track B collector

Key Responsibilities:
- Manage 41 WebSocket subscription slots
- Priority-based slot allocation and replacement
- Minimum dwell time enforcement (2 minutes)
- Overflow ledger for rejected candidates
"""
import os
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict
from collections import deque

try:
    from paths import system_log_dir
except ImportError:
    system_log_dir = None  # type: ignore


@dataclass
class SlotCandidate:
    """Candidate for slot allocation"""
    symbol: str
    trigger_type: str  # "volume_surge", "volatility_spike", etc.
    priority_score: float  # 0.0 ~ 1.0
    detected_at: datetime
    
    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "trigger_type": self.trigger_type,
            "priority_score": self.priority_score,
            "detected_at": self.detected_at.isoformat()
        }


@dataclass
class SlotInfo:
    """Information about an allocated slot"""
    slot_id: int
    symbol: str
    trigger_type: str
    priority_score: float
    allocated_at: datetime
    last_update: datetime
    
    def to_dict(self) -> dict:
        return {
            "slot_id": self.slot_id,
            "symbol": self.symbol,
            "trigger_type": self.trigger_type,
            "priority_score": self.priority_score,
            "allocated_at": self.allocated_at.isoformat(),
            "last_update": self.last_update.isoformat()
        }


@dataclass
class AllocationResult:
    """Result of slot allocation attempt"""
    success: bool
    slot_id: Optional[int]
    overflow: bool
    replaced_symbol: Optional[str]
    reason: str


class SlotManager:
    """
    Manages 41 WebSocket subscription slots for Track B collector.
    
    Features:
    - Priority-based slot allocation
    - Minimum dwell time (2 minutes)
    - Automatic overflow ledger
    - Slot replacement policy
    """
    
    def __init__(
        self,
        max_slots: int = 41,
        min_dwell_seconds: int = 120,
        overflow_ledger_dir: Optional[str] = None
    ):
        self.max_slots = max_slots
        self.min_dwell_seconds = min_dwell_seconds
        
        # Slot state: slot_id -> SlotInfo
        self.slots: Dict[int, Optional[SlotInfo]] = {i: None for i in range(max_slots)}
        
        # Overflow ledger - resolve via paths.py or fallback
        if overflow_ledger_dir is not None:
            self.overflow_ledger_dir = Path(overflow_ledger_dir)
        elif system_log_dir is not None:
            self.overflow_ledger_dir = system_log_dir()
        else:
            # Fallback: relative to current file
            self.overflow_ledger_dir = Path(__file__).resolve().parents[4] / "logs" / "system"
        self.overflow_ledger_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            "total_allocations": 0,
            "total_replacements": 0,
            "total_overflows": 0,
            "total_releases": 0
        }
    
    def assign_slot(self, candidate: SlotCandidate) -> AllocationResult:
        """
        Assign a slot to a candidate.
        
        Priority:
        1. Find an empty slot
        2. Replace a slot with lower priority (respecting min_dwell_time)
        3. Log to overflow ledger if no slot available
        
        Returns:
            AllocationResult with success status and slot_id
        """
        now = datetime.now(timezone.utc)
        
        # Step 1: Check if symbol already has a slot
        existing_slot = self._find_slot_by_symbol(candidate.symbol)
        if existing_slot is not None:
            # Update priority if higher
            slot_info = self.slots[existing_slot]
            if slot_info and candidate.priority_score > slot_info.priority_score:
                slot_info.priority_score = candidate.priority_score
                slot_info.trigger_type = candidate.trigger_type
                slot_info.last_update = now
                return AllocationResult(
                    success=True,
                    slot_id=existing_slot,
                    overflow=False,
                    replaced_symbol=None,
                    reason="updated_existing_slot"
                )
            else:
                return AllocationResult(
                    success=True,
                    slot_id=existing_slot,
                    overflow=False,
                    replaced_symbol=None,
                    reason="already_allocated"
                )
        
        # Step 2: Find an empty slot
        empty_slot = self._find_empty_slot()
        if empty_slot is not None:
            slot_info = SlotInfo(
                slot_id=empty_slot,
                symbol=candidate.symbol,
                trigger_type=candidate.trigger_type,
                priority_score=candidate.priority_score,
                allocated_at=now,
                last_update=now
            )
            self.slots[empty_slot] = slot_info
            self.stats["total_allocations"] += 1
            return AllocationResult(
                success=True,
                slot_id=empty_slot,
                overflow=False,
                replaced_symbol=None,
                reason="allocated_empty_slot"
            )
        
        # Step 3: Try to replace a lower-priority slot
        replaceable_slot = self._find_replaceable_slot(candidate.priority_score, now)
        if replaceable_slot is not None:
            old_symbol = self.slots[replaceable_slot].symbol
            slot_info = SlotInfo(
                slot_id=replaceable_slot,
                symbol=candidate.symbol,
                trigger_type=candidate.trigger_type,
                priority_score=candidate.priority_score,
                allocated_at=now,
                last_update=now
            )
            self.slots[replaceable_slot] = slot_info
            self.stats["total_replacements"] += 1
            return AllocationResult(
                success=True,
                slot_id=replaceable_slot,
                overflow=False,
                replaced_symbol=old_symbol,
                reason="replaced_lower_priority"
            )
        
        # Step 4: Overflow - log to ledger
        self._log_overflow(candidate, now)
        self.stats["total_overflows"] += 1
        return AllocationResult(
            success=False,
            slot_id=None,
            overflow=True,
            replaced_symbol=None,
            reason="overflow_all_slots_occupied"
        )
    
    def release_slot(self, slot_id: int) -> bool:
        """
        Release a slot by slot_id.
        
        Returns:
            True if slot was released, False if slot was already empty
        """
        if slot_id < 0 or slot_id >= self.max_slots:
            return False
        
        if self.slots[slot_id] is not None:
            self.slots[slot_id] = None
            self.stats["total_releases"] += 1
            return True
        return False
    
    def release_symbol(self, symbol: str) -> bool:
        """
        Release a slot by symbol.
        
        Returns:
            True if slot was released, False if symbol not found
        """
        slot_id = self._find_slot_by_symbol(symbol)
        if slot_id is not None:
            return self.release_slot(slot_id)
        return False
    
    def get_slot_info(self, slot_id: int) -> Optional[SlotInfo]:
        """Get information about a specific slot"""
        if slot_id < 0 or slot_id >= self.max_slots:
            return None
        return self.slots[slot_id]
    
    def get_all_slots(self) -> List[SlotInfo]:
        """Get information about all allocated slots"""
        return [slot for slot in self.slots.values() if slot is not None]
    
    def get_symbol_slot(self, symbol: str) -> Optional[int]:
        """Get slot_id for a symbol, or None if not allocated"""
        return self._find_slot_by_symbol(symbol)
    
    def get_stats(self) -> dict:
        """Get allocation statistics"""
        allocated_count = sum(1 for slot in self.slots.values() if slot is not None)
        return {
            **self.stats,
            "allocated_slots": allocated_count,
            "available_slots": self.max_slots - allocated_count
        }
    
    # ---- Internal Methods ----
    
    def _find_empty_slot(self) -> Optional[int]:
        """Find the first empty slot"""
        for slot_id, slot_info in self.slots.items():
            if slot_info is None:
                return slot_id
        return None
    
    def _find_slot_by_symbol(self, symbol: str) -> Optional[int]:
        """Find slot_id by symbol"""
        for slot_id, slot_info in self.slots.items():
            if slot_info is not None and slot_info.symbol == symbol:
                return slot_id
        return None
    
    def _find_replaceable_slot(self, new_priority: float, now: datetime) -> Optional[int]:
        """
        Find a slot that can be replaced.
        
        Criteria:
        1. Priority lower than new_priority
        2. Allocated for at least min_dwell_seconds
        
        Returns the slot with lowest priority that meets criteria.
        """
        candidates = []
        for slot_id, slot_info in self.slots.items():
            if slot_info is None:
                continue
            
            # Check priority
            if slot_info.priority_score >= new_priority:
                continue
            
            # Check min dwell time
            dwell_time = (now - slot_info.allocated_at).total_seconds()
            if dwell_time < self.min_dwell_seconds:
                continue
            
            candidates.append((slot_id, slot_info.priority_score))
        
        if not candidates:
            return None
        
        # Return slot with lowest priority
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]
    
    def _log_overflow(self, candidate: SlotCandidate, timestamp: datetime):
        """Log overflow candidate to JSONL ledger"""
        date_str = timestamp.strftime("%Y%m%d")
        ledger_file = self.overflow_ledger_dir / f"overflow_{date_str}.jsonl"
        
        record = {
            "timestamp": timestamp.isoformat(),
            "symbol": candidate.symbol,
            "trigger_type": candidate.trigger_type,
            "priority_score": candidate.priority_score,
            "detected_at": candidate.detected_at.isoformat(),
            "reason": "all_slots_occupied"
        }
        
        with open(ledger_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ---- CLI for Testing ----

def main():
    """CLI for testing SlotManager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Slot Manager Test CLI")
    parser.add_argument("--max-slots", type=int, default=41, help="Maximum slots (default: 41)")
    parser.add_argument("--min-dwell", type=int, default=120, help="Minimum dwell seconds (default: 120)")
    parser.add_argument("--test", action="store_true", help="Run test scenario")
    args = parser.parse_args()
    
    manager = SlotManager(
        max_slots=args.max_slots,
        min_dwell_seconds=args.min_dwell
    )
    
    if args.test:
        print(f"🧪 Testing SlotManager with {args.max_slots} slots")
        print()
        
        # Test 1: Allocate slots
        print("Test 1: Allocate 45 candidates (overflow expected at 42+)")
        candidates = []
        for i in range(45):
            candidate = SlotCandidate(
                symbol=f"SYM{i:03d}",
                trigger_type="volume_surge",
                priority_score=0.5 + (i % 10) * 0.05,  # 0.5 ~ 0.95
                detected_at=datetime.now(timezone.utc)
            )
            candidates.append(candidate)
            result = manager.assign_slot(candidate)
            
            if result.success:
                print(f"  ✅ Allocated {candidate.symbol} to slot {result.slot_id} (priority={candidate.priority_score:.2f})")
            else:
                print(f"  ⚠️ Overflow: {candidate.symbol} (priority={candidate.priority_score:.2f})")
        
        print()
        stats = manager.get_stats()
        print(f"📊 Stats: {stats}")
        print()
        
        # Test 2: High-priority replacement
        print("Test 2: High-priority candidate (should replace low-priority slot after dwell time)")
        high_priority_candidate = SlotCandidate(
            symbol="HIGH_PRIORITY",
            trigger_type="volatility_spike",
            priority_score=0.98,
            detected_at=datetime.now(timezone.utc)
        )
        
        # Fast-forward time by setting min_dwell to 0 for this test
        manager.min_dwell_seconds = 0
        result = manager.assign_slot(high_priority_candidate)
        
        if result.success:
            print(f"  ✅ High-priority allocated to slot {result.slot_id}")
            if result.replaced_symbol:
                print(f"     Replaced: {result.replaced_symbol}")
        else:
            print(f"  ❌ Failed to allocate high-priority candidate")
        
        print()
        stats = manager.get_stats()
        print(f"📊 Final Stats: {stats}")
    
    else:
        print(f"SlotManager initialized with {args.max_slots} slots")
        print(f"Run with --test to execute test scenario")


if __name__ == "__main__":
    main()
