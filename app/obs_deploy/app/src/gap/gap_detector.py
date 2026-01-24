"""
Gap Detector - Data gap detection and gap-marker generation

Key Responsibilities:
- Detect Track A data gaps (>10 minutes expected interval)
- Detect Track B data gaps (>60 seconds since last update)
- Classify gap severity (Minor/Major/Critical)
- Generate gap-marker JSONL records
- Log gaps to system/gap_YYYYMMDD.jsonl
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path
from enum import Enum

from shared.timezone import ZoneInfo
from shared.time_helpers import TimeAwareMixin

try:
    from paths import system_log_dir
except ImportError:
    system_log_dir = None  # type: ignore

log = logging.getLogger("GapDetector")


class GapType(Enum):
    """Gap severity classification"""
    MINOR = "minor"      # 10~60 seconds
    MAJOR = "major"      # 60 seconds ~ 5 minutes
    CRITICAL = "critical"  # 5+ minutes


class TrackType(Enum):
    """Data track type"""
    TRACK_A = "track_a"  # REST polling, 10-minute interval
    TRACK_B = "track_b"  # WebSocket streaming, 2Hz


@dataclass
class GapEvent:
    """Gap detection event"""
    track_type: str  # "track_a" or "track_b"
    symbol: Optional[str]  # Symbol (for Track B), None for Track A
    gap_type: str  # "minor", "major", "critical"
    gap_duration_seconds: float
    last_update: datetime
    detected_at: datetime
    expected_interval_seconds: float
    
    def to_dict(self) -> dict:
        return {
            "track_type": self.track_type,
            "symbol": self.symbol,
            "gap_type": self.gap_type,
            "gap_duration_seconds": self.gap_duration_seconds,
            "last_update": self.last_update.isoformat(),
            "detected_at": self.detected_at.isoformat(),
            "expected_interval_seconds": self.expected_interval_seconds
        }


@dataclass
class GapDetectorConfig:
    tz_name: str = "Asia/Seoul"
    
    # Track A thresholds (REST polling)
    track_a_expected_interval_seconds: int = 600  # 10 minutes
    track_a_minor_threshold_seconds: int = 660    # 11 minutes (10m + 1m buffer)
    track_a_major_threshold_seconds: int = 900    # 15 minutes
    track_a_critical_threshold_seconds: int = 1800  # 30 minutes
    
    # Track B thresholds (WebSocket streaming)
    track_b_expected_interval_seconds: int = 2    # 2Hz = 0.5s per update (allow 2s max)
    track_b_minor_threshold_seconds: int = 10     # 10 seconds
    track_b_major_threshold_seconds: int = 60     # 60 seconds
    track_b_critical_threshold_seconds: int = 300  # 5 minutes
    
    # Gap log settings (resolved via paths.py or fallback)
    gap_ledger_dir: str = ""  # Empty = use system_log_dir() from paths.py


class GapDetector(TimeAwareMixin):
    """
    Detects data gaps for Track A and Track B collectors.
    
    Features:
    - Track A gap detection (10-minute polling)
    - Track B gap detection (per-symbol WebSocket streaming)
    - Gap severity classification (Minor/Major/Critical)
    - Gap-marker generation and logging
    """
    
    def __init__(self, config: Optional[GapDetectorConfig] = None) -> None:
        self.cfg = config or GapDetectorConfig()
        self._tz_name = self.cfg.tz_name
        self._init_timezone()

        # Track last update timestamps
        self._track_a_last_update: Optional[datetime] = None
        self._track_b_last_updates: Dict[str, datetime] = {}  # symbol -> timestamp
        
        # Ensure gap ledger directory exists
        if self.cfg.gap_ledger_dir:
            self.gap_ledger_dir = Path(self.cfg.gap_ledger_dir)
        elif system_log_dir is not None:
            self.gap_ledger_dir = system_log_dir()
        else:
            # Fallback: relative to current file
            self.gap_ledger_dir = Path(__file__).resolve().parents[4] / "logs" / "system"
        self.gap_ledger_dir.mkdir(parents=True, exist_ok=True)
        
    # -----------------------------------------------------
    # Track A Gap Detection
    # -----------------------------------------------------
    def update_track_a(self, timestamp: Optional[datetime] = None) -> None:
        """
        Update Track A last update timestamp.
        
        Call this every time Track A successfully collects data.
        """
        if timestamp is None:
            timestamp = self._now()
        self._track_a_last_update = timestamp
        log.debug(f"Track A updated: {timestamp.isoformat()}")
    
    def check_track_a_gap(self, current_time: Optional[datetime] = None) -> Optional[GapEvent]:
        """
        Check if Track A has a data gap.
        
        Returns:
            GapEvent if gap detected, None otherwise
        """
        if self._track_a_last_update is None:
            log.debug("Track A: No baseline update yet, cannot detect gap")
            return None
        
        if current_time is None:
            current_time = self._now()
        
        gap_duration = (current_time - self._track_a_last_update).total_seconds()
        
        # Check against thresholds
        if gap_duration < self.cfg.track_a_minor_threshold_seconds:
            return None
        
        # Classify gap severity
        if gap_duration >= self.cfg.track_a_critical_threshold_seconds:
            gap_type = GapType.CRITICAL
        elif gap_duration >= self.cfg.track_a_major_threshold_seconds:
            gap_type = GapType.MAJOR
        else:
            gap_type = GapType.MINOR
        
        gap_event = GapEvent(
            track_type=TrackType.TRACK_A.value,
            symbol=None,
            gap_type=gap_type.value,
            gap_duration_seconds=gap_duration,
            last_update=self._track_a_last_update,
            detected_at=current_time,
            expected_interval_seconds=self.cfg.track_a_expected_interval_seconds
        )
        
        log.warning(
            f"⚠️ Track A GAP DETECTED: {gap_type.value.upper()} "
            f"({gap_duration:.0f}s since last update)"
        )
        
        self._log_gap_event(gap_event)
        return gap_event
    
    # -----------------------------------------------------
    # Track B Gap Detection
    # -----------------------------------------------------
    def update_track_b(self, symbol: str, timestamp: Optional[datetime] = None) -> None:
        """
        Update Track B last update timestamp for a symbol.
        
        Call this every time Track B receives data for a symbol.
        """
        if timestamp is None:
            timestamp = self._now()
        self._track_b_last_updates[symbol] = timestamp
        log.debug(f"Track B updated: {symbol} at {timestamp.isoformat()}")
    
    def check_track_b_gap(
        self, 
        symbol: str, 
        current_time: Optional[datetime] = None
    ) -> Optional[GapEvent]:
        """
        Check if a specific symbol has a data gap in Track B.
        
        Args:
            symbol: Symbol to check
            current_time: Current timestamp (default: now)
        
        Returns:
            GapEvent if gap detected, None otherwise
        """
        if symbol not in self._track_b_last_updates:
            log.debug(f"Track B: No baseline update for {symbol}, cannot detect gap")
            return None
        
        if current_time is None:
            current_time = self._now()
        
        last_update = self._track_b_last_updates[symbol]
        gap_duration = (current_time - last_update).total_seconds()
        
        # Check against thresholds
        if gap_duration < self.cfg.track_b_minor_threshold_seconds:
            return None
        
        # Classify gap severity
        if gap_duration >= self.cfg.track_b_critical_threshold_seconds:
            gap_type = GapType.CRITICAL
        elif gap_duration >= self.cfg.track_b_major_threshold_seconds:
            gap_type = GapType.MAJOR
        else:
            gap_type = GapType.MINOR
        
        gap_event = GapEvent(
            track_type=TrackType.TRACK_B.value,
            symbol=symbol,
            gap_type=gap_type.value,
            gap_duration_seconds=gap_duration,
            last_update=last_update,
            detected_at=current_time,
            expected_interval_seconds=self.cfg.track_b_expected_interval_seconds
        )
        
        log.warning(
            f"⚠️ Track B GAP DETECTED: {symbol} - {gap_type.value.upper()} "
            f"({gap_duration:.0f}s since last update)"
        )
        
        self._log_gap_event(gap_event)
        return gap_event
    
    def check_all_track_b_gaps(
        self, 
        current_time: Optional[datetime] = None
    ) -> List[GapEvent]:
        """
        Check all Track B symbols for gaps.
        
        Returns:
            List of GapEvent for all symbols with gaps
        """
        gaps = []
        for symbol in list(self._track_b_last_updates.keys()):
            gap = self.check_track_b_gap(symbol, current_time)
            if gap:
                gaps.append(gap)
        return gaps
    
    # -----------------------------------------------------
    # Gap Logging
    # -----------------------------------------------------
    def _log_gap_event(self, gap_event: GapEvent) -> None:
        """
        Log gap event to gap ledger JSONL file.
        
        File: logs/system/gap_YYYYMMDD.jsonl
        """
        try:
            date_str = gap_event.detected_at.strftime("%Y%m%d")
            ledger_file = self.gap_ledger_dir / f"gap_{date_str}.jsonl"
            
            # Write to file
            with open(ledger_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(gap_event.to_dict(), ensure_ascii=False) + "\n")
        
        except Exception as e:
            log.error(f"Failed to log gap event: {e}", exc_info=True)

    # -----------------------------------------------------
    # Utilities
    # -----------------------------------------------------
    
    def get_status(self) -> Dict[str, Any]:
        """Get detector status"""
        now = self._now()
        
        track_a_gap = None
        if self._track_a_last_update:
            track_a_gap = (now - self._track_a_last_update).total_seconds()
        
        track_b_symbols = len(self._track_b_last_updates)
        track_b_gaps = {}
        for symbol, last_update in self._track_b_last_updates.items():
            gap = (now - last_update).total_seconds()
            if gap >= self.cfg.track_b_minor_threshold_seconds:
                track_b_gaps[symbol] = gap
        
        return {
            "track_a_last_update": (
                self._track_a_last_update.isoformat() 
                if self._track_a_last_update else None
            ),
            "track_a_gap_seconds": track_a_gap,
            "track_b_monitored_symbols": track_b_symbols,
            "track_b_symbols_with_gaps": len(track_b_gaps),
            "track_b_gaps": track_b_gaps
        }


# ---- CLI for Testing ----

def main():
    """CLI for testing GapDetector"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Gap Detector Test CLI")
    parser.add_argument("--test", action="store_true", help="Run test scenario")
    args = parser.parse_args()
    
    detector = GapDetector()
    
    if args.test:
        print("🧪 Testing GapDetector")
        print()
        
        # Test 1: Track A gap detection
        print("Test 1: Track A gap detection")
        print("-" * 50)
        
        # Simulate Track A update
        now = detector._now()
        detector.update_track_a(now)
        print(f"✅ Track A updated at {now.isoformat()}")
        
        # Check immediately (no gap expected)
        gap = detector.check_track_a_gap(now)
        assert gap is None, "No gap should be detected immediately"
        print("✅ No gap detected immediately after update")
        
        # Simulate 12-minute gap (MINOR)
        future_time = now + timedelta(minutes=12)
        gap = detector.check_track_a_gap(future_time)
        assert gap is not None, "Gap should be detected after 12 minutes"
        assert gap.gap_type == GapType.MINOR.value, "Should be MINOR gap"
        print(f"✅ MINOR gap detected: {gap.gap_duration_seconds:.0f}s")
        
        # Simulate 20-minute gap (MAJOR)
        future_time = now + timedelta(minutes=20)
        gap = detector.check_track_a_gap(future_time)
        assert gap is not None, "Gap should be detected after 20 minutes"
        assert gap.gap_type == GapType.MAJOR.value, "Should be MAJOR gap"
        print(f"✅ MAJOR gap detected: {gap.gap_duration_seconds:.0f}s")
        
        # Simulate 35-minute gap (CRITICAL)
        future_time = now + timedelta(minutes=35)
        gap = detector.check_track_a_gap(future_time)
        assert gap is not None, "Gap should be detected after 35 minutes"
        assert gap.gap_type == GapType.CRITICAL.value, "Should be CRITICAL gap"
        print(f"✅ CRITICAL gap detected: {gap.gap_duration_seconds:.0f}s")
        
        print()
        
        # Test 2: Track B gap detection
        print("Test 2: Track B gap detection")
        print("-" * 50)
        
        # Simulate Track B updates
        detector.update_track_b("005930", now)
        detector.update_track_b("000660", now)
        print(f"✅ Track B updated for 2 symbols")
        
        # Check immediately (no gap expected)
        gap = detector.check_track_b_gap("005930", now)
        assert gap is None, "No gap should be detected immediately"
        print("✅ No gap detected immediately after update")
        
        # Simulate 15-second gap (MINOR)
        future_time = now + timedelta(seconds=15)
        gap = detector.check_track_b_gap("005930", future_time)
        assert gap is not None, "Gap should be detected after 15 seconds"
        assert gap.gap_type == GapType.MINOR.value, "Should be MINOR gap"
        print(f"✅ MINOR gap detected: {gap.gap_duration_seconds:.0f}s")
        
        # Simulate 90-second gap (MAJOR)
        future_time = now + timedelta(seconds=90)
        gap = detector.check_track_b_gap("005930", future_time)
        assert gap is not None, "Gap should be detected after 90 seconds"
        assert gap.gap_type == GapType.MAJOR.value, "Should be MAJOR gap"
        print(f"✅ MAJOR gap detected: {gap.gap_duration_seconds:.0f}s")
        
        # Simulate 6-minute gap (CRITICAL)
        future_time = now + timedelta(minutes=6)
        gap = detector.check_track_b_gap("005930", future_time)
        assert gap is not None, "Gap should be detected after 6 minutes"
        assert gap.gap_type == GapType.CRITICAL.value, "Should be CRITICAL gap"
        print(f"✅ CRITICAL gap detected: {gap.gap_duration_seconds:.0f}s")
        
        print()
        
        # Test 3: Check all Track B gaps
        print("Test 3: Check all Track B gaps")
        print("-" * 50)
        gaps = detector.check_all_track_b_gaps(future_time)
        print(f"✅ Found {len(gaps)} gaps across all symbols")
        
        print()
        
        # Show status
        status = detector.get_status()
        print("📊 Final Status:")
        print(json.dumps(status, indent=2, ensure_ascii=False))
    
    else:
        print("GapDetector initialized")
        print("Run with --test to execute test scenario")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    main()
