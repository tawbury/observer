"""
Time helper utilities and mixins for timezone-aware datetime operations.

This module provides reusable components for handling time operations
consistently across the codebase.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .timezone import get_zoneinfo


__all__ = ["TimeAwareMixin", "now_with_timezone"]


class TimeAwareMixin:
    """
    Mixin class providing timezone-aware time helpers.

    Classes using this mixin should set `_tz_name` attribute
    to enable timezone-aware datetime operations.

    Attributes:
        _tz_name: Optional timezone name (e.g., "Asia/Seoul")
        _tz: Cached ZoneInfo object (set automatically)

    Example:
        >>> class MyCollector(TimeAwareMixin):
        ...     def __init__(self):
        ...         self._tz_name = "Asia/Seoul"
        ...         self._init_timezone()
        ...
        ...     def collect(self):
        ...         current_time = self._now()
    """

    _tz_name: Optional[str] = None
    _tz: Optional[object] = None  # ZoneInfo or None

    def _init_timezone(self) -> None:
        """
        Initialize timezone from _tz_name.
        Call this in __init__ after setting _tz_name.
        """
        if self._tz_name:
            self._tz = get_zoneinfo(self._tz_name)
        else:
            self._tz = None

    def _now(self) -> datetime:
        """
        Get current datetime with configured timezone.

        Returns:
            Current datetime. If timezone is configured and available,
            returns timezone-aware datetime. Otherwise returns UTC.
        """
        if self._tz:
            return datetime.now(self._tz)
        return datetime.now(timezone.utc)

    def _today(self) -> datetime:
        """
        Get today's date at midnight with configured timezone.

        Returns:
            Today's date at 00:00:00 with timezone info.
        """
        now = self._now()
        return now.replace(hour=0, minute=0, second=0, microsecond=0)


def now_with_timezone(tz_name: Optional[str] = None) -> datetime:
    """
    Standalone function to get current datetime with timezone.

    Use this when you don't need the mixin pattern.

    Args:
        tz_name: Optional timezone name

    Returns:
        Current datetime with timezone
    """
    if tz_name:
        tz = get_zoneinfo(tz_name)
        if tz:
            return datetime.now(tz)
    return datetime.now(timezone.utc)
