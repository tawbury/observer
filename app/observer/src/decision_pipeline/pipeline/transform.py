from __future__ import annotations

from typing import Any, Dict


class Transformer:
    """
    Transform 단계

    - Extract 결과를 Evaluate가 소비 가능한 형태로 정규화
    - Phase 7에서는 feature engineering은 수행하지 않는다.
    """

    def transform(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(raw, dict):
            raise TypeError("raw must be a dict")

        return {
            "features": raw.get("inputs", {}),
            "context": raw.get("context", {}),
            "meta": raw.get("meta", {}),
        }
