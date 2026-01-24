from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class ExecutionStatus(str, Enum):
    """
    ExecutionStatus

    - ACCEPTED: 실행 가능 판정(단, VIRTUAL은 실행하지 않음)
    - REJECTED: 최종 관문(guard/kill-switch)에서 차단
    - SKIPPED: 실행 대상 아님 (action NONE 등)
    """

    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    SKIPPED = "SKIPPED"


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """
    ExecutionResult (Phase 8)

    기존 Phase 7의 NOOP 중심 계약을 확장한다.
    - status/blocked_by/audit를 표준화해 SIM/REAL 확장 시에도 유지한다.

    호환성:
    - NoopExecutor는 "NOOP"로도 계속 반환 가능하지만,
      Phase 8부터는 status를 가능한 한 표준 상태(ACCEPTED/REJECTED/SKIPPED)로 사용하는 것을 권장.
    """

    mode: str
    status: str
    executed: bool

    decision_id: str
    order_fingerprint: str

    blocked_by: Optional[str] = None
    reason: Optional[str] = None
    audit: Optional[Dict[str, Any]] = None
