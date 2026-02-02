# observer/tick_events.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional


TickEvent = Dict[str, Any]


class ITickEventProvider(ABC):
    """
    ITickEventProvider
    
    Purpose:
    - Provide tick events for supplemental snapshot generation
    - Tick events are supplemental to loop-based snapshots
    - No filtering or interpretation of tick events
    
    Rules:
    - Tick events trigger additional snapshots, never replace loop snapshots
    - No decision logic or strategy coupling
    - Tick events are pure data events
    """
    
    @abstractmethod
    def start(self) -> None:
        """Start listening for tick events."""
        raise NotImplementedError
    
    @abstractmethod
    def stop(self) -> None:
        """Stop listening for tick events."""
        raise NotImplementedError
    
    @abstractmethod
    def set_callback(self, callback: Callable[[TickEvent], None]) -> None:
        """Set callback function for tick events."""
        raise NotImplementedError
    
    def close(self) -> None:
        """Optional: close underlying resources."""
        return None


class MockTickEventProvider(ITickEventProvider):
    """
    MockTickEventProvider for testing hybrid trigger functionality.
    """
    
    def __init__(self, tick_interval_ms: float = 100.0) -> None:
        self._tick_interval_ms = tick_interval_ms
        self._callback: Optional[Callable[[TickEvent], None]] = None
        self._running = False
        self._tick_count = 0
    
    def start(self) -> None:
        """Start generating mock tick events."""
        self._running = True
    
    def stop(self) -> None:
        """Stop generating tick events."""
        self._running = False
    
    def set_callback(self, callback: Callable[[TickEvent], None]) -> None:
        """Set callback for tick events."""
        self._callback = callback
    
    def generate_tick(self) -> None:
        """Generate a single mock tick event (for testing)."""
        if not self._running or self._callback is None:
            return
        
        self._tick_count += 1
        
        tick_event: TickEvent = {
            "meta": {
                "source": "mock_tick",
                "tick_count": self._tick_count,
            },
            "instruments": [
                {
                    "symbol": "MOCK",
                    "price": {
                        "open": 100.0 + self._tick_count * 0.01,
                        "high": 100.5 + self._tick_count * 0.01,
                        "low": 99.5 + self._tick_count * 0.01,
                        "close": 100.0 + self._tick_count * 0.01,
                    },
                    "volume": 1000,
                    "timestamp": f"mock_tick_{self._tick_count}",
                }
            ],
        }
        
        self._callback(tick_event)
    
    def auto_generate_ticks(self, count: int, interval_ms: float = 50.0) -> None:
        """Generate multiple ticks with specified interval (for testing)."""
        import time
        
        for i in range(count):
            if not self._running:
                break
            self.generate_tick()
            if interval_ms > 0:
                time.sleep(interval_ms / 1000.0)
