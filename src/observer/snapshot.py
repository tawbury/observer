from __future__ import annotations

"""
snapshot.py
- Observer-Core Phase 2의 "기록 단위"를 정의하는 파일
- 1 Snapshot = 1 관측 레코드(나중에 JSONL로 1줄 저장)

초보자 가이드
- 이 파일은 "데이터 모양(구조)"을 고정하는 용도다.
- 여기서는 판단/분석/실행을 하지 않는다.
- 외부에서 관측한 값(inputs/computed/state)을 받아서, 정해진 포맷으로 묶어준다.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
from datetime import datetime, timezone
import uuid


# ============================================================
# Short-term State Cache (module-local, minimal)
# ============================================================

_last_price: Optional[float] = None
_last_volume: Optional[float] = None


# ============================================================
# Time / ID Utilities
# ============================================================

def utc_now_iso() -> str:
    """
    현재 시간을 UTC ISO-8601 문자열로 반환한다.
    예: '2025-12-25T03:12:45.123Z'
    """
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def utc_now_ms() -> int:
    """
    현재 시간을 epoch milliseconds(UTC)로 반환한다.
    - 스켈프 확장 시 시간 해상도 강화를 위해 유지하는 값
    """
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def new_run_id() -> str:
    """
    Snapshot 단위의 고유 ID를 생성한다.
    - uuid4 기반 (충돌 가능성 매우 낮음)
    """
    return uuid.uuid4().hex


# ============================================================
# Meta
# ============================================================

@dataclass(frozen=True)
class Meta:
    """
    Snapshot 메타 정보 (언제/어떤 세션에서 기록됐는가)

    필수:
    - timestamp / timestamp_ms : 시간
    - session_id               : 실행 묶음 ID (네가 정하는 값, 예: 'session_001')
    - run_id                   : 스냅샷 1개 고유 ID (보통 자동 생성)
    - mode                     : 'DEV' / 'PROD' 등
    - observer_version         : 버전 추적용
    
    확장 필드 (Scalp Extension E2):
    - iteration_id             : 루프 반복 카운터
    - loop_interval_ms         : 목표 루프 주기
    - latency_ms               : 수집 지연
    - tick_source              : 데이터 유입 채널
    - buffer_depth             : 버퍼 깊이
    - flush_reason             : 플러시 트리거
    """
    timestamp: str              # ISO-8601 (UTC)
    timestamp_ms: int           # epoch milliseconds (UTC)
    session_id: str
    run_id: str
    mode: str
    observer_version: str = "v1.0.0"
    
    # Extended meta fields (Scalp Extension E2)
    iteration_id: Optional[int] = None
    loop_interval_ms: Optional[float] = None
    latency_ms: Optional[float] = None
    tick_source: Optional[str] = None
    buffer_depth: Optional[int] = None
    flush_reason: Optional[str] = None


# ============================================================
# Context
# ============================================================

@dataclass(frozen=True)
class Context:
    """
    관측 컨텍스트 (관측 성격)

    - source: 데이터 출처
      - market | broker | system | external
    - stage: 관측 단계/성격
      - raw | computed | state

    symbol/market는 없을 수도 있으므로 Optional.
    """
    source: str
    stage: str
    symbol: Optional[str] = None
    market: Optional[str] = None


# ============================================================
# Observation
# ============================================================

@dataclass(frozen=True)
class Observation:
    """
    판단 없는 순수 관측 데이터

    - inputs   : 원천 데이터 (가격/거래량 등)
    - computed : 계산 결과 (RSI/이동평균 등)
    - state    : 상태 정보 (포지션/레짐 등)
    """
    inputs: Dict[str, Any]
    computed: Dict[str, Any]
    state: Dict[str, Any]


# ============================================================
# Observation Snapshot (Contract Unit)
# ============================================================

@dataclass(frozen=True)
class ObservationSnapshot:
    """
    Observer Core - Minimal Observation Unit (Contract v1.0.0)

    This is the atomic unit of observation data passed through the system.
    """
    meta: Meta
    context: Context
    observation: Observation

    def to_dict(self) -> Dict[str, Any]:
        """
        JSON 직렬화 / 저장 / 학습용 변환
        - dataclass를 dict로 변환해준다.
        """
        return asdict(self)


# ============================================================
# Internal helpers
# ============================================================

def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _compute_short_deltas(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    직전 관측값 기준 단기 delta 계산
    - 판단/플래그 없음
    - 숫자값만 기록
    """
    global _last_price, _last_volume

    computed: Dict[str, Any] = {}

    price = inputs.get("price")
    volume = inputs.get("volume")

    # ---- price delta ----
    if _is_number(price):
        if _last_price is not None:
            computed["price_delta_short"] = price - _last_price
        else:
            computed["price_delta_short"] = 0
        _last_price = price

    # ---- volume delta ----
    if _is_number(volume):
        if _last_volume is not None:
            computed["volume_delta_short"] = volume - _last_volume
        else:
            computed["volume_delta_short"] = 0
        _last_volume = volume

    return computed


# ============================================================
# Snapshot Factory (초보자용 진입점)
# ============================================================

def build_snapshot(
    *,
    session_id: str,
    mode: str,
    source: str,
    stage: str,
    inputs: Dict[str, Any],
    computed: Optional[Dict[str, Any]] = None,
    state: Optional[Dict[str, Any]] = None,
    symbol: Optional[str] = None,
    market: Optional[str] = None,
    observer_version: str = "v1.0.0",
    run_id: Optional[str] = None,
    # Extended meta fields (Scalp Extension E2)
    iteration_id: Optional[int] = None,
    loop_interval_ms: Optional[float] = None,
    latency_ms: Optional[float] = None,
    tick_source: Optional[str] = None,
    buffer_depth: Optional[int] = None,
    flush_reason: Optional[str] = None,
) -> ObservationSnapshot:
    """
    초보자용 스냅샷 생성 함수 (권장 사용법)

    사용 예:
        snapshot = build_snapshot(
            session_id="session_001",
            mode="DEV",
            source="market",
            stage="raw",
            inputs={"price": 71000, "volume": 12345},
            computed={"rsi": 42.1},
            state={"position": 0},
            symbol="005930",
            market="KRX",
        )

    포인트:
    - computed/state는 없으면 자동으로 빈 dict 처리된다.
    - timestamp / timestamp_ms / run_id 는 자동 생성된다(안전).
    """
    computed = computed or {}
    state = state or {}

    meta = Meta(
        timestamp=utc_now_iso(),
        timestamp_ms=utc_now_ms(),
        session_id=session_id,
        run_id=run_id or new_run_id(),
        mode=mode,
        observer_version=observer_version,
        # Extended meta fields (Scalp Extension E2)
        iteration_id=iteration_id,
        loop_interval_ms=loop_interval_ms,
        latency_ms=latency_ms,
        tick_source=tick_source,
        buffer_depth=buffer_depth,
        flush_reason=flush_reason,
    )

    context = Context(
        source=source,
        stage=stage,
        symbol=symbol,
        market=market,
    )

    observation = Observation(
        inputs=inputs,
        computed=computed,
        state=state,
    )

    return ObservationSnapshot(
        meta=meta,
        context=context,
        observation=observation,
    )
