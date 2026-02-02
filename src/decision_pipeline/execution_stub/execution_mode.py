from __future__ import annotations

from enum import Enum


class ExecutionMode(str, Enum):
    """
    ExecutionMode

    Virtual → SIM → REAL 단계 확장용 모드.
    Phase 8에서는 VIRTUAL만 구현 대상.
    """

    VIRTUAL = "VIRTUAL"
    SIM = "SIM"
    REAL = "REAL"
