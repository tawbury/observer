from __future__ import annotations

"""
provider_engine.py

Provider Engine: unifies REST and WebSocket providers for the Observer.

Responsibilities:
- Initialize and manage KIS REST + WebSocket providers (real/virtual)
- Provide simple lifecycle (start/stop) for websocket streaming
- Manage subscriptions with KIS slot limit (41)
- Expose health information
- Relay normalized streaming updates via a single callback

This module intentionally keeps a thin surface; higher-level components
like Track A/Track B collectors can depend on this engine.
"""

import asyncio
import logging
from typing import Callable, Iterable, Optional, Set, Dict, Any

from .kis import KISAuth, KISRestProvider, KISWebSocketProvider

logger = logging.getLogger(__name__)


class ProviderEngine:
    """Unified engine to access KIS REST and WebSocket providers."""

    MAX_WS_SLOTS = 41

    def __init__(
        self,
        auth: KISAuth,
        rest_provider: Optional[KISRestProvider] = None,
        ws_provider: Optional[KISWebSocketProvider] = None,
        is_virtual: bool = False,
    ) -> None:
        self.auth = auth
        self.rest: KISRestProvider = rest_provider or KISRestProvider(auth)
        self.ws: KISWebSocketProvider = ws_provider or KISWebSocketProvider(auth, is_virtual=is_virtual)
        self.is_virtual = is_virtual

        # Subscription state (mirrors ws provider but tracked here for convenience)
        self._subs: Set[str] = set()

        # External event relay callback (normalized dict from ws provider)
        self.on_price_update: Optional[Callable[[Dict[str, Any]], None]] = None

        # Wire callbacks
        self.ws.on_price_update = self._handle_ws_update
        self.ws.on_connection = lambda: logger.info("ProviderEngine: WS connected")
        self.ws.on_disconnection = lambda: logger.warning("ProviderEngine: WS disconnected")
        self.ws.on_error = lambda msg: logger.error("ProviderEngine WS error: %s", msg)

        logger.info("ProviderEngine initialized (mode=%s)", "virtual" if is_virtual else "real")

    # ---------------------------------------------------------------------
    # Lifecycle (WebSocket)
    # ---------------------------------------------------------------------
    async def start_stream(self) -> bool:
        """Start WebSocket streaming session."""
        return await self.ws.connect()

    async def stop_stream(self) -> None:
        """Stop WebSocket streaming session and clear local state."""
        await self.ws.close()
        self._subs.clear()

    # ---------------------------------------------------------------------
    # REST access (pass-through)
    # ---------------------------------------------------------------------
    async def fetch_current_price(self, symbol: str) -> Dict[str, Any]:
        return await self.rest.fetch_current_price(symbol)

    async def fetch_daily_prices(self, symbol: str, days: int = 30) -> Any:
        return await self.rest.fetch_daily_prices(symbol, days=days)
    
    async def fetch_stock_list(self, market: str = "ALL") -> list[str]:
        """Fetch all available stock symbols from provider."""
        return await self.rest.fetch_stock_list(market=market)

    # ---------------------------------------------------------------------
    # Subscriptions
    # ---------------------------------------------------------------------
    @property
    def subscription_count(self) -> int:
        return len(self._subs)

    @property
    def available_slots(self) -> int:
        return self.MAX_WS_SLOTS - self.subscription_count

    async def subscribe(self, symbol: str) -> bool:
        if symbol in self._subs:
            return True
        if self.subscription_count >= self.MAX_WS_SLOTS:
            logger.error("WS slot limit reached (%s)", self.MAX_WS_SLOTS)
            return False
        ok = await self.ws.subscribe(symbol)
        if ok:
            self._subs.add(symbol)
        return ok

    async def subscribe_many(self, symbols: Iterable[str], spacing_sec: float = 0.25) -> Dict[str, bool]:
        results: Dict[str, bool] = {}
        for sym in symbols:
            results[sym] = await self.subscribe(sym)
            await asyncio.sleep(spacing_sec)
        return results

    async def unsubscribe(self, symbol: str) -> bool:
        ok = await self.ws.unsubscribe(symbol)
        if ok:
            self._subs.discard(symbol)
        return ok

    async def unsubscribe_all(self) -> None:
        await self.ws.unsubscribe_all()
        self._subs.clear()

    # ---------------------------------------------------------------------
    # Events
    # ---------------------------------------------------------------------
    def _handle_ws_update(self, data: Dict[str, Any]) -> None:
        if self.on_price_update:
            self.on_price_update(data)

    # ---------------------------------------------------------------------
    # Health
    # ---------------------------------------------------------------------
    async def health(self) -> Dict[str, Any]:
        """Return a lightweight health snapshot for REST/WS/auth."""
        # Ensure we have a token (non-throwing)
        token_ok = True
        try:
            await self.auth.ensure_token()
        except Exception as e:
            logger.warning("Health: token ensure failed: %s", e)
            token_ok = False

        return {
            "mode": "virtual" if self.is_virtual else "real",
            "rest_ready": token_ok,
            "ws_connected": self.ws.is_connected,
            "ws_subscriptions": self.subscription_count,
            "ws_available_slots": self.available_slots,
        }

    # ---------------------------------------------------------------------
    # Close
    # ---------------------------------------------------------------------
    async def close(self) -> None:
        await self.stop_stream()
        await self.rest.close()
        await self.auth.close()
