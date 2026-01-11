from __future__ import annotations

"""
guard.py

Observer-Core Phase 3
- Guard Layer (사전 차단) 스켈레톤

원칙:
- ValidationResult를 기반으로만 얇게 차단한다.
- Safety/KillSwitch로 확장하지 않는다. (Phase 3 제외)
- 구조 변경/성능 논의/스켈프 고려 없음
"""

from dataclasses import dataclass
from typing import Any, Dict

from .snapshot import ObservationSnapshot
from .validation import ValidationResult


@dataclass(frozen=True)
class GuardDecision:
    """
    Guard 판단 결과

    - allow: 기록 파이프라인 진입 허용 여부
    - action: PASS | BLOCK | NO_OP
    - reason: 단일 사유 문자열
    - details: 추가 정보 (옵션)
    """
    allow: bool
    action: str
    reason: str
    details: Dict[str, Any]


class DefaultGuard:
    """
    Phase 3 기본 Guard

    정책(확장 금지):
    1) ValidationResult.is_valid == False 이면 BLOCK
    2) stage 값이 비정상/미정이면 BLOCK (Validation이 이미 잡지만 2중 안전)
    """

    def decide(self, snapshot: ObservationSnapshot, validation: ValidationResult) -> GuardDecision:
        if not validation.is_valid:
            return GuardDecision(
                allow=False,
                action="BLOCK",
                reason="Validation failed",
                details={"severity": validation.severity, "errors": validation.errors[:20]},
            )

        stage = getattr(snapshot.context, "stage", None)
        if stage in (None, ""):
            return GuardDecision(
                allow=False,
                action="BLOCK",
                reason="Invalid context.stage",
                details={},
            )

        return GuardDecision(
            allow=True,
            action="PASS",
            reason="OK",
            details={},
        )
