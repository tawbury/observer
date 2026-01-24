# TASK-3.1: BaseCollector 추상 클래스 생성

## 태스크 정보
- **Phase**: 3 - 베이스 클래스 추출
- **우선순위**: High
- **의존성**: TASK-1.1, TASK-1.2, TASK-1.3, TASK-2.3
- **상태**: 대기

---

## 목표
TrackACollector와 TrackBCollector의 공통 코드를 BaseCollector 추상 클래스로 추출하여 코드 중복을 제거하고 일관성을 향상시킵니다.

---

## 현재 문제

### 중복 코드 패턴

두 Collector 클래스에서 다음 패턴이 중복됩니다:

| 패턴 | TrackACollector | TrackBCollector |
|------|-----------------|-----------------|
| `_now()` 메서드 | 라인 ~63 | 라인 ~95 |
| `_in_trading_hours()` 메서드 | 라인 68-70 | 라인 100-102 |
| Timezone 초기화 | `__init__` | `__init__` |
| Error callback 처리 | `_on_error` | `_on_error` |
| Async start() 루프 | `start()` | `start()` |
| 로그 경로 처리 | `observer_asset_dir()` | `observer_asset_dir()` |
| Trading hours 설정 | `cfg.trading_start/end` | `cfg.trading_start/end` |

### 영향 파일 (2개)

| # | 파일 경로 | 크기 |
|---|----------|------|
| 1 | `app/obs_deploy/app/src/collector/track_a_collector.py` | ~300줄 |
| 2 | `app/obs_deploy/app/src/collector/track_b_collector.py` | ~400줄 |

---

## 구현 계획

### 1. BaseCollector 추상 클래스 생성

**파일**: `app/obs_deploy/app/src/collector/base.py`

```python
"""
Base collector class for market data collection.

Provides common functionality shared by TrackACollector and TrackBCollector.
"""
from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from shared.time_helpers import TimeAwareMixin
from shared.trading_hours import in_trading_hours
from paths import observer_asset_dir


__all__ = ["BaseCollector", "BaseCollectorConfig"]

logger = logging.getLogger(__name__)


@dataclass
class BaseCollectorConfig:
    """
    Base configuration for collectors.

    Subclasses should extend this with specific configuration options.
    """
    tz_name: str = "Asia/Seoul"
    trading_start: time = time(9, 0)
    trading_end: time = time(15, 30)
    market: str = "kr_stocks"


class BaseCollector(ABC, TimeAwareMixin):
    """
    Abstract base class for market data collectors.

    Provides common functionality:
    - Timezone-aware time handling (via TimeAwareMixin)
    - Trading hours checking
    - Error callback handling
    - Async lifecycle management
    - Logging setup

    Subclasses must implement:
    - collect_once(): Single collection iteration
    - get_interval(): Time between collections
    """

    def __init__(
        self,
        config: BaseCollectorConfig,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize base collector.

        Args:
            config: Collector configuration
            on_error: Optional callback for error handling
        """
        self.cfg = config
        self._on_error = on_error
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Initialize timezone from TimeAwareMixin
        self._tz_name = config.tz_name
        self._init_timezone()

        # Setup logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup collector-specific logging."""
        self._log_dir = observer_asset_dir() / "logs"
        self._log_dir.mkdir(parents=True, exist_ok=True)

    def _in_trading_hours(self, dt: Optional[datetime] = None) -> bool:
        """
        Check if current time (or given datetime) is within trading hours.

        Args:
            dt: Datetime to check (uses current time if not provided)

        Returns:
            True if within trading hours
        """
        check_time = dt or self._now()
        return in_trading_hours(
            check_time,
            self.cfg.trading_start,
            self.cfg.trading_end,
        )

    def _handle_error(self, error: Exception) -> None:
        """
        Handle an error by logging and calling error callback.

        Args:
            error: The exception that occurred
        """
        error_msg = f"{self.__class__.__name__} error: {error}"
        logger.error(error_msg)

        if self._on_error:
            try:
                self._on_error(str(error))
            except Exception as callback_error:
                logger.warning(f"Error callback failed: {callback_error}")

    @abstractmethod
    async def collect_once(self) -> Dict[str, Any]:
        """
        Perform a single collection iteration.

        Returns:
            Dictionary with collected data

        Raises:
            Exception: If collection fails
        """
        pass

    @abstractmethod
    def get_interval(self) -> float:
        """
        Get the interval between collections in seconds.

        Returns:
            Interval in seconds
        """
        pass

    async def start(self) -> None:
        """
        Start the collector's main loop.

        Runs collect_once() at intervals defined by get_interval().
        Handles errors gracefully and respects trading hours.
        """
        self._running = True
        logger.info(f"{self.__class__.__name__} started")

        while self._running:
            try:
                # Check trading hours
                if not self._in_trading_hours():
                    logger.debug(f"{self.__class__.__name__}: Outside trading hours")
                    await asyncio.sleep(60)  # Check every minute
                    continue

                # Perform collection
                await self.collect_once()

                # Wait for next interval
                await asyncio.sleep(self.get_interval())

            except asyncio.CancelledError:
                logger.info(f"{self.__class__.__name__} cancelled")
                break
            except Exception as e:
                self._handle_error(e)
                await asyncio.sleep(10)  # Wait before retry

        logger.info(f"{self.__class__.__name__} stopped")

    async def stop(self) -> None:
        """Stop the collector."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    @property
    def is_running(self) -> bool:
        """Check if collector is currently running."""
        return self._running

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(running={self._running})"
```

### 2. TrackACollector 리팩토링

**파일**: `app/obs_deploy/app/src/collector/track_a_collector.py`

```python
"""
Track A Collector - Periodic market data collection.

Collects market data at regular intervals (default: 10 minutes).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .base import BaseCollector, BaseCollectorConfig
from provider import ProviderEngine


__all__ = ["TrackACollector", "TrackAConfig"]

logger = logging.getLogger(__name__)


@dataclass
class TrackAConfig(BaseCollectorConfig):
    """Configuration for Track A collector."""
    interval_minutes: int = 10
    session_id: str = ""
    mode: str = "production"
    max_symbols: int = 100

    # Override defaults
    trading_start: time = time(9, 0)
    trading_end: time = time(15, 30)


class TrackACollector(BaseCollector):
    """
    Track A: Periodic batch data collection.

    Collects market data for all symbols in universe at regular intervals.
    Uses REST API for batch queries.
    """

    def __init__(
        self,
        cfg: TrackAConfig,
        engine: ProviderEngine,
        universe_manager=None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize Track A collector.

        Args:
            cfg: Track A configuration
            engine: Provider engine for market data
            universe_manager: Optional universe manager for symbol list
            on_error: Optional error callback
        """
        super().__init__(cfg, on_error)
        self.engine = engine
        self.universe_manager = universe_manager
        self._output_file: Optional[Path] = None

    def get_interval(self) -> float:
        """Get collection interval in seconds."""
        return self.cfg.interval_minutes * 60

    async def collect_once(self) -> Dict[str, Any]:
        """
        Perform a single collection iteration.

        Fetches current prices for all symbols and writes to output file.
        """
        symbols = self._get_symbols()
        if not symbols:
            logger.warning("No symbols to collect")
            return {"collected": 0}

        # Fetch data
        data = await self._fetch_data(symbols)

        # Write to file
        self._write_data(data)

        logger.info(f"Track A: Collected {len(data)} symbols")
        return {"collected": len(data), "symbols": list(data.keys())}

    def _get_symbols(self) -> List[str]:
        """Get list of symbols to collect."""
        if self.universe_manager:
            return self.universe_manager.get_symbols()[:self.cfg.max_symbols]
        return []

    async def _fetch_data(self, symbols: List[str]) -> Dict[str, Any]:
        """Fetch data for symbols."""
        result = {}
        for symbol in symbols:
            try:
                price = await self.engine.get_current_price(symbol)
                if price:
                    result[symbol] = price
            except Exception as e:
                logger.warning(f"Failed to fetch {symbol}: {e}")
        return result

    def _write_data(self, data: Dict[str, Any]) -> None:
        """Write collected data to JSONL file."""
        if not self._output_file:
            timestamp = self._now().strftime("%Y%m%d")
            self._output_file = self._log_dir / f"track_a_{timestamp}.jsonl"

        record = {
            "timestamp": self._now().isoformat(),
            "data": data,
        }

        with open(self._output_file, "a") as f:
            f.write(json.dumps(record) + "\n")
```

### 3. TrackBCollector 리팩토링

**파일**: `app/obs_deploy/app/src/collector/track_b_collector.py`

```python
"""
Track B Collector - Real-time WebSocket data collection.

Manages WebSocket connections for real-time market data streaming.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .base import BaseCollector, BaseCollectorConfig
from provider import ProviderEngine
from trigger.trigger_engine import TriggerEngine
from slot.slot_manager import SlotManager


__all__ = ["TrackBCollector", "TrackBConfig"]

logger = logging.getLogger(__name__)


@dataclass
class TrackBConfig(BaseCollectorConfig):
    """Configuration for Track B collector."""
    max_slots: int = 41
    min_dwell_seconds: int = 120  # 2 minutes minimum
    check_interval_seconds: int = 5

    # Override defaults
    trading_start: time = time(9, 0)
    trading_end: time = time(15, 30)


class TrackBCollector(BaseCollector):
    """
    Track B: Real-time WebSocket data collection.

    Manages WebSocket slots for streaming market data.
    Uses trigger engine for priority-based slot allocation.
    """

    def __init__(
        self,
        cfg: TrackBConfig,
        engine: ProviderEngine,
        trigger_engine: TriggerEngine,
        slot_manager: SlotManager,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize Track B collector.

        Args:
            cfg: Track B configuration
            engine: Provider engine for market data
            trigger_engine: Trigger engine for anomaly detection
            slot_manager: Slot manager for WebSocket allocation
            on_error: Optional error callback
        """
        super().__init__(cfg, on_error)
        self.engine = engine
        self.trigger_engine = trigger_engine
        self.slot_manager = slot_manager

    def get_interval(self) -> float:
        """Get check interval in seconds."""
        return self.cfg.check_interval_seconds

    async def collect_once(self) -> Dict[str, Any]:
        """
        Perform a single slot management iteration.

        Checks triggers and reallocates slots based on priority.
        """
        # Get current triggers
        triggers = self.trigger_engine.get_active_triggers()

        # Manage slots
        allocated = await self._manage_slots(triggers)

        logger.debug(f"Track B: {len(allocated)} active slots")
        return {"active_slots": len(allocated)}

    async def _manage_slots(self, triggers: List[Dict]) -> List[str]:
        """
        Manage WebSocket slot allocation.

        Args:
            triggers: List of active triggers with priorities

        Returns:
            List of currently allocated symbols
        """
        # Sort by priority
        sorted_triggers = sorted(
            triggers,
            key=lambda t: t.get("priority", 0),
            reverse=True,
        )

        # Get top symbols
        symbols = [t["symbol"] for t in sorted_triggers[:self.cfg.max_slots]]

        # Update slot allocation
        for symbol in symbols:
            if not self.slot_manager.has_slot(symbol):
                await self.slot_manager.allocate(symbol)

        return self.slot_manager.get_active_symbols()
```

### 4. __init__.py 업데이트

**파일**: `app/obs_deploy/app/src/collector/__init__.py`

```python
"""
Market data collectors.

Provides Track A (periodic batch) and Track B (real-time WebSocket)
data collection functionality.
"""
from .base import BaseCollector, BaseCollectorConfig
from .track_a_collector import TrackACollector, TrackAConfig
from .track_b_collector import TrackBCollector, TrackBConfig

__all__ = [
    "BaseCollector",
    "BaseCollectorConfig",
    "TrackACollector",
    "TrackAConfig",
    "TrackBCollector",
    "TrackBConfig",
]
```

---

## 검증 방법

### 1. 단위 테스트

```python
# tests/unit/collector/test_base.py
import pytest
import asyncio
from datetime import time
from unittest.mock import Mock, AsyncMock

from collector.base import BaseCollector, BaseCollectorConfig


class ConcreteCollector(BaseCollector):
    """Concrete implementation for testing."""

    def __init__(self, config, **kwargs):
        super().__init__(config, **kwargs)
        self.collect_count = 0

    async def collect_once(self):
        self.collect_count += 1
        return {"count": self.collect_count}

    def get_interval(self):
        return 0.1  # Fast for testing


class TestBaseCollector:
    def test_init(self):
        config = BaseCollectorConfig(tz_name="Asia/Seoul")
        collector = ConcreteCollector(config)
        assert collector._tz_name == "Asia/Seoul"
        assert not collector.is_running

    def test_in_trading_hours_within(self):
        config = BaseCollectorConfig(
            trading_start=time(9, 0),
            trading_end=time(15, 30),
        )
        collector = ConcreteCollector(config)
        # Test with mock time within hours
        # ...

    def test_error_callback(self):
        error_handler = Mock()
        config = BaseCollectorConfig()
        collector = ConcreteCollector(config, on_error=error_handler)

        collector._handle_error(Exception("test error"))
        error_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_stop(self):
        config = BaseCollectorConfig()
        collector = ConcreteCollector(config)

        # Start in background
        task = asyncio.create_task(collector.start())
        await asyncio.sleep(0.3)

        assert collector.is_running
        await collector.stop()
        assert not collector.is_running
```

### 2. 통합 테스트

```bash
# 기존 테스트 통과 확인
pytest app/obs_deploy/app/src/collector/ -v

# 상속 관계 확인
python -c "
from collector import TrackACollector, TrackBCollector, BaseCollector
print(f'TrackA inherits BaseCollector: {issubclass(TrackACollector, BaseCollector)}')
print(f'TrackB inherits BaseCollector: {issubclass(TrackBCollector, BaseCollector)}')
"
```

### 3. 코드 중복 확인

```bash
# _now 메서드가 base.py 외에 없어야 함
grep -rn "def _now" --include="*.py" app/obs_deploy/app/src/collector/

# _in_trading_hours 메서드가 base.py 외에 없어야 함
grep -rn "def _in_trading_hours" --include="*.py" app/obs_deploy/app/src/collector/
```

---

## 완료 조건

- [ ] `collector/base.py` 파일 생성됨
- [ ] `BaseCollector` 추상 클래스 구현됨
- [ ] `BaseCollectorConfig` dataclass 구현됨
- [ ] `TrackACollector`가 `BaseCollector` 상속
- [ ] `TrackBCollector`가 `BaseCollector` 상속
- [ ] 중복 `_now()` 메서드 제거됨
- [ ] 중복 `_in_trading_hours()` 메서드 제거됨
- [ ] `collector/__init__.py` 업데이트됨
- [ ] 단위 테스트 통과
- [ ] 기존 테스트 모두 통과

---

## 코드 중복 감소 예상

| 항목 | Before | After | 감소 |
|------|--------|-------|------|
| `_now()` 구현 | 2개 | 0개 (상속) | 100% |
| `_in_trading_hours()` 구현 | 2개 | 0개 (상속) | 100% |
| Timezone 초기화 | 2개 | 0개 (상속) | 100% |
| Error 처리 | 2개 | 0개 (상속) | 100% |
| 총 라인 수 | ~700줄 | ~550줄 | ~21% |

---

## 관련 태스크
- [TASK-1.1](../phase-1/TASK-1.1-timezone-utility.md): Timezone 유틸리티 (선행)
- [TASK-1.2](../phase-1/TASK-1.2-time-helper-mixin.md): Time Helper Mixin (선행)
- [TASK-1.3](../phase-1/TASK-1.3-trading-hours.md): Trading Hours 유틸리티 (선행)
- [TASK-3.2](TASK-3.2-base-executor.md): BaseExecutor (유사 패턴)
