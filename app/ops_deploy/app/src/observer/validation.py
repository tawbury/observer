from __future__ import annotations

"""
validation.py

Observer-Core Phase 3
- Validation Layer (정합성 검사) 스켈레톤

원칙:
- 구조 변경 없음
- 성능/스켈프 논의 없음
- 판단/분석/학습 없음
- "Observer의 기록 파이프라인"으로 흘려보내기 전에
  입력 스냅샷의 최소 정합성을 보장한다.

주의:
- Validation 실패 시, Phase 3 기준으로 "기록 파이프라인 진입을 차단"한다.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Iterable
import math

from .snapshot import ObservationSnapshot


# ============================================================
# Result Contract
# ============================================================

@dataclass(frozen=True)
class ValidationResult:
    """
    Validation 결과

    - is_valid: 통과 여부
    - severity: INFO | WARN | BLOCK (Phase 3에서는 BLOCK 중심)
    - errors: 사람에게 읽히는 에러 메시지 리스트
    - details: 디버깅/로그용 구조화 데이터 (옵션)
    """
    is_valid: bool
    severity: str
    errors: List[str]
    details: Dict[str, Any]


# ============================================================
# Validator Interface
# ============================================================

class SnapshotValidator(Protocol):
    def validate(self, snapshot: ObservationSnapshot) -> ValidationResult:
        ...


# ============================================================
# Default Implementation
# ============================================================

class DefaultSnapshotValidator:
    """
    Phase 3 기본 Validator

    검증 범위 (확장 금지):
    1) snapshot.meta 필수 키 존재
    2) snapshot.context 필수 키 존재
    3) snapshot.observation.inputs/computed/state 존재 및 dict 타입
    4) inputs/computed/state 내부의 NaN/Inf 차단 (숫자값에 한함)
    """

    def validate(self, snapshot: ObservationSnapshot) -> ValidationResult:
        errors: List[str] = []
        details: Dict[str, Any] = {}

        # -----------------------------
        # 1) meta 검증
        # -----------------------------
        meta = getattr(snapshot, "meta", None)
        if meta is None:
            errors.append("snapshot.meta missing")
        else:
            for key in ("timestamp", "timestamp_ms", "session_id", "run_id", "mode", "observer_version"):
                if getattr(meta, key, None) in (None, ""):
                    errors.append(f"snapshot.meta.{key} missing/empty")

            # timestamp_ms numeric sanity
            ts_ms = getattr(meta, "timestamp_ms", None)
            if ts_ms is not None and not isinstance(ts_ms, int):
                errors.append("snapshot.meta.timestamp_ms must be int")

        # -----------------------------
        # 2) context 검증
        # -----------------------------
        context = getattr(snapshot, "context", None)
        if context is None:
            errors.append("snapshot.context missing")
        else:
            for key in ("source", "stage"):
                if getattr(context, key, None) in (None, ""):
                    errors.append(f"snapshot.context.{key} missing/empty")

        # -----------------------------
        # 3) observation 구조 검증
        # -----------------------------
        obs = getattr(snapshot, "observation", None)
        if obs is None:
            errors.append("snapshot.observation missing")
        else:
            for field in ("inputs", "computed", "state"):
                val = getattr(obs, field, None)
                if val is None:
                    errors.append(f"snapshot.observation.{field} missing")
                    continue
                if not isinstance(val, dict):
                    errors.append(f"snapshot.observation.{field} must be dict")
                    continue

                # -----------------------------
                # 4) NaN / Inf 검사
                # -----------------------------
                bad_paths = list(_find_non_finite_numbers(val, prefix=f"observation.{field}"))
                if bad_paths:
                    errors.append(f"non-finite numbers detected in {field}: {len(bad_paths)}")
                    details[f"non_finite_{field}"] = bad_paths[:50]  # 과도한 출력 방지 (Phase 3)

        # -----------------------------
        # 결과
        # -----------------------------
        if errors:
            return ValidationResult(
                is_valid=False,
                severity="BLOCK",
                errors=errors,
                details=details,
            )

        return ValidationResult(
            is_valid=True,
            severity="INFO",
            errors=[],
            details={},
        )


# ============================================================
# Helpers
# ============================================================

def _is_number(x: Any) -> bool:
    # bool은 int의 서브클래스이므로 제외
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _find_non_finite_numbers(obj: Any, prefix: str) -> Iterable[str]:
    """
    dict/list 내부를 순회하며 NaN/Inf를 찾는다.
    - 숫자 타입(int/float)에 대해서만 isfinite 검사 수행
    - dict key는 문자열로 path를 구성
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}"
            yield from _find_non_finite_numbers(v, path)
        return

    if isinstance(obj, list):
        for i, v in enumerate(obj):
            path = f"{prefix}[{i}]"
            yield from _find_non_finite_numbers(v, path)
        return

    if _is_number(obj):
        # float에 대해 NaN/Inf 차단
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            yield prefix
        return

    # 그 외 타입은 Phase 3에서 관여하지 않음
    return
