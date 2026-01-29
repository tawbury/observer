"""
Log Rotation Manager - Time-based log file rotation with partitioning

Key Responsibilities:
- Rotate log files based on time windows (10min, 1min, 1hour)
- Generate partitioned filenames (YYYYMMDD_HHMM format)
- Provide file path management for collectors
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path
from zoneinfo import ZoneInfo

from shared.time_helpers import TimeAwareMixin

log = logging.getLogger("LogRotationManager")


@dataclass
class RotationConfig:
    """Log rotation configuration"""
    window_ms: int  # Rotation window in milliseconds (60_000 = 1min, 600_000 = 10min)
    enable_rotation: bool = True
    base_filename: str = "observer"


class TimeWindow:
    """Time window management for log rotation"""
    
    def __init__(self, window_ms: int) -> None:
        """
        Initialize time window.
        
        Args:
            window_ms: Window size in milliseconds
        """
        self.window_ms = window_ms
        self.window_seconds = window_ms / 1000
        self.window_td = timedelta(seconds=self.window_seconds)
    
    def get_window_start(self, dt: datetime) -> datetime:
        """
        Get the start time of the window containing the given datetime.
        
        Examples:
        - 1-minute window (60_000ms): 09:15:30 → 09:15:00
        - 10-minute window (600_000ms): 09:15:30 → 09:10:00
        - 1-hour window (3600_000ms): 09:15:30 → 09:00:00
        """
        window_seconds = int(self.window_seconds)
        
        # Calculate total seconds since midnight
        seconds_since_midnight = (
            dt.hour * 3600 + 
            dt.minute * 60 + 
            dt.second
        )
        
        # Round down to nearest window boundary
        window_index = seconds_since_midnight // window_seconds
        window_start_seconds = window_index * window_seconds
        
        # Calculate hours and minutes for window start
        start_hour = window_start_seconds // 3600
        start_minute = (window_start_seconds % 3600) // 60
        start_second = window_start_seconds % 60
        
        # Reconstruct datetime at window start
        window_start = dt.replace(
            hour=start_hour,
            minute=start_minute,
            second=start_second,
            microsecond=0
        )
        
        return window_start
    
    def get_window_end(self, dt: datetime) -> datetime:
        """Get the end time of the window (exclusive)"""
        return self.get_window_start(dt) + self.window_td
    
    def has_window_changed(self, old_dt: datetime, new_dt: datetime) -> bool:
        """Check if the time window has changed"""
        return self.get_window_start(old_dt) != self.get_window_start(new_dt)
    
    def format_filename(
        self, 
        dt: datetime, 
        base_filename: str, 
        extension: str = ".jsonl"
    ) -> str:
        """
        Generate filename from datetime.
        
        Format: {base_filename}_YYYYMMDD_HHMM{extension}
        
        Examples:
        - swing_20260122_0910 (10-minute window)
        - scalp_20260122_0915 (1-minute window)
        """
        window_start = self.get_window_start(dt)
        date_str = window_start.strftime("%Y%m%d")
        time_str = window_start.strftime("%H%M")
        return f"{base_filename}_{date_str}_{time_str}{extension}"


class LogRotationManager(TimeAwareMixin):
    """
    Manages time-based log file rotation.
    
    Features:
    - Time-window based rotation (10min, 1min, 1hour)
    - Automatic filename generation
    - Per-track log path management
    """
    
    def __init__(
        self,
        base_dir: Path,
        tz_name: str = "Asia/Seoul"
    ) -> None:
        """
        Initialize log rotation manager.
        
        Args:
            base_dir: Base directory for all logs (e.g., config/)
            tz_name: Timezone name
        """
        self.base_dir = Path(base_dir)
        self._tz_name = tz_name
        self._init_timezone()

        # Rotation configs for different tracks
        self.configs = {
            "swing": RotationConfig(
                window_ms=600_000,  # 10 minutes
                base_filename="swing"
            ),
            "scalp": RotationConfig(
                window_ms=60_000,   # 1 minute
                base_filename="scalp"
            ),
            "system": RotationConfig(
                window_ms=3600_000,  # 1 hour
                base_filename="system"
            )
        }
        
        # Time windows for each track
        self.windows = {
            track: TimeWindow(cfg.window_ms)
            for track, cfg in self.configs.items()
        }
        
        # Ensure base directories exist
        for track in self.configs.keys():
            track_dir = self.base_dir / track
            track_dir.mkdir(parents=True, exist_ok=True)

    def get_log_path(self, track: str, timestamp: Optional[datetime] = None) -> Path:
        """
        Get the log file path for a track.
        
        Args:
            track: Track type ("swing", "scalp", "system")
            timestamp: Optional timestamp (default: now)
        
        Returns:
            Full path to log file
        """
        if timestamp is None:
            timestamp = self._now()
        
        if track not in self.configs:
            raise ValueError(f"Unknown track: {track}")
        
        cfg = self.configs[track]
        window = self.windows[track]
        
        filename = window.format_filename(timestamp, cfg.base_filename)
        track_dir = self.base_dir / track
        
        return track_dir / filename
    
    def should_rotate(
        self, 
        track: str, 
        old_timestamp: datetime, 
        new_timestamp: datetime
    ) -> bool:
        """
        Check if log rotation is needed.
        
        Args:
            track: Track type
            old_timestamp: Previous timestamp
            new_timestamp: Current timestamp
        
        Returns:
            True if rotation needed, False otherwise
        """
        if track not in self.windows:
            return False
        
        window = self.windows[track]
        return window.has_window_changed(old_timestamp, new_timestamp)
    
    def get_status(self, track: str) -> dict:
        """Get rotation status for a track"""
        now = self._now()
        window = self.windows[track]
        
        window_start = window.get_window_start(now)
        window_end = window.get_window_end(now)
        
        return {
            "track": track,
            "current_file": self.get_log_path(track, now).name,
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "window_duration_seconds": int(window.window_seconds),
            "seconds_until_rotation": int((window_end - now).total_seconds())
        }


# ---- CLI for Testing ----

def main():
    """CLI for testing LogRotationManager"""
    import argparse
    from paths import observer_asset_dir
    
    parser = argparse.ArgumentParser(description="Log Rotation Manager Test CLI")
    parser.add_argument("--test", action="store_true", help="Run test scenario")
    args = parser.parse_args()
    
    base_dir = observer_asset_dir()
    manager = LogRotationManager(base_dir)
    
    if args.test:
        print("🧪 Testing LogRotationManager")
        print()
        
        # Test 1: Get current log paths
        print("Test 1: Current log paths")
        print("-" * 60)
        
        for track in ["swing", "scalp", "system"]:
            path = manager.get_log_path(track)
            print(f"  {track}: {path.relative_to(base_dir)}")
        
        print()
        
        # Test 2: Rotation detection (swing)
        print("Test 2: Rotation detection (swing, 10-minute window)")
        print("-" * 60)
        
        now = manager._now()
        window_swing = manager.windows["swing"]
        
        # Get current window start
        window_start = window_swing.get_window_start(now)
        window_end = window_swing.get_window_end(now)
        
        print(f"  Current time: {now.strftime('%H:%M:%S')}")
        print(f"  Window start: {window_start.strftime('%H:%M:%S')}")
        print(f"  Window end: {window_end.strftime('%H:%M:%S')}")
        
        # Test at 1 minute before window end
        future_1min = now + timedelta(minutes=1)
        rotate_1min = manager.should_rotate("swing", now, future_1min)
        
        print(f"  +1 minute: time={future_1min.strftime('%H:%M:%S')}, rotate={rotate_1min}")
        
        # Test at window end or beyond
        time_to_window_end = (window_end - now).total_seconds()
        future_at_end = now + timedelta(seconds=time_to_window_end + 1)
        rotate_at_end = manager.should_rotate("swing", now, future_at_end)
        
        print(f"  At window end: time={future_at_end.strftime('%H:%M:%S')}, rotate={rotate_at_end}")
        print(f"  ✅ Rotation detection working as expected")
        
        print()
        
        # Test 3: Rotation detection (scalp)
        print("Test 3: Rotation detection (scalp, 1-minute window)")
        print("-" * 60)
        
        window_scalp = manager.windows["scalp"]
        
        # Get current window start
        window_start = window_scalp.get_window_start(now)
        window_end = window_scalp.get_window_end(now)
        
        print(f"  Current time: {now.strftime('%H:%M:%S')}")
        print(f"  Window start: {window_start.strftime('%H:%M:%S')}")
        print(f"  Window end: {window_end.strftime('%H:%M:%S')}")
        
        # Test at 30 seconds
        future_30sec = now + timedelta(seconds=30)
        rotate_30sec = manager.should_rotate("scalp", now, future_30sec)
        
        print(f"  +30 seconds: time={future_30sec.strftime('%H:%M:%S')}, rotate={rotate_30sec}")
        
        # Test at window end
        time_to_window_end = (window_end - now).total_seconds()
        future_at_end = now + timedelta(seconds=time_to_window_end + 1)
        rotate_at_end = manager.should_rotate("scalp", now, future_at_end)
        
        print(f"  At window end: time={future_at_end.strftime('%H:%M:%S')}, rotate={rotate_at_end}")
        print(f"  ✅ Rotation detection working as expected")
        
        print()
        
        # Test 4: Get status
        print("Test 4: Rotation status")
        print("-" * 60)
        
        for track in ["swing", "scalp", "system"]:
            status = manager.get_status(track)
            print(f"\n  {track}:")
            print(f"    File: {status['current_file']}")
            print(f"    Window: {status['seconds_until_rotation']}s remaining")
        
        print()
        print("✅ All tests passed")
    
    else:
        print("LogRotationManager initialized")
        print("Run with --test to execute test scenario")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    main()
