# observer/log_rotation.py

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from .snapshot import utc_now_ms
from paths import observer_asset_dir

logger = logging.getLogger(__name__)


# ============================================================
# Rotation Configuration
# ============================================================

@dataclass(frozen=True)
class RotationConfig:
    """Configuration for time-based log rotation."""
    window_ms: int = 60_000  # Rotation window in milliseconds (default: 1 minute)
    enable_rotation: bool = True  # Enable/disable rotation
    base_filename: str = "observer"  # Base filename without extension


# ============================================================
# Time Window Utilities
# ============================================================

class TimeWindow:
    """Represents a time window for log rotation."""
    
    def __init__(self, window_ms: int, timestamp_ms: Optional[int] = None) -> None:
        """
        Initialize a time window.
        
        Args:
            window_ms: Window size in milliseconds
            timestamp_ms: Timestamp to calculate window for (defaults to current time)
        """
        self.window_ms = window_ms
        self.timestamp_ms = timestamp_ms or utc_now_ms()
        
        # Calculate window start time (floor to window boundary)
        self.start_ms = (self.timestamp_ms // window_ms) * window_ms
        self.end_ms = self.start_ms + window_ms
    
    def contains(self, timestamp_ms: int) -> bool:
        """Check if a timestamp falls within this window."""
        return self.start_ms <= timestamp_ms < self.end_ms
    
    def is_expired(self, timestamp_ms: int) -> bool:
        """Check if this window is expired for the given timestamp."""
        return timestamp_ms >= self.end_ms
    
    def get_next_window(self) -> TimeWindow:
        """Get the next time window."""
        return TimeWindow(self.window_ms, self.end_ms)
    
    def to_datetime(self) -> datetime:
        """Convert window start to datetime object."""
        return datetime.fromtimestamp(self.start_ms / 1000.0, tz=timezone.utc)
    
    def to_filename(self, base_filename: str) -> str:
        """
        Generate filename for this time window.
        
        Format: {base_filename}_YYYYMMDD_HHMM.jsonl
        
        Examples:
        - observer_20251209_1430.jsonl (minute-level rotation)
        - observer_20251209_1430.jsonl (5-minute rotation would still show start time)
        """
        dt = self.to_datetime()
        time_part = dt.strftime("%Y%m%d_%H%M")
        return f"{base_filename}_{time_part}.jsonl"


# ============================================================
# Rotation Manager
# ============================================================

class RotationManager:
    """
    Manages time-based log rotation for observer sinks.
    
    This manager:
    - Tracks current time window
    - Determines when rotation should occur
    - Generates appropriate filenames for each window
    - Ensures atomic file transitions
    """
    
    def __init__(self, config: RotationConfig) -> None:
        """Initialize rotation manager with configuration."""
        self._config = config
        self._current_window: Optional[TimeWindow] = None
        self._current_file_path: Optional[Path] = None
    
    def should_rotate(self, timestamp_ms: Optional[int] = None) -> bool:
        """
        Check if rotation should occur for the given timestamp.
        
        Args:
            timestamp_ms: Timestamp to check (defaults to current time)
            
        Returns:
            True if rotation should occur, False otherwise
        """
        if not self._config.enable_rotation:
            return False
        
        timestamp = timestamp_ms or utc_now_ms()
        current_window = TimeWindow(self._config.window_ms, timestamp)
        
        # If we haven't established a current window, or if the timestamp
        # is outside the current window, we need to rotate
        if self._current_window is None:
            return True
        
        return not self._current_window.contains(timestamp)
    
    def get_current_file_path(self, timestamp_ms: Optional[int] = None) -> Path:
        """
        Get the appropriate file path for the given timestamp.
        
        This method will update the current window if rotation is needed
        and return the correct file path.
        
        Args:
            timestamp_ms: Timestamp to get file path for (defaults to current time)
            
        Returns:
            Path object for the appropriate log file
        """
        timestamp = timestamp_ms or utc_now_ms()
        new_window = TimeWindow(self._config.window_ms, timestamp)
        
        # Check if we need to rotate
        if self._current_window is None or not self._current_window.contains(timestamp):
            self._current_window = new_window
            self._current_file_path = observer_asset_dir() / new_window.to_filename(self._config.base_filename)
            
            logger.info(
                "Log rotation triggered",
                extra={
                    "new_file": str(self._current_file_path),
                    "window_start_ms": new_window.start_ms,
                    "window_end_ms": new_window.end_ms,
                    "window_size_ms": self._config.window_ms,
                },
            )
        
        return self._current_file_path
    
    def get_rotation_stats(self) -> dict:
        """Get current rotation statistics for monitoring."""
        current_time_ms = utc_now_ms()
        
        if self._current_window is None:
            return {
                "rotation_enabled": self._config.enable_rotation,
                "window_ms": self._config.window_ms,
                "current_window": None,
                "time_until_rotation_ms": None,
            }
        
        time_until_rotation = self._current_window.end_ms - current_time_ms
        
        return {
            "rotation_enabled": self._config.enable_rotation,
            "window_ms": self._config.window_ms,
            "current_window_start_ms": self._current_window.start_ms,
            "current_window_end_ms": self._current_window.end_ms,
            "time_until_rotation_ms": max(0, time_until_rotation),
            "current_file": str(self._current_file_path) if self._current_file_path else None,
        }


# ============================================================
# Utility Functions
# ============================================================

def create_rotation_config(
    window_ms: int = 60_000,
    enable_rotation: bool = True,
    base_filename: str = "observer"
) -> RotationConfig:
    """
    Create a rotation configuration with sensible defaults.
    
    Args:
        window_ms: Rotation window in milliseconds (default: 1 minute)
        enable_rotation: Whether to enable rotation (default: True)
        base_filename: Base filename for log files (default: "observer")
        
    Returns:
        RotationConfig object
    """
    return RotationConfig(
        window_ms=window_ms,
        enable_rotation=enable_rotation,
        base_filename=base_filename,
    )


def validate_rotation_config(config: RotationConfig) -> None:
    """
    Validate rotation configuration parameters.
    
    Args:
        config: Rotation configuration to validate
        
    Raises:
        ValueError: If configuration is invalid
    """
    if config.window_ms <= 0:
        raise ValueError("window_ms must be positive")
    
    if config.window_ms < 1000:  # Less than 1 second
        logger.warning(
            "Very small rotation window may cause performance issues",
            extra={"window_ms": config.window_ms},
        )
    
    if not config.base_filename or not config.base_filename.strip():
        raise ValueError("base_filename must be a non-empty string")
    
    # Check for invalid characters in filename
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    if any(char in config.base_filename for char in invalid_chars):
        raise ValueError(f"base_filename contains invalid characters: {invalid_chars}")
