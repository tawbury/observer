from __future__ import annotations

"""
pattern_record.py

파일 경로:
    src/ops/observer/pattern_record.py

역할 요약:
- ObservationSnapshot을 "Observer-Core의 최종 출력 데이터 자산"으로 감싼다.
- 이 파일은 판단/분석/학습을 하지 않는다.
- 오직 '데이터 구조(형태)'만 정의한다.

초보자 가이드:
- snapshot은 "사실 기록"이다.
- PatternRecord는 "패턴 분석을 위한 최소 단위 컨테이너"다.
- 지금 비어 있는 필드들은 의도적으로 남겨둔 확장 슬롯이다.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, List

from .snapshot import ObservationSnapshot


# ============================================================
# Pattern Record (Observer Output Asset)
# ============================================================

@dataclass(frozen=True)
class PatternRecord:
    """
    Observer-Core 최종 데이터 자산 단위 (Phase 2 기준)

    이 클래스는:
    - Observer가 외부로 내보내는 "최종 산출물"이며
    - 파일(JSONL), DB, 분석 파이프라인으로 전달될 수 있다.

    구성 필드 설명:

    1) snapshot
       - ObservationSnapshot
       - 실제 관측된 데이터 (시간, 입력값, 상태 등)
       - 절대 수정하지 않고 그대로 보존한다.

    2) regime_tags
       - 시장 국면 태그 (예: bull / bear / sideway)
       - Phase 2에서는 사용하지 않으며, 빈 dict가 정상이다.

    3) condition_tags
       - 조건 태그 (예: rsi_oversold, breakout 등)
       - Phase 2에서는 사용하지 않으며, 빈 list가 정상이다.

    4) outcome_labels
       - 결과 라벨 (예: win / loss / pnl)
       - Phase 2에서는 사용하지 않으며, 빈 dict가 정상이다.

    5) metadata
       - 데이터 관리 및 추적용 정보
       - 예: schema_version, dataset_version, build_id, session_id 등
       - Observer / EventBus / 외부 분석 단계에서 활용된다.
    """

    snapshot: ObservationSnapshot
    regime_tags: Dict[str, Any]
    condition_tags: List[Dict[str, Any]]
    outcome_labels: Dict[str, Any]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """
        PatternRecord를 dict로 변환한다.

        사용 목적:
        - JSONL 파일 저장
        - 외부 시스템 전달
        - 향후 분석/학습 파이프라인 입력

        주의:
        - 이 메서드는 구조 변환만 수행한다.
        - 데이터 의미를 해석하거나 변경하지 않는다.
        """
        return asdict(self)
