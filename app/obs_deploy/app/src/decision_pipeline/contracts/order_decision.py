from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional


def _as_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)


def _as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s:
        return None
    return float(s)


def _require_non_empty(name: str, value: Optional[str]) -> str:
    if value is None or not str(value).strip():
        raise ValueError(f"{name} must be a non-empty string")
    return str(value).strip()


@dataclass(frozen=True, slots=True)
class OrderDecision:
    """
    OrderDecision

    Decide 단계의 '최종 주문 판단 결과' 계약.
    - Act(실행) 없음: 이 객체 자체는 주문을 발생시키지 않는다.
    - execution_stub(추후) 또는 테스트/로그에서 소비하는 형태로 고정.

    action:
      - BUY / SELL / NONE

    order_type:
      - MARKET / LIMIT / NONE
    """

    action: str
    symbol: Optional[str]
    qty: Optional[float]

    order_type: str = "NONE"
    limit_price: Optional[float] = None

    reason: Optional[str] = None

    def validate(self) -> "OrderDecision":
        action = self.action.upper().strip()
        if action not in {"BUY", "SELL", "NONE"}:
            raise ValueError(f"action must be BUY/SELL/NONE, got: {self.action!r}")

        order_type = self.order_type.upper().strip()
        if order_type not in {"MARKET", "LIMIT", "NONE"}:
            raise ValueError(f"order_type must be MARKET/LIMIT/NONE, got: {self.order_type!r}")

        # NONE action generally implies no symbol/qty; do not hard-enforce, but keep qty sane.
        if self.qty is not None and self.qty <= 0:
            raise ValueError(f"qty must be positive when provided, got: {self.qty!r}")

        if order_type == "LIMIT":
            if self.limit_price is None or self.limit_price <= 0:
                raise ValueError("LIMIT order_type requires positive limit_price")

        return self

    def to_dict(self) -> dict:
        return {
            "action": self.action.upper(),
            "symbol": self.symbol,
            "qty": self.qty,
            "order_type": self.order_type.upper(),
            "limit_price": self.limit_price,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "OrderDecision":
        action = _require_non_empty("action", _as_str(data.get("action"))).upper()
        order_type = _as_str(data.get("order_type") or "NONE").upper()

        obj = cls(
            action=action,
            symbol=_as_str(data.get("symbol")),
            qty=_as_float(data.get("qty")),
            order_type=order_type,
            limit_price=_as_float(data.get("limit_price")),
            reason=_as_str(data.get("reason")),
        )
        return obj.validate()

    @classmethod
    def none(cls, reason: Optional[str] = None) -> "OrderDecision":
        return cls(action="NONE", symbol=None, qty=None, order_type="NONE", limit_price=None, reason=reason).validate()
