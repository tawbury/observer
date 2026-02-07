# observer/inputs/mock_market_data_provider.py

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from shared.timezone import now_kst

from .imarket_data_provider import IMarketDataProvider, MarketDataContract


class MockMarketDataProvider(IMarketDataProvider):
    """
    MockMarketDataProvider

    - Phase 10 실행 검증용
    - MarketDataContract v1.0을 생성해 공급한다.
    """

    def __init__(self, symbol: str = "TEST001", market: str = "TEST") -> None:
        self._symbol = symbol
        self._market = market

    def fetch(self) -> Optional[MarketDataContract]:
        now = now_kst()
        o = round(random.uniform(100, 105), 2)
        h = round(o + random.uniform(0, 5), 2)
        l = round(o - random.uniform(0, 5), 2)
        c = round(random.uniform(l, h), 2)

        return {
            "meta": {
                "source": "mock",
                "market": self._market,
                "captured_at": now.isoformat(),
                "schema_version": "1.0",
            },
            "instruments": [
                {
                    "symbol": self._symbol,
                    "timestamp": now.isoformat(),
                    "price": {"open": o, "high": h, "low": l, "close": c},
                    "volume": random.randint(1_000, 10_000),
                }
            ],
        }
