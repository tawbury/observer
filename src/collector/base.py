"""
Base collector class for data collection components.

Provides common functionality for Track A and Track B collectors.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, time
from typing import Any, Callable, Dict, Optional

from shared.time_helpers import TimeAwareMixin
from shared.trading_hours import in_trading_hours


__all__ = ["BaseCollector", "CollectorConfig"]

log = logging.getLogger("BaseCollector")


@dataclass
class CollectorConfig:
    """Base configuration for collectors."""
    tz_name: str = "Asia/Seoul"
    trading_start: time = time(9, 0)
    trading_end: time = time(15, 30)
    market: str = "kr_stocks"


class BaseCollector(TimeAwareMixin, ABC):
    """
    Abstract base class for data collectors.

    Provides common functionality:
    - Timezone-aware time operations (_now() from TimeAwareMixin)
    - Trading hours checking
    - Error handling
    - Async start/stop lifecycle

    Subclasses must implement:
    - collect_once(): Single collection iteration
    """

    def __init__(
        self,
        config: CollectorConfig,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        Initialize base collector.

        Args:
            config: Collector configuration
            on_error: Optional error callback
        """
        self.cfg = config
        self._tz_name = config.tz_name
        self._init_timezone()
        self._on_error = on_error
        self._running = False

        log.info("%s initialized: tz=%s, trading_hours=%s-%s, market=%s",
                 self.__class__.__name__, config.tz_name, config.trading_start, config.trading_end, config.market)

    def is_in_trading_hours(self, dt: Optional[datetime] = None) -> bool:
        """
        Check if current or given datetime is within trading hours.

        Args:
            dt: Datetime to check (default: now)

        Returns:
            True if within trading hours
        """
        if dt is None:
            dt = self._now()
        return in_trading_hours(dt, self.cfg.trading_start, self.cfg.trading_end)

    def handle_error(self, error: Exception, context: str = "") -> None:
        """
        Handle error with optional callback.

        Args:
            error: Exception that occurred
            context: Context description
        """
        error_msg = f"{context}: {error}" if context else str(error)
        log.error(error_msg)
        if self._on_error:
            try:
                self._on_error(error_msg)
            except Exception as callback_error:
                log.error("Error callback failed while handling '%s': %s (callback_type=%s)",
                          error_msg[:100], callback_error, type(self._on_error).__name__)

    @abstractmethod
    async def collect_once(self) -> Dict[str, Any]:
        """
        Perform a single collection iteration.

        Returns:
            Dictionary with collection results

        Raises:
            Exception: On collection failure
        """
        pass

    @abstractmethod
    async def start(self) -> None:
        """
        Start the collector.

        Should set self._running = True and run collection loop.
        """
        pass

    async def stop(self) -> None:
        """Stop the collector."""
        self._running = False
        log.info(f"{self.__class__.__name__} stopped")
