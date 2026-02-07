"""
Trading hours utilities for Korean stock market.

This module provides functions to check trading hours and market sessions
for the Korean stock market (KRX).
"""
from __future__ import annotations

from datetime import datetime, time, date
from typing import NamedTuple, Optional


__all__ = [
    "in_trading_hours",
    "TradingSession",
    "KRX_REGULAR_SESSION",
    "KRX_PRE_MARKET",
    "KRX_AFTER_HOURS",
    "is_regular_trading_hours",
    "is_market_open",
    "is_market_open_today",
    "get_current_session",
]


class TradingSession(NamedTuple):
    """Trading session definition with start and end times."""
    name: str
    start: time
    end: time

    def contains(self, dt: datetime) -> bool:
        """Check if datetime is within this trading session."""
        t = dt.time()
        return self.start <= t <= self.end


# Korean Stock Exchange (KRX) trading sessions
KRX_PRE_MARKET = TradingSession(
    name="pre_market",
    start=time(8, 30),
    end=time(8, 59),
)

KRX_REGULAR_SESSION = TradingSession(
    name="regular",
    start=time(9, 0),
    end=time(15, 30),
)

KRX_AFTER_HOURS = TradingSession(
    name="after_hours",
    start=time(15, 40),
    end=time(18, 0),
)


def in_trading_hours(
    dt: datetime,
    start: time,
    end: time,
) -> bool:
    """
    Check if datetime is within the specified trading hours.

    Args:
        dt: Datetime to check
        start: Trading start time
        end: Trading end time

    Returns:
        True if dt is within [start, end], False otherwise
    """
    t = dt.time()
    return start <= t <= end


def is_regular_trading_hours(dt: datetime) -> bool:
    """
    Check if datetime is within KRX regular trading hours (09:00-15:30).

    Args:
        dt: Datetime to check

    Returns:
        True if within regular trading hours
    """
    return KRX_REGULAR_SESSION.contains(dt)


def is_market_open(dt: datetime) -> bool:
    """
    Check if datetime is within any KRX trading session.

    Includes pre-market, regular, and after-hours sessions.
    NOTE: This only checks TIME, not whether the date is a holiday.
    Use is_market_open_today() for full holiday-aware check.

    Args:
        dt: Datetime to check

    Returns:
        True if market is open in any session
    """
    return (
        KRX_PRE_MARKET.contains(dt) or
        KRX_REGULAR_SESSION.contains(dt) or
        KRX_AFTER_HOURS.contains(dt)
    )


def is_market_open_today(dt: Optional[datetime] = None) -> bool:
    """
    Check if the market is currently open (holiday-aware).
    
    This function checks:
    1. Whether today is a trading day (not weekend/holiday)
    2. Whether current time is within trading hours
    
    Args:
        dt: Datetime to check (default: now in KST)
        
    Returns:
        True if market is open right now
    """
    from zoneinfo import ZoneInfo
    
    if dt is None:
        dt = datetime.now(ZoneInfo("Asia/Seoul"))
    
    # Check if today is a trading day
    try:
        from shared.market_calendar import is_trading_day
        if not is_trading_day(dt.date()):
            return False
    except ImportError:
        # Fallback: just check weekday
        if dt.weekday() >= 5:  # Saturday=5, Sunday=6
            return False
    
    # Check trading hours
    return is_market_open(dt)


def get_current_session(dt: datetime) -> Optional[TradingSession]:
    """
    Get the current trading session for the given datetime.

    Args:
        dt: Datetime to check

    Returns:
        TradingSession if within a session, None otherwise
    """
    for session in [KRX_PRE_MARKET, KRX_REGULAR_SESSION, KRX_AFTER_HOURS]:
        if session.contains(dt):
            return session
    return None

