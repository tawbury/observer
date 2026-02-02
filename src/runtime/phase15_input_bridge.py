from __future__ import annotations

import inspect
from dataclasses import is_dataclass, fields
from typing import Any, Dict, Type

from ops.runtime.phase15_current_price_source import CurrentPriceEvent


class Phase15InputBridge:
    """
    Phase 15 원칙:
    - raw payload를 가공하지 않는다.
    - 정식 ObservationSnapshot 계약(context, observation)을 '최소 형태'로 만족시킨다.
    """

    def __init__(
        self,
        snapshot_cls: Type[Any],
        source_name: str = "kis_real",
        ingest_name: str = "phase15_current_price",
    ) -> None:
        self._snapshot_cls = snapshot_cls
        self._source_name = source_name
        self._ingest_name = ingest_name

    def _build_context(self, ev: CurrentPriceEvent) -> Dict[str, Any]:
        """
        Phase 15 전용 컨텍스트.
        - 의미 최소화
        - 관찰 정보만 포함
        """
        return {
            "phase": "phase15",
            "ingest": self._ingest_name,
            "source": self._source_name,
            "received_at": ev.received_at,
        }

    def _build_observation(self, ev: CurrentPriceEvent) -> Dict[str, Any]:
        """
        Phase 15 Observation.
        - raw payload를 그대로 담는다.
        """
        return {
            "raw": ev.raw,
            "received_at": ev.received_at,
        }

    def build_snapshot(self, ev: CurrentPriceEvent) -> Any:
        cls = self._snapshot_cls

        context = self._build_context(ev)
        observation = self._build_observation(ev)

        candidates: Dict[str, Any] = {
            "context": context,
            "observation": observation,
            # 혹시 기존 Snapshot이 추가 필드를 허용하는 경우 대비
            "meta": {
                "schema_version": "phase15-raw",
                "ingest": self._ingest_name,
            },
        }

        # dataclass 기반 Snapshot
        if is_dataclass(cls):
            allowed = {f.name for f in fields(cls)}
            kwargs = {k: v for k, v in candidates.items() if k in allowed}
            return cls(**kwargs)

        # 일반 class 기반 Snapshot
        sig = inspect.signature(cls.__init__)
        params = set(sig.parameters.keys()) - {"self"}
        kwargs = {k: v for k, v in candidates.items() if k in params}

        if "context" not in kwargs or "observation" not in kwargs:
            raise RuntimeError(
                f"Phase15InputBridge cannot satisfy ObservationSnapshot contract. "
                f"Required: context, observation | Found: {sorted(kwargs.keys())}"
            )

        return cls(**kwargs)
