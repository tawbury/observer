"""
Shared utilities for Observer system.

This package provides common utilities used across the codebase:
- timezone: Timezone handling with ZoneInfo compatibility
- time_helpers: Time-aware mixin classes
- trading_hours: Trading hours utilities for KRX
- market_calendar: Market holiday management for KRX
- serialization: Object serialization and fingerprinting
"""
from .timezone import ZoneInfo, get_zoneinfo, now_with_tz, is_zoneinfo_available
from .time_helpers import TimeAwareMixin, now_with_timezone
from .trading_hours import in_trading_hours, TradingSession, KRX_REGULAR_SESSION, is_market_open_today
from .serialization import safe_to_dict, fingerprint, order_hint_fingerprint
from .market_calendar import (
    MarketCalendar,
    is_trading_day,
    is_market_holiday,
    get_next_trading_day,
    get_previous_trading_day,
)

__all__ = [
    # timezone
    "ZoneInfo",
    "get_zoneinfo",
    "now_with_tz",
    "is_zoneinfo_available",
    # time_helpers
    "TimeAwareMixin",
    "now_with_timezone",
    # trading_hours
    "in_trading_hours",
    "TradingSession",
    "KRX_REGULAR_SESSION",
    "is_market_open_today",
    # market_calendar
    "MarketCalendar",
    "is_trading_day",
    "is_market_holiday",
    "get_next_trading_day",
    "get_previous_trading_day",
    # serialization
    "safe_to_dict",
    "fingerprint",
    "order_hint_fingerprint",
]
