"""
Timezone utilities with ZoneInfo compatibility.

This module provides a unified interface for timezone handling,
with fallback support for environments where zoneinfo is unavailable.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

# ZoneInfo compatibility wrapper
try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore

if TYPE_CHECKING:
    from zoneinfo import ZoneInfo as ZoneInfoType


__all__ = ["ZoneInfo", "get_zoneinfo", "now_with_tz", "is_zoneinfo_available"]


def is_zoneinfo_available() -> bool:
    """Check if ZoneInfo is available in the current environment."""
    return ZoneInfo is not None


def get_zoneinfo(tz_name: str) -> Optional["ZoneInfoType"]:
    """
    Get a ZoneInfo object for the given timezone name.

    Args:
        tz_name: Timezone name (e.g., "Asia/Seoul", "UTC")

    Returns:
        ZoneInfo object if available, None otherwise
    """
    if ZoneInfo is None:
        return None
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return None


def now_with_tz(tz_name: Optional[str] = None) -> datetime:
    """
    Get current datetime with optional timezone.

    Args:
        tz_name: Optional timezone name. If None or ZoneInfo unavailable,
                 returns UTC datetime.

    Returns:
        Current datetime with timezone info
    """
    if tz_name and ZoneInfo is not None:
        try:
            return datetime.now(ZoneInfo(tz_name))
        except Exception:
            pass
    return datetime.now(timezone.utc)
