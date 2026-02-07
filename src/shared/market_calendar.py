"""
market_calendar.py

KRX (Korea Exchange) Market Calendar Manager.

Responsibilities:
- Fetch and cache market holidays from KIS API
- Check if a given date is a trading day
- Provide next/previous trading day utilities

Holiday data is refreshed monthly (1st of each month at 05:00 AM).
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional, Set
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

__all__ = [
    "MarketCalendar",
    "is_trading_day",
    "is_market_holiday",
    "get_next_trading_day",
    "get_previous_trading_day",
]

# Korean timezone
KST = ZoneInfo("Asia/Seoul")


class MarketCalendar:
    """
    KRX Market Calendar with holiday caching.
    
    Features:
    - Monthly holiday refresh from KIS API or pykrx
    - Local JSON cache for fast access
    - Fallback to weekday-only logic if API fails
    - Thread-safe singleton pattern
    """
    
    _instance: Optional["MarketCalendar"] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._holidays: Set[date] = set()
        self._cache_file: Optional[Path] = None
        self._last_refresh: Optional[datetime] = None
        self._initialized = True
        
        # Try to load from cache on init
        self._load_cache()
    
    def _get_cache_path(self) -> Path:
        """Get the cache file path."""
        if self._cache_file:
            return self._cache_file
        
        try:
            from observer.paths import config_dir
            cache_dir = config_dir() / "calendar"
        except ImportError:
            cache_dir = Path.home() / ".observer" / "calendar"
        
        cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_file = cache_dir / "krx_holidays.json"
        return self._cache_file
    
    def _load_cache(self) -> bool:
        """Load holidays from local cache."""
        try:
            cache_path = self._get_cache_path()
            if not cache_path.exists():
                logger.debug("No holiday cache file found")
                return False
            
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Parse cached data
            self._holidays = {
                date.fromisoformat(d) for d in data.get("holidays", [])
            }
            
            last_refresh_str = data.get("last_refresh")
            if last_refresh_str:
                self._last_refresh = datetime.fromisoformat(last_refresh_str)
            
            logger.info(f"[MarketCalendar] Loaded {len(self._holidays)} holidays from cache")
            return True
            
        except Exception as e:
            logger.warning(f"[MarketCalendar] Failed to load cache: {e}")
            return False
    
    def _save_cache(self) -> bool:
        """Save holidays to local cache."""
        try:
            cache_path = self._get_cache_path()
            
            data = {
                "holidays": sorted([d.isoformat() for d in self._holidays]),
                "last_refresh": datetime.now(KST).isoformat(),
                "count": len(self._holidays),
            }
            
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"[MarketCalendar] Saved {len(self._holidays)} holidays to cache")
            return True
            
        except Exception as e:
            logger.warning(f"[MarketCalendar] Failed to save cache: {e}")
            return False
    
    def needs_refresh(self) -> bool:
        """Check if holiday data needs to be refreshed (monthly)."""
        if not self._last_refresh:
            return True
        
        now = datetime.now(KST)
        
        # Refresh on the 1st of each month at 05:00 AM
        if now.day == 1 and now.hour >= 5:
            if self._last_refresh.month != now.month or self._last_refresh.year != now.year:
                return True
        
        # Also refresh if cache is older than 30 days
        age = now - self._last_refresh.replace(tzinfo=KST)
        if age.days >= 30:
            return True
        
        return False
    
    async def refresh_holidays(self, year: Optional[int] = None) -> bool:
        """
        Refresh holiday data from external sources.
        
        Sources tried in order:
        1. pykrx library (most reliable)
        2. KIS API (if credentials available)
        3. Static fallback (basic holidays)
        
        Args:
            year: Year to fetch holidays for (default: current and next year)
            
        Returns:
            True if refresh succeeded
        """
        async with self._lock:
            logger.info("[MarketCalendar] Refreshing holidays...")
            
            current_year = year or datetime.now(KST).year
            years_to_fetch = [current_year, current_year + 1]
            
            new_holidays: Set[date] = set()
            
            # Source 1: pykrx library
            pykrx_holidays = await self._fetch_from_pykrx(years_to_fetch)
            if pykrx_holidays:
                new_holidays.update(pykrx_holidays)
                logger.info(f"[MarketCalendar] Got {len(pykrx_holidays)} holidays from pykrx")
            
            # Source 2: KIS API (optional, requires auth)
            # kis_holidays = await self._fetch_from_kis_api(years_to_fetch)
            # if kis_holidays:
            #     new_holidays.update(kis_holidays)
            
            # Source 3: Static fallback (weekends + Korean holidays)
            if not new_holidays:
                logger.warning("[MarketCalendar] All sources failed, using weekday-only mode")
                return False
            
            self._holidays = new_holidays
            self._last_refresh = datetime.now(KST)
            self._save_cache()
            
            logger.info(f"[MarketCalendar] Refresh complete: {len(self._holidays)} holidays cached")
            return True
    
    async def _fetch_from_pykrx(self, years: List[int]) -> Set[date]:
        """Fetch holidays using pykrx library."""
        holidays: Set[date] = set()
        
        try:
            from pykrx import stock as pykrx_stock
            
            for year in years:
                # pykrx provides business day info - we can derive holidays
                # by checking which days are NOT trading days
                start_date = f"{year}0101"
                end_date = f"{year}1231"
                
                try:
                    # Get all trading days for the year
                    trading_days_df = pykrx_stock.get_market_ohlcv_by_date(
                        start_date, end_date, "005930"  # Use Samsung as reference
                    )
                    
                    if trading_days_df is not None and not trading_days_df.empty:
                        # Convert index to set of dates
                        trading_dates = {
                            d.date() if hasattr(d, 'date') else d 
                            for d in trading_days_df.index
                        }
                        
                        # Find non-trading weekdays (holidays)
                        current = date(year, 1, 1)
                        end = date(year, 12, 31)
                        
                        while current <= end:
                            # If it's a weekday but not a trading day, it's a holiday
                            if current.weekday() < 5 and current not in trading_dates:
                                holidays.add(current)
                            current += timedelta(days=1)
                        
                        logger.info(f"[MarketCalendar] pykrx: Found {len(holidays)} holidays for {year}")
                        
                except Exception as e:
                    logger.warning(f"[MarketCalendar] pykrx fetch failed for {year}: {e}")
                    
        except ImportError:
            logger.warning("[MarketCalendar] pykrx not installed, skipping")
        except Exception as e:
            logger.error(f"[MarketCalendar] pykrx error: {e}")
        
        return holidays
    
    def is_holiday(self, d: date) -> bool:
        """
        Check if the given date is a market holiday.
        
        Args:
            d: Date to check
            
        Returns:
            True if the date is a holiday (market closed)
        """
        # Weekends are always holidays
        if d.weekday() >= 5:  # Saturday=5, Sunday=6
            return True
        
        # Check against cached holidays
        return d in self._holidays
    
    def is_trading_day(self, d: date) -> bool:
        """
        Check if the given date is a trading day.
        
        Args:
            d: Date to check
            
        Returns:
            True if the market is open on this date
        """
        return not self.is_holiday(d)
    
    def get_next_trading_day(self, d: date) -> date:
        """
        Get the next trading day after the given date.
        
        Args:
            d: Reference date
            
        Returns:
            Next trading day
        """
        next_day = d + timedelta(days=1)
        while self.is_holiday(next_day):
            next_day += timedelta(days=1)
        return next_day
    
    def get_previous_trading_day(self, d: date) -> date:
        """
        Get the previous trading day before the given date.
        
        Args:
            d: Reference date
            
        Returns:
            Previous trading day
        """
        prev_day = d - timedelta(days=1)
        while self.is_holiday(prev_day):
            prev_day -= timedelta(days=1)
        return prev_day
    
    def get_holidays_in_range(self, start: date, end: date) -> List[date]:
        """Get all holidays in the given date range."""
        return sorted([
            d for d in self._holidays
            if start <= d <= end
        ])


# Module-level convenience functions
_calendar: Optional[MarketCalendar] = None


def _get_calendar() -> MarketCalendar:
    """Get or create the singleton calendar instance."""
    global _calendar
    if _calendar is None:
        _calendar = MarketCalendar()
    return _calendar


def is_trading_day(d: Optional[date] = None) -> bool:
    """
    Check if the given date (or today) is a trading day.
    
    Args:
        d: Date to check (default: today in KST)
        
    Returns:
        True if the market is open
    """
    if d is None:
        d = datetime.now(KST).date()
    return _get_calendar().is_trading_day(d)


def is_market_holiday(d: Optional[date] = None) -> bool:
    """
    Check if the given date (or today) is a market holiday.
    
    Args:
        d: Date to check (default: today in KST)
        
    Returns:
        True if the market is closed
    """
    if d is None:
        d = datetime.now(KST).date()
    return _get_calendar().is_holiday(d)


def get_next_trading_day(d: Optional[date] = None) -> date:
    """Get the next trading day after the given date (or today)."""
    if d is None:
        d = datetime.now(KST).date()
    return _get_calendar().get_next_trading_day(d)


def get_previous_trading_day(d: Optional[date] = None) -> date:
    """Get the previous trading day before the given date (or today)."""
    if d is None:
        d = datetime.now(KST).date()
    return _get_calendar().get_previous_trading_day(d)
