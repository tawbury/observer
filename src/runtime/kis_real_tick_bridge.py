from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Iterator, Protocol

from shared.timezone import now_kst


class KisRealTickClient(Protocol):
    """
    KIS 실계좌 실시간 데이터 클라이언트 인터페이스(Phase 15용).
    - 여기서는 '틱 이벤트 dict'를 yield하는 것만 요구한다.
    - 구현체는 기존에 보유한 KIS 연동 방식을 사용해서 채우면 된다.
    """
    def stream_ticks(self) -> Iterable[Dict[str, Any]]: ...


@dataclass(frozen=True)
class Phase15TickEnvelope:
    raw: Dict[str, Any]
    received_at: str  # ISO8601


class KisRealTickBridge:
    """
    Phase 15 원칙:
    - 실데이터는 가공하지 않는다.
    - raw payload를 그대로 snapshot.meta에 태운다.
    """
    def __init__(self, client: KisRealTickClient, source: str = "kis_real") -> None:
        self._client = client
        self._source = source

    def stream_envelopes(self) -> Iterator[Phase15TickEnvelope]:
        for tick in self._client.stream_ticks():
            yield Phase15TickEnvelope(
                raw=tick,
                received_at=now_kst().isoformat(),
            )

    def to_snapshot_kwargs(self, env: Phase15TickEnvelope) -> Dict[str, Any]:
        """
        ObservationSnapshot 생성에 필요한 kwargs를 '최소'로 구성한다.
        - 필드명은 현재 QTS observer.snapshot.ObservationSnapshot 정의에 맞춰 조정.
        - 중요한 점: tick을 해석하지 말고 meta에 그대로 넣는다.
        """
        # 아래 키들은 예시다. 실제 ObservationSnapshot 필드에 맞게 정렬만 한다.
        return {
            "captured_at": env.received_at,
            "source": self._source,
            "payload": env.raw,  # 혹은 snapshot이 요구하는 원본 필드명
            "meta": {
                "schema_version": "phase15-raw",
                "ingest_mode": "real_tick",
                "raw": env.raw,  # 중복이더라도 '있는 그대로' 보존이 우선
            },
        }
