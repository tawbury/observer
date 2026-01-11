from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from .execution_context import ExecutionContext


@dataclass(frozen=True, slots=True)
class GuardDecision:
    blocked_by: Optional[str] = None
    reason: Optional[str] = None
    audit: Dict[str, Any] = None  # type: ignore[assignment]


def apply_execution_guards(
    *,
    order: Any,
    context: ExecutionContext,
) -> GuardDecision:
    """
    Execution-level final gate.

    Phase 8 필수 규칙:
    - action NONE -> SKIPPED는 executor에서 처리(여기서는 차단 아님)
    - symbol empty -> REJECTED
    - qty <= 0 -> REJECTED
    - trading_enabled False -> REJECTED
    - kill_switch True -> REJECTED
    - anomaly_flags present -> REJECTED
    """

    audit: Dict[str, Any] = {}

    symbol = getattr(order, "symbol", None)
    qty = getattr(order, "qty", None)
    action = getattr(order, "action", None)

    audit.update({"action": action, "symbol": symbol, "qty": qty})

    if not symbol:
        return GuardDecision("G_EXE_SYMBOL_EMPTY", "symbol is empty", audit)

    if qty is None or qty <= 0:
        return GuardDecision("G_EXE_QTY_NONPOSITIVE", "qty must be positive", audit)

    if context.trading_enabled is False:
        return GuardDecision("G_EXE_TRADING_DISABLED", "trading_enabled is False", {**audit, "trading_enabled": False})

    if context.kill_switch is True:
        return GuardDecision("G_EXE_KILLSWITCH_ON", "kill_switch is ON", {**audit, "kill_switch": True})

    if context.anomaly_flags:
        return GuardDecision("G_EXE_ANOMALY", "anomaly flags present", {**audit, "anomaly_flags": list(context.anomaly_flags)})

    return GuardDecision(None, None, audit)
