from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional


def _as_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    s = str(value).strip().lower()
    if s in {"true", "1", "yes", "y", "on"}:
        return True
    if s in {"false", "0", "no", "n", "off"}:
        return False
    return default


@dataclass(frozen=True, slots=True)
class ExecutionHint:
    """
    ExecutionHint

    '실행을 하지 않지만' 실행을 가정했을 때 필요한 조건/라우팅 정보를 담는 힌트.
    - execution_stub 계층이 생기면 그대로 소비 가능
    - Observer 분석/로그에서 "왜 실행이 안 됐는지" 설명 보강에 사용 가능

    Note:
    - intended=False가 기본이며, Phase 7에서는 실행은 항상 비활성(정책)이다.
    """

    intended: bool = False

    broker: Optional[str] = None
    account: Optional[str] = None

    constraints: Dict[str, Any] = field(default_factory=dict)
    note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intended": self.intended,
            "broker": self.broker,
            "account": self.account,
            "constraints": self.constraints,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExecutionHint":
        return cls(
            intended=_as_bool(data.get("intended"), default=False),
            broker=_as_str(data.get("broker")),
            account=_as_str(data.get("account")),
            constraints=dict(data.get("constraints") or {}),
            note=_as_str(data.get("note")),
        )
