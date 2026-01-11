from __future__ import annotations

from typing import Any, Dict, Optional

from src.ops.decision_pipeline.contracts.decision_snapshot import DecisionSnapshot
from src.ops.decision_pipeline.contracts.order_decision import OrderDecision
from src.ops.decision_pipeline.contracts.execution_hint import ExecutionHint


class Decider:
    """
    Decide 단계

    - Evaluate 결과를 기반으로
      '실행하지 않는 판단 계약 객체'를 생성한다.
    """

    def decide(
        self,
        evaluation: Dict[str, Any],
        *,
        strategy_name: Optional[str] = None,
    ) -> Dict[str, Any]:

        approved: bool = bool(evaluation.get("approved", False))
        reason: Optional[str] = evaluation.get("reason")

        # Phase 7 고정: 실행 없음
        order_decision = OrderDecision.none(
            reason="Execution excluded (Phase 7)"
        )

        snapshot = DecisionSnapshot.new(
            pipeline_step="DECIDE",
            action="NONE",
            strategy_name=strategy_name,
            risk_approved=approved,
            portfolio_adjusted=False,
            reason=reason,
            metadata={
                "phase": 7,
                "approved": approved,
                "note": "Decision recorded without execution",
            },
        )

        execution_hint = ExecutionHint(
            intended=False,
            note="Execution intentionally disabled in Phase 7",
        )

        return {
            "order_decision": order_decision,
            "decision_snapshot": snapshot,
            "execution_hint": execution_hint,
        }
