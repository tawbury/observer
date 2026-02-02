from __future__ import annotations

from typing import Any, Dict

from shared.serialization import order_hint_fingerprint

from decision_pipeline.contracts.order_decision import OrderDecision
from decision_pipeline.contracts.execution_hint import ExecutionHint

from .execution_context import ExecutionContext
from .execution_mode import ExecutionMode
from .execution_result import ExecutionResult, ExecutionStatus
from .execution_guards import apply_execution_guards
from .iexecution import IExecution


class VirtualExecutor(IExecution):
    """
    VirtualExecutor (Phase 8)

    - No external API calls
    - No side effects (enforced by policy defaults)
    - Deterministic validation + audit result
    """

    def execute(
        self,
        *,
        order: OrderDecision,
        hint: ExecutionHint,
        context: ExecutionContext,
    ) -> ExecutionResult:
        # 0) mode sanity
        # VirtualExecutor는 기본적으로 VIRTUAL을 기대하지만,
        # context.mode가 다른 경우에도 "VIRTUAL 판정"만 수행한다(실행하지 않음).
        decision_id = getattr(order, "decision_id", None) or getattr(order, "id", None) or "UNKNOWN"
        action = getattr(order, "action", None)

        fp = order_hint_fingerprint(order, hint)

        # 1) Skip
        if action in (None, "NONE"):
            return ExecutionResult(
                mode=ExecutionMode.VIRTUAL.value,
                status=ExecutionStatus.SKIPPED.value,
                executed=False,
                decision_id=str(decision_id),
                order_fingerprint=fp,
                blocked_by=None,
                reason="action is NONE",
                audit={
                    "action": action,
                    "order": _safe_to_dict(order),
                    "hint": _safe_to_dict(hint),
                    "context": context.to_dict(),
                },
            )

        # 2) Final gate (guards)
        gd = apply_execution_guards(order=order, context=context)
        if gd.blocked_by:
            return ExecutionResult(
                mode=ExecutionMode.VIRTUAL.value,
                status=ExecutionStatus.REJECTED.value,
                executed=False,
                decision_id=str(decision_id),
                order_fingerprint=fp,
                blocked_by=gd.blocked_by,
                reason=gd.reason,
                audit={
                    "guard_audit": gd.audit or {},
                    "order": _safe_to_dict(order),
                    "hint": _safe_to_dict(hint),
                    "context": context.to_dict(),
                },
            )

        # 3) Accepted (still virtual; no execution)
        return ExecutionResult(
            mode=ExecutionMode.VIRTUAL.value,
            status=ExecutionStatus.ACCEPTED.value,
            executed=False,
            decision_id=str(decision_id),
            order_fingerprint=fp,
            blocked_by=None,
            reason="virtual accepted",
            audit={
                "order": _safe_to_dict(order),
                "hint": _safe_to_dict(hint),
                "context": context.to_dict(),
                "note": "No side effects performed (VirtualExecutor).",
            },
        )
