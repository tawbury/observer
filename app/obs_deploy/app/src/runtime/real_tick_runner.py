from __future__ import annotations

import logging
from typing import Any, Dict

from ops.observer.observer import Observer
from ops.runtime.kis_real_tick_bridge import KisRealTickBridge, KisRealTickClient

log = logging.getLogger("Phase15RealTickRunner")


def _assert_trading_disabled() -> None:
    """
    Phase 15: 거래는 0건이어야 한다.
    Config 로딩 구조가 이미 있다면 여기서 'trading_enabled == False'를 확인하라.
    지금 단계에서는 최소 안전장치로, 운영자가 확실히 off 했다는 전제 문구를 남긴다.
    """
    log.warning("Phase 15 safety: ensure trading_enabled == False (NO ORDERS).")


class Phase15RealTickRunner:
    def __init__(self, observer: Observer, kis_client: KisRealTickClient) -> None:
        self._observer = observer
        self._bridge = KisRealTickBridge(kis_client)

    def run_forever(self) -> None:
        _assert_trading_disabled()

        for env in self._bridge.stream_envelopes():
            try:
                snapshot_kwargs: Dict[str, Any] = self._bridge.to_snapshot_kwargs(env)

                # ObservationSnapshot 생성부는 프로젝트 기존 정의에 맞게 맞춘다.
                # 예) snapshot = ObservationSnapshot(**snapshot_kwargs)
                # 아래는 "생성/전달" 위치만 명확히 하기 위한 placeholder다.
                snapshot = self._observer._snapshot_factory(**snapshot_kwargs)  # type: ignore[attr-defined]

                self._observer.observe(snapshot)

            except Exception as e:
                # Phase 15 원칙: 조용한 실패 금지
                log.exception("Phase 15 tick ingest failed: %s", e)
                raise
