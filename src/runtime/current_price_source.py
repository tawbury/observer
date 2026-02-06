from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, Optional, Protocol

from shared.timezone import now_kst


@dataclass(frozen=True)
class CurrentPriceEvent:
    """
    Phase 15 raw event envelope.
    - raw: KIS에서 받은 원본 payload (그대로)
    - received_at: 수신 시각(KST ISO8601)
    """
    raw: Dict[str, Any]
    received_at: str


class CurrentPriceSource(Protocol):
    """
    Phase 15 Source contract.
    - 현재가 이벤트를 "raw dict"로 계속 방출한다.
    - 어떤 방식(REST/WS)이든 상관 없음.
    """
    def stream(self) -> Iterator[CurrentPriceEvent]: ...


class MockCurrentPriceSource:
    """
    로컬에서 Phase 15 파이프를 먼저 뚫기 위한 Mock.
    - 실계좌 연동 전이라도 Observer까지 흐름을 검증 가능.
    """
    def __init__(self, symbol: str = "TEST", interval_sec: float = 1.0) -> None:
        self._symbol = symbol
        self._interval_sec = interval_sec
        self._price = 100.0

    def stream(self) -> Iterator[CurrentPriceEvent]:
        while True:
            self._price += 0.1
            raw = {
                "symbol": self._symbol,
                "last": round(self._price, 2),
                "note": "mock_current_price",
            }
            yield CurrentPriceEvent(
                raw=raw,
                received_at=now_kst().isoformat(),
            )
            time.sleep(self._interval_sec)


class KisCurrentPriceSource:
    """
    KIS 실계좌 현재가 수신 Source (Phase 15용 슬롯).

    중요:
    - 여기서는 KIS SDK/HTTP/WS 구체 구현을 강제하지 않는다.
    - 프로젝트가 아직 구현 전이라고 했으므로, 사용자 환경에 맞게
      fetch_current_price_raw()만 구현하면 된다.

    운영 원칙:
    - raw payload를 '그대로' 반환
    - 해석/정규화/보정 금지
    """

    def __init__(self, symbol: str, interval_sec: float = 1.0) -> None:
        self._symbol = symbol
        self._interval_sec = interval_sec

        # env는 이미 채워져 있다고 했으므로, 존재만 확인해 "명시적 실패"를 만든다.
        self._app_key = os.getenv("KIS_APP_KEY")
        self._app_secret = os.getenv("KIS_APP_SECRET")
        self._account_no = os.getenv("KIS_ACCOUNT_NO")  # 있으면 좋고 없어도 됨(시세만이면)
        if not self._app_key or not self._app_secret:
            raise RuntimeError(
                "Missing KIS credentials in env: KIS_APP_KEY / KIS_APP_SECRET"
            )

    def fetch_current_price_raw(self) -> Dict[str, Any]:
        """
        TODO: 사용자 환경에 맞게 구현.

        반환 규칙:
        - 반드시 dict
        - 반드시 '현재가 payload' 전체를 raw로 반환 (필드 가공 금지)

        예:
        - requests로 REST 호출 결과 json dict 그대로 반환
        - websocket에서 받은 메시지 dict 그대로 반환
        """
        raise NotImplementedError(
            "Implement KIS current price fetch here (REST or WS)."
        )

    def stream(self) -> Iterator[CurrentPriceEvent]:
        while True:
            raw = self.fetch_current_price_raw()
            # raw는 절대 손대지 않는다.
            yield CurrentPriceEvent(
                raw=raw,
                received_at=now_kst().isoformat(),
            )
            time.sleep(self._interval_sec)


def build_phase15_source(symbol: str, mode: Optional[str] = None) -> CurrentPriceSource:
    """
    mode:
      - "mock" (기본): Mock source
      - "kis": KIS 실계좌 source (fetch_current_price_raw 구현 필요)
    """
    m = (mode or os.getenv("PHASE15_SOURCE_MODE") or "mock").lower().strip()
    if m == "kis":
        interval = float(os.getenv("PHASE15_POLL_INTERVAL_SEC", "1.0"))
        return KisCurrentPriceSource(symbol=symbol, interval_sec=interval)
    return MockCurrentPriceSource(symbol=symbol, interval_sec=1.0)
