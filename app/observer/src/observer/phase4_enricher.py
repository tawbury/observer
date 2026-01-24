from __future__ import annotations

"""
phase4_enricher.py

Observer-Core Phase 4:
- PatternRecord를 대상으로 "품질 태깅(Quality)" 및 "해석 메타데이터(Interpretation)"를 추가한다.

중요한 경계:
- Execution / Strategy / Risk / Safety 로직 금지
- 매수/매도 판단 금지
- 결과(outcome) 라벨링 금지 (Phase 5 이후)

이 파일의 역할:
- PatternRecord 생성 이후, EventBus dispatch 전에
  record.metadata에 다음 네임스페이스를 부착한다.

  metadata:
    _schema:         스키마 라이트(버전/호환)
    _quality:        품질 태그/통계/플래그
    _interpretation: 해석 보조(결론/판단 금지)

설계 포인트:
- PatternRecord는 frozen dataclass이므로 "수정"하지 않고 새 레코드를 만들어 반환한다.
- 품질/해석 메타데이터는 반드시 metadata 하위 네임스페이스로만 추가한다.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Protocol, Tuple

from .pattern_record import PatternRecord
from .snapshot import ObservationSnapshot
from .schema_lite import (
    NS_QUALITY,
    NS_INTERPRETATION,
    apply_schema_lite,
)


# ============================================================
# Enricher Interface
# ============================================================

class RecordEnricher(Protocol):
    """
    Phase 4 Enricher 인터페이스
    """
    def enrich(self, record: PatternRecord) -> PatternRecord:
        ...


# ============================================================
# Quality Tagger
# ============================================================

@dataclass(frozen=True)
class QualityResult:
    flags: List[str]
    stats: Dict[str, Any]


class QualityTagger:
    """
    관측 데이터의 "품질 특성"을 태깅한다.

    주의:
    - Phase 3 Validation은 기록 차단이 목적이다.
    - Phase 4 Quality는 "분류/우선순위 판단을 위한 속성" 기록이 목적이다.
    - 따라서 Phase 4는 차단하지 않는다.
    """

    def tag(self, snapshot: ObservationSnapshot) -> QualityResult:
        flags: List[str] = []
        stats: Dict[str, Any] = {}

        # -----------------------------
        # 기본 구조 통계
        # -----------------------------
        inputs = snapshot.observation.inputs or {}
        computed = snapshot.observation.computed or {}
        state = snapshot.observation.state or {}

        stats["inputs_count"] = len(inputs)
        stats["computed_count"] = len(computed)
        stats["state_count"] = len(state)

        if len(inputs) == 0:
            flags.append("EMPTY_INPUTS")

        # computed/state는 빈 dict가 정상일 수 있으므로 경고 수준만 기록
        if len(computed) == 0:
            flags.append("NO_COMPUTED")
        if len(state) == 0:
            flags.append("NO_STATE")

        # -----------------------------
        # 시간 해상도/준비도(스켈프 친화성의 '중립 지표')
        # -----------------------------
        # 스켈프/스윙을 판별하지 않고, "ms 타임스탬프가 있는지" 같은 중립 속성만 남긴다.
        stats["timestamp_ms"] = snapshot.meta.timestamp_ms
        stats["timestamp_iso"] = snapshot.meta.timestamp
        stats["time_resolution"] = "ms"  # contract 상 timestamp_ms 제공

        # -----------------------------
        # 관측 최소 키 존재 여부(분석/필터링 편의)
        # -----------------------------
        # 단, 여기서 price/volume을 "필수"로 가정하지 않는다.
        # 있을 경우만 표시한다.
        stats["has_price"] = "price" in inputs
        stats["has_volume"] = "volume" in inputs

        # -----------------------------
        # 값 타입/기초 이상치 힌트(판단 금지, 힌트만)
        # -----------------------------
        # Validation이 이미 비정상 값을 막았더라도,
        # "데이터가 실제로 숫자 형태로 들어왔는지" 같은 힌트는 남길 수 있다.
        def _is_number(x: Any) -> bool:
            return isinstance(x, (int, float)) and not isinstance(x, bool)

        if "price" in inputs and not _is_number(inputs.get("price")):
            flags.append("PRICE_NOT_NUMERIC")
        if "volume" in inputs and not _is_number(inputs.get("volume")):
            flags.append("VOLUME_NOT_NUMERIC")

        return QualityResult(flags=flags, stats=stats)


# ============================================================
# Interpretation Annotator
# ============================================================

@dataclass(frozen=True)
class InterpretationResult:
    summary: Dict[str, Any]
    hints: List[str]


class InterpretationAnnotator:
    """
    해석 메타데이터(Interpretation Metadata)

    절대 금지:
    - BUY/SELL 같은 실행 결론
    - 리스크 승인/거부
    - 전략적 판단

    허용:
    - "이 레코드가 어떤 관측인지" 빠르게 이해하도록 돕는 요약/힌트
    """

    def annotate(self, snapshot: ObservationSnapshot) -> InterpretationResult:
        hints: List[str] = []
        summary: Dict[str, Any] = {}

        # -----------------------------
        # 컨텍스트 요약
        # -----------------------------
        summary["source"] = snapshot.context.source
        summary["stage"] = snapshot.context.stage
        summary["symbol"] = snapshot.context.symbol
        summary["market"] = snapshot.context.market

        # -----------------------------
        # 입력 주요 값 일부만 '요약' (과도한 데이터 복제 금지)
        # -----------------------------
        inputs = snapshot.observation.inputs or {}

        # 관례적으로 많이 쓰는 키만 "있으면" 요약한다.
        # (없으면 None을 넣지 않고 아예 생략)
        if "price" in inputs:
            summary["price"] = inputs.get("price")
            hints.append("HAS_PRICE")
        if "volume" in inputs:
            summary["volume"] = inputs.get("volume")
            hints.append("HAS_VOLUME")

        # -----------------------------
        # 계산/상태 존재 힌트
        # -----------------------------
        if snapshot.observation.computed:
            hints.append("HAS_COMPUTED")
        if snapshot.observation.state:
            hints.append("HAS_STATE")

        return InterpretationResult(summary=summary, hints=hints)


# ============================================================
# Default Phase 4 Enricher
# ============================================================

class DefaultRecordEnricher:
    """
    Phase 4 기본 Enricher

    입력:
      - PatternRecord (Phase 3까지 생성된 레코드)

    출력:
      - PatternRecord (metadata 확장된 레코드)

    주의:
      - record.regime_tags / condition_tags / outcome_labels는 Phase 4에서 변경하지 않는다.
      - 오직 metadata namespace만 확장한다.
    """

    def __init__(
        self,
        *,
        producer: str = "observer_core",
        build_id: str = "observer_core_v1",
        dataset_version: str = "v1.0.0",
    ) -> None:
        self._producer = producer
        self._build_id = build_id
        self._dataset_version = dataset_version

        self._quality = QualityTagger()
        self._interpretation = InterpretationAnnotator()

    def enrich(self, record: PatternRecord) -> PatternRecord:
        snapshot = record.snapshot

        # -----------------------------
        # 1) Quality / Interpretation 생성
        # -----------------------------
        q = self._quality.tag(snapshot)
        it = self._interpretation.annotate(snapshot)

        # -----------------------------
        # 2) metadata 확장 (네임스페이스 고정)
        # -----------------------------
        md = dict(record.metadata)

        # Schema-Lite 적용: _schema 영역 표준화 + 버전 기록
        md = apply_schema_lite(
            md,
            producer=self._producer,
            build_id=self._build_id,
            dataset_version=self._dataset_version,
            generated_at=record.metadata.get("generated_at", ""),
            session_id=record.metadata.get("session_id", ""),
            mode=record.metadata.get("mode", ""),
        )

        # Quality 네임스페이스
        quality_payload: Dict[str, Any] = {
            "flags": q.flags,     # 분류용 플래그
            "stats": q.stats,     # 카운트/시간/존재 여부 등의 중립 통계
        }
        md[NS_QUALITY] = _merge_dict(md.get(NS_QUALITY, {}), quality_payload)

        # Interpretation 네임스페이스
        interpretation_payload: Dict[str, Any] = {
            "summary": it.summary,  # 관측 요약
            "hints": it.hints,      # 해석 보조 힌트 (결론 아님)
        }
        md[NS_INTERPRETATION] = _merge_dict(md.get(NS_INTERPRETATION, {}), interpretation_payload)

        # -----------------------------
        # 3) 새 PatternRecord 반환 (불변성 유지)
        # -----------------------------
        return PatternRecord(
            snapshot=record.snapshot,
            regime_tags=record.regime_tags,
            condition_tags=record.condition_tags,
            outcome_labels=record.outcome_labels,
            metadata=md,
        )


def _merge_dict(base: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
    """
    얕은 병합(append-only 성격)
    - base에 있는 값은 유지하되, extra 키가 겹치면 extra가 우선한다.
    - Phase 4는 "최신 생성 결과"를 우선하는 것이 자연스럽다.
    """
    out = dict(base)
    out.update(extra)
    return out
