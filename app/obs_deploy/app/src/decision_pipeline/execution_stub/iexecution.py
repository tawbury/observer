from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from decision_pipeline.contracts.order_decision import OrderDecision
from decision_pipeline.contracts.execution_hint import ExecutionHint

from .execution_context import ExecutionContext
from .execution_result import ExecutionResult


class IExecution(Protocol):
    """
    IExecution

    실행 계층 인터페이스(계약).
    - Phase 7: NoopExecutor가 항상 실행하지 않음
    - Phase 8: VirtualExecutor가 '실행 가능성 최종 판정'을 수행 (side-effect 없음)
    - Phase 9+: SIM Executor
    - Phase 10+: REAL Executor
    """

    def execute(
        self,
        *,
        order: OrderDecision,
        hint: ExecutionHint,
        context: ExecutionContext,
    ) -> ExecutionResult:
        ...
