from __future__ import annotations

from typing import Any, Dict


class Extractor:
    """
    Extract 단계

    - Observer / Runtime으로부터 전달된 context에서
      판단 파이프라인에 필요한 입력을 추출한다.
    - 외부 I/O는 수행하지 않는다.
    """

    def extract(self, context: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(context, dict):
            raise TypeError("context must be a dict")

        return {
            "context": context,
            "inputs": context.get("inputs", {}),
            "meta": {
                "source": context.get("source", "unknown"),
                "session_id": context.get("session_id"),
            },
        }
