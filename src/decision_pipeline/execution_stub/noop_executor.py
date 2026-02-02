from __future__ import annotations

from dataclasses import dataclass

from decision_pipeline.contracts.order_decision import OrderDecision
from decision_pipeline.contracts.execution_hint import ExecutionHint

from .execution_context import ExecutionContext
from .execution_mode import ExecutionMode
from .execution_result import ExecutionResult
from .iexecution import IExecution


@dataclass(frozen=True, slots=True)
class NoopExecutor(IExecution):
    """
    NoopExecutor

    Phase 7 정책 유지:
    - executor는 존재하되, 항상 실행하지 않는다.
    - pipeline은 executor를 호출해도 안전해야 한다.
    """

    reason: str = "Execution intentionally disabled (NOOP)"

    def execute(
        self,
        *,
        order: OrderDecision,
        hint: ExecutionHint,
        context: ExecutionContext,
    ) -> ExecutionResult:
        _ = order
        _ = hint
        _ = context

        # Noop은 Virtual로 취급(실행 불가가 아니라 '정책상 실행 안 함')
        return ExecutionResult(
            mode=ExecutionMode.VIRTUAL.value,
            status="SKIPPED",
            executed=False,
            decision_id=getattr(order, "decision_id", None) or getattr(order, "id", None) or "UNKNOWN",
            order_fingerprint="noop",
            blocked_by="G_EXE_NOOP_POLICY",
            reason=self.reason,
            audit={"executor": "NoopExecutor"},
        )
