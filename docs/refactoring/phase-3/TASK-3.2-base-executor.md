# TASK-3.2: BaseExecutor 추상 클래스 생성

## 태스크 정보
- **Phase**: 3 - 베이스 클래스 추출
- **우선순위**: High
- **의존성**: TASK-1.4 (Serialization 유틸리티)
- **상태**: 대기

---

## 목표
NoopExecutor, SimExecutor, VirtualExecutor의 공통 코드를 BaseExecutor 추상 클래스로 추출하여 코드 중복을 제거하고 일관성을 향상시킵니다.

---

## 현재 문제

### 중복 코드 패턴

세 Executor 클래스에서 다음 패턴이 중복됩니다:

| 패턴 | 파일들 |
|------|--------|
| `_safe_to_dict()` | sim_executor.py, virtual_executor.py |
| `_fingerprint()` | sim_executor.py, virtual_executor.py |
| Decision ID 추출 | 모든 executor |
| ExecutionResult 생성 | 모든 executor |
| 유효성 검사 로직 | 모든 executor |

### 영향 파일 (3개)

| # | 파일 경로 | 설명 |
|---|----------|------|
| 1 | `src/decision_pipeline/execution_stub/noop_executor.py` | 실행 없이 로깅만 |
| 2 | `src/decision_pipeline/execution_stub/sim_executor.py` | 시뮬레이션 실행 |
| 3 | `src/decision_pipeline/execution_stub/virtual_executor.py` | 가상 실행 |

---

## 구현 계획

### 1. BaseExecutor 추상 클래스 생성

**파일**: `app/obs_deploy/app/src/decision_pipeline/execution_stub/base_executor.py`

```python
"""
Base executor class for decision execution.

Provides common functionality shared by all executor implementations.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from shared.serialization import safe_to_dict, order_hint_fingerprint


__all__ = [
    "BaseExecutor",
    "ExecutionMode",
    "ExecutionStatus",
    "ExecutionResult",
    "IExecution",
]

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Execution mode for executors."""
    NOOP = "noop"
    SIMULATION = "simulation"
    VIRTUAL = "virtual"
    LIVE = "live"


class ExecutionStatus(Enum):
    """Status of execution result."""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    INVALID = "invalid"


@dataclass
class ExecutionResult:
    """
    Result of an execution attempt.

    Attributes:
        decision_id: ID of the decision being executed
        mode: Execution mode used
        status: Execution status
        fingerprint: Unique fingerprint of order/hint pair
        timestamp: When execution occurred
        audit: Additional audit information
        error: Error message if failed
    """
    decision_id: str
    mode: ExecutionMode
    status: ExecutionStatus
    fingerprint: str
    timestamp: str
    audit: Dict[str, Any]
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "decision_id": self.decision_id,
            "mode": self.mode.value,
            "status": self.status.value,
            "fingerprint": self.fingerprint,
            "timestamp": self.timestamp,
            "audit": self.audit,
            "error": self.error,
        }


class IExecution(ABC):
    """Interface for execution implementations."""

    @abstractmethod
    def execute(self, order: Any, hint: Any) -> ExecutionResult:
        """
        Execute an order with the given hint.

        Args:
            order: Order to execute
            hint: Execution hint/context

        Returns:
            ExecutionResult with status and details
        """
        pass


class BaseExecutor(IExecution, ABC):
    """
    Abstract base class for executors.

    Provides common functionality:
    - Decision ID extraction
    - Fingerprint generation
    - Result construction
    - Validation
    - Audit trail
    """

    def __init__(self, mode: ExecutionMode):
        """
        Initialize base executor.

        Args:
            mode: Execution mode for this executor
        """
        self._mode = mode
        self._execution_count = 0

    @property
    def mode(self) -> ExecutionMode:
        """Get execution mode."""
        return self._mode

    def execute(self, order: Any, hint: Any) -> ExecutionResult:
        """
        Execute an order with validation and audit trail.

        Template method that:
        1. Extracts decision ID
        2. Generates fingerprint
        3. Validates order
        4. Calls subclass implementation
        5. Creates result with audit

        Args:
            order: Order to execute
            hint: Execution hint/context

        Returns:
            ExecutionResult with full audit trail
        """
        self._execution_count += 1
        timestamp = datetime.now().isoformat()

        # Extract decision ID
        decision_id = self._get_decision_id(order)

        # Generate fingerprint
        fingerprint = order_hint_fingerprint(order, hint)

        # Validate order
        validation = self._validate_order(order)
        if not validation["valid"]:
            return self._create_result(
                decision_id=decision_id,
                status=ExecutionStatus.INVALID,
                fingerprint=fingerprint,
                timestamp=timestamp,
                audit={"validation": validation},
                error=validation.get("error"),
            )

        try:
            # Call subclass implementation
            result = self._do_execute(order, hint, decision_id, fingerprint)

            # Build audit
            audit = self._build_audit(order, hint, result)

            return self._create_result(
                decision_id=decision_id,
                status=ExecutionStatus.SUCCESS,
                fingerprint=fingerprint,
                timestamp=timestamp,
                audit=audit,
            )

        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return self._create_result(
                decision_id=decision_id,
                status=ExecutionStatus.FAILED,
                fingerprint=fingerprint,
                timestamp=timestamp,
                audit={"error_type": type(e).__name__},
                error=str(e),
            )

    @abstractmethod
    def _do_execute(
        self,
        order: Any,
        hint: Any,
        decision_id: str,
        fingerprint: str,
    ) -> Dict[str, Any]:
        """
        Perform the actual execution.

        Subclasses implement this to define execution behavior.

        Args:
            order: Order to execute
            hint: Execution hint
            decision_id: Extracted decision ID
            fingerprint: Order/hint fingerprint

        Returns:
            Dictionary with execution details
        """
        pass

    def _get_decision_id(self, order: Any) -> str:
        """
        Extract decision ID from order.

        Args:
            order: Order object

        Returns:
            Decision ID string or "UNKNOWN"
        """
        # Try common attribute names
        for attr in ["decision_id", "id", "order_id"]:
            value = getattr(order, attr, None)
            if value is not None:
                return str(value)

        # Try dictionary access
        if isinstance(order, dict):
            for key in ["decision_id", "id", "order_id"]:
                if key in order:
                    return str(order[key])

        return "UNKNOWN"

    def _validate_order(self, order: Any) -> Dict[str, Any]:
        """
        Validate an order before execution.

        Override in subclasses for specific validation.

        Args:
            order: Order to validate

        Returns:
            Dictionary with 'valid' bool and optional 'error'
        """
        # Check for required attributes
        if order is None:
            return {"valid": False, "error": "Order is None"}

        # Check for action
        action = getattr(order, "action", None)
        if action is None and isinstance(order, dict):
            action = order.get("action")

        if action is None:
            return {"valid": False, "error": "Missing action"}

        # Check for quantity
        qty = getattr(order, "qty", None) or getattr(order, "quantity", None)
        if qty is None and isinstance(order, dict):
            qty = order.get("qty") or order.get("quantity")

        if qty is None:
            return {"valid": False, "error": "Missing quantity"}

        if qty <= 0:
            return {"valid": False, "error": f"Invalid quantity: {qty}"}

        return {"valid": True}

    def _build_audit(
        self,
        order: Any,
        hint: Any,
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build audit trail for execution.

        Args:
            order: Executed order
            hint: Execution hint
            result: Execution result from _do_execute

        Returns:
            Complete audit dictionary
        """
        return {
            "order": safe_to_dict(order),
            "hint": safe_to_dict(hint),
            "result": result,
            "execution_count": self._execution_count,
        }

    def _create_result(
        self,
        decision_id: str,
        status: ExecutionStatus,
        fingerprint: str,
        timestamp: str,
        audit: Dict[str, Any],
        error: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Create an ExecutionResult.

        Args:
            decision_id: Decision ID
            status: Execution status
            fingerprint: Order/hint fingerprint
            timestamp: Execution timestamp
            audit: Audit trail
            error: Optional error message

        Returns:
            ExecutionResult instance
        """
        return ExecutionResult(
            decision_id=decision_id,
            mode=self._mode,
            status=status,
            fingerprint=fingerprint,
            timestamp=timestamp,
            audit=audit,
            error=error,
        )
```

### 2. NoopExecutor 리팩토링

**파일**: `app/obs_deploy/app/src/decision_pipeline/execution_stub/noop_executor.py`

```python
"""
No-operation executor for logging and testing.

Logs execution requests without performing any actual execution.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from .base_executor import BaseExecutor, ExecutionMode


__all__ = ["NoopExecutor"]

logger = logging.getLogger(__name__)


class NoopExecutor(BaseExecutor):
    """
    No-operation executor.

    Logs all execution requests without side effects.
    Useful for testing and dry-run scenarios.
    """

    def __init__(self):
        super().__init__(ExecutionMode.NOOP)

    def _do_execute(
        self,
        order: Any,
        hint: Any,
        decision_id: str,
        fingerprint: str,
    ) -> Dict[str, Any]:
        """Log execution without performing action."""
        logger.info(
            f"NOOP Execute: decision={decision_id}, "
            f"fingerprint={fingerprint}"
        )
        return {"action": "noop", "logged": True}
```

### 3. SimExecutor 리팩토링

**파일**: `app/obs_deploy/app/src/decision_pipeline/execution_stub/sim_executor.py`

```python
"""
Simulation executor for paper trading.

Simulates order execution without real market impact.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from .base_executor import BaseExecutor, ExecutionMode


__all__ = ["SimExecutor"]

logger = logging.getLogger(__name__)


class SimExecutor(BaseExecutor):
    """
    Simulation executor.

    Simulates order execution with realistic behavior
    but no real market impact.
    """

    def __init__(self):
        super().__init__(ExecutionMode.SIMULATION)
        self._simulated_orders: Dict[str, Dict] = {}

    def _do_execute(
        self,
        order: Any,
        hint: Any,
        decision_id: str,
        fingerprint: str,
    ) -> Dict[str, Any]:
        """Simulate order execution."""
        action = getattr(order, "action", "unknown")
        qty = getattr(order, "qty", 0) or getattr(order, "quantity", 0)
        symbol = getattr(order, "symbol", "UNKNOWN")

        # Record simulated order
        self._simulated_orders[fingerprint] = {
            "decision_id": decision_id,
            "action": action,
            "qty": qty,
            "symbol": symbol,
        }

        logger.info(
            f"SIM Execute: {action} {qty} {symbol}, "
            f"decision={decision_id}"
        )

        return {
            "action": "simulated",
            "simulated_action": action,
            "simulated_qty": qty,
            "simulated_symbol": symbol,
        }

    def get_simulated_orders(self) -> Dict[str, Dict]:
        """Get all simulated orders."""
        return self._simulated_orders.copy()

    def clear_simulated_orders(self) -> None:
        """Clear simulated order history."""
        self._simulated_orders.clear()
```

### 4. VirtualExecutor 리팩토링

**파일**: `app/obs_deploy/app/src/decision_pipeline/execution_stub/virtual_executor.py`

```python
"""
Virtual executor for backtesting.

Executes orders in a virtual environment with full state tracking.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .base_executor import BaseExecutor, ExecutionMode


__all__ = ["VirtualExecutor", "VirtualPosition"]

logger = logging.getLogger(__name__)


@dataclass
class VirtualPosition:
    """Represents a virtual position."""
    symbol: str
    quantity: int = 0
    avg_price: float = 0.0
    history: List[Dict] = field(default_factory=list)


class VirtualExecutor(BaseExecutor):
    """
    Virtual executor for backtesting.

    Maintains virtual positions and execution history
    for comprehensive backtesting scenarios.
    """

    def __init__(self, initial_cash: float = 1_000_000):
        super().__init__(ExecutionMode.VIRTUAL)
        self._cash = initial_cash
        self._positions: Dict[str, VirtualPosition] = {}

    def _do_execute(
        self,
        order: Any,
        hint: Any,
        decision_id: str,
        fingerprint: str,
    ) -> Dict[str, Any]:
        """Execute order in virtual environment."""
        action = getattr(order, "action", "unknown")
        qty = getattr(order, "qty", 0) or getattr(order, "quantity", 0)
        symbol = getattr(order, "symbol", "UNKNOWN")
        price = getattr(order, "price", 0) or getattr(hint, "price", 0)

        # Update virtual position
        position = self._get_or_create_position(symbol)

        if action.lower() == "buy":
            cost = qty * price
            if cost > self._cash:
                return {"action": "rejected", "reason": "insufficient_cash"}

            self._cash -= cost
            position.quantity += qty
            position.history.append({
                "action": "buy",
                "qty": qty,
                "price": price,
                "decision_id": decision_id,
            })

        elif action.lower() == "sell":
            if qty > position.quantity:
                return {"action": "rejected", "reason": "insufficient_position"}

            self._cash += qty * price
            position.quantity -= qty
            position.history.append({
                "action": "sell",
                "qty": qty,
                "price": price,
                "decision_id": decision_id,
            })

        logger.info(
            f"VIRTUAL Execute: {action} {qty} {symbol} @ {price}, "
            f"cash={self._cash:.2f}"
        )

        return {
            "action": "virtual_executed",
            "executed_action": action,
            "executed_qty": qty,
            "executed_price": price,
            "remaining_cash": self._cash,
            "position_qty": position.quantity,
        }

    def _get_or_create_position(self, symbol: str) -> VirtualPosition:
        """Get or create a virtual position."""
        if symbol not in self._positions:
            self._positions[symbol] = VirtualPosition(symbol=symbol)
        return self._positions[symbol]

    @property
    def cash(self) -> float:
        """Get current cash balance."""
        return self._cash

    def get_positions(self) -> Dict[str, VirtualPosition]:
        """Get all virtual positions."""
        return self._positions.copy()

    def reset(self, initial_cash: float = 1_000_000) -> None:
        """Reset virtual environment."""
        self._cash = initial_cash
        self._positions.clear()
        self._execution_count = 0
```

### 5. __init__.py 업데이트

**파일**: `app/obs_deploy/app/src/decision_pipeline/execution_stub/__init__.py`

```python
"""
Execution stubs for decision pipeline.

Provides various executor implementations for different scenarios:
- NoopExecutor: Logging only
- SimExecutor: Simulation/paper trading
- VirtualExecutor: Backtesting with state
"""
from .base_executor import (
    BaseExecutor,
    ExecutionMode,
    ExecutionStatus,
    ExecutionResult,
    IExecution,
)
from .noop_executor import NoopExecutor
from .sim_executor import SimExecutor
from .virtual_executor import VirtualExecutor, VirtualPosition

__all__ = [
    # Base
    "BaseExecutor",
    "ExecutionMode",
    "ExecutionStatus",
    "ExecutionResult",
    "IExecution",
    # Implementations
    "NoopExecutor",
    "SimExecutor",
    "VirtualExecutor",
    "VirtualPosition",
]
```

---

## 검증 방법

### 1. 단위 테스트

```python
# tests/unit/decision_pipeline/test_base_executor.py
import pytest
from dataclasses import dataclass

from decision_pipeline.execution_stub import (
    BaseExecutor,
    ExecutionMode,
    ExecutionStatus,
    NoopExecutor,
    SimExecutor,
    VirtualExecutor,
)


@dataclass
class MockOrder:
    decision_id: str
    action: str
    qty: int
    symbol: str
    price: float = 100.0


@dataclass
class MockHint:
    reason: str
    price: float = 100.0


class TestNoopExecutor:
    def test_execute(self):
        executor = NoopExecutor()
        order = MockOrder("D001", "buy", 100, "AAPL")
        hint = MockHint("test")

        result = executor.execute(order, hint)

        assert result.status == ExecutionStatus.SUCCESS
        assert result.mode == ExecutionMode.NOOP
        assert result.decision_id == "D001"

    def test_fingerprint_consistency(self):
        executor = NoopExecutor()
        order = MockOrder("D001", "buy", 100, "AAPL")
        hint = MockHint("test")

        result1 = executor.execute(order, hint)
        result2 = executor.execute(order, hint)

        assert result1.fingerprint == result2.fingerprint


class TestSimExecutor:
    def test_execute(self):
        executor = SimExecutor()
        order = MockOrder("D001", "buy", 100, "AAPL")
        hint = MockHint("test")

        result = executor.execute(order, hint)

        assert result.status == ExecutionStatus.SUCCESS
        assert result.mode == ExecutionMode.SIMULATION

    def test_simulated_orders_tracking(self):
        executor = SimExecutor()
        order = MockOrder("D001", "buy", 100, "AAPL")
        hint = MockHint("test")

        executor.execute(order, hint)

        orders = executor.get_simulated_orders()
        assert len(orders) == 1


class TestVirtualExecutor:
    def test_buy_execution(self):
        executor = VirtualExecutor(initial_cash=100_000)
        order = MockOrder("D001", "buy", 10, "AAPL", price=100)
        hint = MockHint("test", price=100)

        result = executor.execute(order, hint)

        assert result.status == ExecutionStatus.SUCCESS
        assert executor.cash == 99_000  # 100,000 - 10*100

    def test_sell_execution(self):
        executor = VirtualExecutor(initial_cash=100_000)

        # Buy first
        buy_order = MockOrder("D001", "buy", 10, "AAPL", price=100)
        executor.execute(buy_order, MockHint("buy", price=100))

        # Then sell
        sell_order = MockOrder("D002", "sell", 5, "AAPL", price=110)
        result = executor.execute(sell_order, MockHint("sell", price=110))

        assert result.status == ExecutionStatus.SUCCESS
        assert executor.cash == 99_550  # 99,000 + 5*110

    def test_insufficient_cash(self):
        executor = VirtualExecutor(initial_cash=1_000)
        order = MockOrder("D001", "buy", 100, "AAPL", price=100)
        hint = MockHint("test", price=100)

        result = executor.execute(order, hint)
        # Should still succeed but audit shows rejection
        assert "rejected" in str(result.audit)


class TestBaseExecutorValidation:
    def test_missing_action(self):
        executor = NoopExecutor()

        @dataclass
        class InvalidOrder:
            decision_id: str = "D001"
            qty: int = 100

        result = executor.execute(InvalidOrder(), MockHint("test"))
        assert result.status == ExecutionStatus.INVALID

    def test_zero_quantity(self):
        executor = NoopExecutor()
        order = MockOrder("D001", "buy", 0, "AAPL")
        hint = MockHint("test")

        result = executor.execute(order, hint)
        assert result.status == ExecutionStatus.INVALID
```

### 2. 통합 테스트

```bash
# 기존 테스트 통과 확인
pytest app/obs_deploy/app/src/decision_pipeline/ -v

# 상속 관계 확인
python -c "
from decision_pipeline.execution_stub import *
print(f'Noop inherits Base: {issubclass(NoopExecutor, BaseExecutor)}')
print(f'Sim inherits Base: {issubclass(SimExecutor, BaseExecutor)}')
print(f'Virtual inherits Base: {issubclass(VirtualExecutor, BaseExecutor)}')
"
```

### 3. 핑거프린트 호환성

```bash
# 기존 핑거프린트와 동일한지 확인
python -c "
from shared.serialization import order_hint_fingerprint
from dataclasses import dataclass

@dataclass
class Order:
    id: str = '123'

@dataclass
class Hint:
    action: str = 'buy'

fp = order_hint_fingerprint(Order(), Hint())
print(f'Fingerprint: {fp}')
print(f'Length: {len(fp)}')
"
```

---

## 완료 조건

- [ ] `execution_stub/base_executor.py` 파일 생성됨
- [ ] `BaseExecutor` 추상 클래스 구현됨
- [ ] `ExecutionMode`, `ExecutionStatus`, `ExecutionResult` 정의됨
- [ ] `NoopExecutor`가 `BaseExecutor` 상속
- [ ] `SimExecutor`가 `BaseExecutor` 상속
- [ ] `VirtualExecutor`가 `BaseExecutor` 상속
- [ ] 중복 `_safe_to_dict()` 제거됨
- [ ] 중복 `_fingerprint()` 제거됨
- [ ] `execution_stub/__init__.py` 업데이트됨
- [ ] 단위 테스트 통과
- [ ] 핑거프린트 호환성 확인됨
- [ ] 기존 테스트 모두 통과

---

## 코드 중복 감소 예상

| 항목 | Before | After | 감소 |
|------|--------|-------|------|
| `_safe_to_dict()` | 2개 | 0개 (shared 모듈) | 100% |
| `_fingerprint()` | 2개 | 0개 (shared 모듈) | 100% |
| 유효성 검사 | 3개 | 1개 (base) | 67% |
| 결과 생성 | 3개 | 1개 (base) | 67% |

---

## 관련 태스크
- [TASK-1.4](../phase-1/TASK-1.4-serialization.md): Serialization 유틸리티 (선행)
- [TASK-3.1](TASK-3.1-base-collector.md): BaseCollector (유사 패턴)
