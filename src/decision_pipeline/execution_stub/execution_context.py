from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from shared.timezone import KST, now_kst

from .execution_mode import ExecutionMode


def _utcnow() -> datetime:
    return now_kst()


def _uuid_hex() -> str:
    return uuid4().hex


def _default_side_effect_policy() -> Dict[str, bool]:
    # Phase 8 기본값: side-effect 전부 차단
    return {
        "allow_file_write": False,
        "allow_network_call": False,
        "allow_sheet_write": False,
    }


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """
    ExecutionContext

    Phase 7의 최소 컨텍스트 계약을 Phase 8 스펙으로 확장한다.

    핵심 원칙:
    - 기존 필드 유지(호환성)
    - Phase 8 필드는 추가만 수행
    - Virtual/SIM/REAL이 동일 컨텍스트를 공유하도록 설계

    Phase 7 legacy:
    - request_id, created_at, broker, account, metadata
    Phase 8 additions:
    - mode, trading_enabled, kill_switch, dry_run
    - anomaly_flags, risk_limits
    - broker_id/account_id/market (확장 대비)
    - side_effect_policy (부작용 차단 기본)
    - correlation_id (추적용)
    """

    # ----------------------------
    # Phase 7 legacy fields
    # ----------------------------
    request_id: str = field(default_factory=_uuid_hex)
    created_at: datetime = field(default_factory=_utcnow)

    broker: Optional[str] = None
    account: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    # ----------------------------
    # Phase 8 fields (additive)
    # ----------------------------
    correlation_id: str = field(default_factory=_uuid_hex)

    mode: ExecutionMode = ExecutionMode.VIRTUAL
    trading_enabled: bool = True
    kill_switch: bool = False
    dry_run: bool = True  # Phase 8 기본: 절대 부작용 금지 성향

    anomaly_flags: List[str] = field(default_factory=list)
    risk_limits: Dict[str, float] = field(default_factory=dict)

    # 확장 대비 (SIM/REAL에서 사용 가능)
    broker_id: Optional[str] = None
    account_id: Optional[str] = None
    market: Optional[str] = None

    side_effect_policy: Dict[str, bool] = field(default_factory=_default_side_effect_policy)

    # ----------------------------
    # Compatibility / aliases
    # ----------------------------
    @property
    def run_id(self) -> str:
        # Phase 8 spec alias
        return self.request_id

    @property
    def generated_at(self) -> datetime:
        # Phase 8 spec alias
        return self.created_at

    @property
    def broker_resolved(self) -> Optional[str]:
        # prefer Phase 8 broker_id if provided, else legacy broker
        return self.broker_id or self.broker

    @property
    def account_resolved(self) -> Optional[str]:
        return self.account_id or self.account

    def to_dict(self) -> Dict[str, Any]:
        return {
            # legacy
            "request_id": self.request_id,
            "created_at": self.created_at.astimezone(KST or timezone.utc).isoformat(),
            "broker": self.broker,
            "account": self.account,
            "metadata": self.metadata,
            # phase 8
            "correlation_id": self.correlation_id,
            "mode": self.mode.value,
            "trading_enabled": self.trading_enabled,
            "kill_switch": self.kill_switch,
            "dry_run": self.dry_run,
            "anomaly_flags": list(self.anomaly_flags),
            "risk_limits": dict(self.risk_limits),
            "broker_id": self.broker_id,
            "account_id": self.account_id,
            "market": self.market,
            "side_effect_policy": dict(self.side_effect_policy),
        }
