# src/ops/observer/inputs/imarket_data_provider.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


MarketDataContract = Dict[str, Any]


class IMarketDataProvider(ABC):
    """
    IMarketDataProvider

    목적:
    - Observer에게 'MarketDataContract 1스냅샷'을 제공하는 입력 포트(규격)이다.
    - 데이터 출처(Mock / Replay / Live)는 Provider 구현체의 책임이다.

    규칙:
    - fetch()는 MarketDataContract(v1.0)을 반환하거나, 더 이상 데이터가 없으면 None을 반환한다.
    - Provider는 예외를 외부로 던지지 않는다(필요 시 내부에서 처리 후 None 반환).
    """

    @abstractmethod
    def fetch(self) -> Optional[MarketDataContract]:
        """Return one MarketDataContract snapshot, or None if unavailable/end-of-stream."""
        raise NotImplementedError

    def reset(self) -> None:
        """Optional: reset internal cursor/stream."""
        return None

    def close(self) -> None:
        """Optional: close underlying resources."""
        return None
