from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from hashlib import sha256
from typing import Any, Dict

from src.ops.decision_pipeline.contracts.order_decision import OrderDecision
from src.ops.decision_pipeline.contracts.execution_hint import ExecutionHint

from .execution_context import ExecutionContext
from .execution_mode import ExecutionMode
from .execution_result import ExecutionResult, ExecutionStatus
from .execution_guards import apply_execution_guards
from .iexecution import IExecution


def _safe_to_dict(obj: Any) -> Dict[str, Any]:
    """
    Best-effort serialization for fingerprint/audit.
    - dataclass: asdict
    - has to_dict: use it
    - fallback: shallow attr dict of common keys
    """
    if obj is None:
        return {}

    if is_dataclass(obj):
        return asdict(obj)

    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        try:
            return dict(to_dict())
        except Exception:
            pass

    # conservative fallback
    keys = ["action", "symbol", "qty", "order_type", "price", "reason", "meta", "metadata", "decision_id", "id"]
    out: Dict[str, Any] = {}
    for k in keys:
        if hasattr(obj, k):
            out[k] = getattr(obj, k)
    return out


def _fingerprint(order: Any, hint: Any) -> str:
    payload = {
        "order": _safe_to_dict(order),
        "hint": _safe_to_dict(hint),
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return sha256(raw.encode("utf-8")).hexdigest()[:16]


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

        fp = _fingerprint(order, hint)

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
