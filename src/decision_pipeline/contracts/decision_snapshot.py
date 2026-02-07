from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional
from uuid import uuid4

from shared.timezone import KST, now_kst


# ---------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------

def _utcnow() -> datetime:
    return now_kst()


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


def _as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s:
        return None
    return float(s)


def _parse_dt(value: Any) -> datetime:
    """
    Accepts:
      - datetime
      - ISO-8601 string
      - None -> utcnow()
    """
    if value is None:
        return _utcnow()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=KST or timezone.utc)
        return value.astimezone(KST or timezone.utc)
    s = str(value).strip()
    if not s:
        return _utcnow()
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=KST or timezone.utc)
    return dt.astimezone(KST or timezone.utc)


def _require_non_empty(name: str, value: Optional[str]) -> str:
    if value is None or not str(value).strip():
        raise ValueError(f"{name} must be a non-empty string")
    return str(value).strip()


# ---------------------------------------------------------------------
# contract
# ---------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class DecisionSnapshot:
    """
    DecisionSnapshot

    Evaluate / Decide 결과를
    '실행하지 않는 판단 자산'으로 고정하는 계약 객체.

    - Act(Execution) 단계 없음
    - Observer / Ops / Test 공용
    - JSON 직렬화 가능
    """

    # -----------------------------------------------------------------
    # identity (non-default)
    # -----------------------------------------------------------------
    decision_id: str
    created_at: datetime

    # -----------------------------------------------------------------
    # pipeline context (non-default)
    # -----------------------------------------------------------------
    pipeline_step: str          # e.g. "DECIDE"
    action: str                 # BUY / SELL / HOLD / NONE

    # -----------------------------------------------------------------
    # optional context (default)
    # -----------------------------------------------------------------
    strategy_name: Optional[str] = None
    symbol: Optional[str] = None
    qty: Optional[float] = None

    # -----------------------------------------------------------------
    # evaluation flags
    # -----------------------------------------------------------------
    risk_approved: bool = False
    portfolio_adjusted: bool = False

    # -----------------------------------------------------------------
    # explanation / metadata
    # -----------------------------------------------------------------
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # -----------------------------------------------------------------
    # factories
    # -----------------------------------------------------------------
    @classmethod
    def new(
        cls,
        *,
        pipeline_step: str,
        action: str,
        strategy_name: Optional[str] = None,
        symbol: Optional[str] = None,
        qty: Optional[float] = None,
        risk_approved: bool = False,
        portfolio_adjusted: bool = False,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        decision_id: Optional[str] = None,
    ) -> "DecisionSnapshot":

        snapshot = cls(
            decision_id=decision_id or uuid4().hex,
            created_at=_parse_dt(created_at),
            pipeline_step=_require_non_empty(
                "pipeline_step", _as_str(pipeline_step)
            ),
            action=_require_non_empty(
                "action", _as_str(action)
            ).upper(),
            strategy_name=_as_str(strategy_name),
            symbol=_as_str(symbol),
            qty=_as_float(qty),
            risk_approved=bool(risk_approved),
            portfolio_adjusted=bool(portfolio_adjusted),
            reason=_as_str(reason),
            metadata=dict(metadata or {}),
        )
        return snapshot.validate()

    # -----------------------------------------------------------------
    # validation
    # -----------------------------------------------------------------
    def validate(self) -> "DecisionSnapshot":
        action = self.action.upper().strip()
        if action not in {"BUY", "SELL", "HOLD", "NONE"}:
            raise ValueError(
                f"action must be one of BUY/SELL/HOLD/NONE, got: {self.action!r}"
            )

        if self.qty is not None and self.qty <= 0:
            raise ValueError(
                f"qty must be positive when provided, got: {self.qty!r}"
            )

        if not self.pipeline_step.strip():
            raise ValueError("pipeline_step must be non-empty")

        if self.created_at.tzinfo is None:
             raise ValueError("created_at must be timezone-aware (KST)")

        return self

    # -----------------------------------------------------------------
    # serialization
    # -----------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "created_at": self.created_at.astimezone(KST or timezone.utc).isoformat(),
            "pipeline_step": self.pipeline_step,
            "action": self.action,
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "qty": self.qty,
            "risk_approved": self.risk_approved,
            "portfolio_adjusted": self.portfolio_adjusted,
            "reason": self.reason,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DecisionSnapshot":
        decision_id = _require_non_empty(
            "decision_id", _as_str(data.get("decision_id"))
        )

        snapshot = cls(
            decision_id=decision_id,
            created_at=_parse_dt(data.get("created_at")),
            pipeline_step=_require_non_empty(
                "pipeline_step", _as_str(data.get("pipeline_step"))
            ),
            action=_require_non_empty(
                "action", _as_str(data.get("action"))
            ).upper(),
            strategy_name=_as_str(data.get("strategy_name")),
            symbol=_as_str(data.get("symbol")),
            qty=_as_float(data.get("qty")),
            risk_approved=_as_bool(data.get("risk_approved")),
            portfolio_adjusted=_as_bool(data.get("portfolio_adjusted")),
            reason=_as_str(data.get("reason")),
            metadata=dict(data.get("metadata") or {}),
        )
        return snapshot.validate()
