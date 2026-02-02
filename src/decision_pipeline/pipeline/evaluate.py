from __future__ import annotations

from typing import Any, Dict


class Evaluator:
    """
    Evaluate 단계

    - 전략/리스크/포트폴리오 관점에서
      '판단 가능 여부'를 평가한다.
    - Phase 7에서는 실제 엔진 호출 없이
      규칙 기반 기본 판단만 수행한다.
    """

    def evaluate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise TypeError("data must be a dict")

        features = data.get("features", {})

        # 기본 승인 규칙 (Phase 7 최소 기준)
        approved = True
        reason = None

        if features is None:
            approved = False
            reason = "No features provided"

        return {
            "approved": approved,
            "features": features,
            "context": data.get("context", {}),
            "meta": data.get("meta", {}),
            "reason": reason,
        }
