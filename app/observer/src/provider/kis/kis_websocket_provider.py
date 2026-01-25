"""
kis_websocket_provider.py

KIS WebSocket Provider for Real-time Market Data Streaming
- WebSocket connection management
- Symbol subscription/unsubscription
- Real-time execution data reception and parsing
- EUC-KR message decoding
- Automatic reconnection logic

Phase 05, Task 5.3: KIS WebSocket Provider Implementation
"""

from __future__ import annotations

import asyncio
import logging
import os
import json
import ssl
from datetime import datetime, timezone
from typing import Callable, Optional, Dict, Any, Set
from dataclasses import dataclass, field
import websockets
from websockets.client import WebSocketClientProtocol

from .kis_auth import KISAuth

logger = logging.getLogger(__name__)


@dataclass
class MarketDataContract:
    """Normalized market data contract"""
    meta: Dict[str, Any]
    instruments: list[Dict[str, Any]] = field(default_factory=list)


class WebSocketReconnector:
    """WebSocket reconnection manager with exponential backoff"""
    
    def __init__(self, max_retries: int = 5, initial_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.retry_count = 0
        
    def get_delay(self) -> float:
        """Calculate exponential backoff delay"""
        delay = min(self.initial_delay * (2 ** self.retry_count), self.max_delay)
        return delay
    
    def increment(self) -> None:
        """Increment retry counter"""
        self.retry_count += 1
    
    def reset(self) -> None:
        """Reset retry counter on successful connection"""
        self.retry_count = 0
    
    def should_retry(self) -> bool:
        """Check if should attempt reconnection"""
        return self.retry_count < self.max_retries


class KISWebSocketProvider:
    """
    KIS WebSocket Provider for real-time market data streaming
    
    Supports:
    - Up to 41 simultaneous symbol subscriptions
    - Real-time execution data (H0STCNT0)
    - Automatic reconnection with exponential backoff
    - Message encoding/decoding (EUC-KR format)
    - Event-based data delivery
    """
    
    # WebSocket endpoint and limits
    WEBSOCKET_URL = "wss://openapi.koreainvestment.com:9443/websocket"
    MAX_SUBSCRIPTIONS = 41  # KIS API limit
    
    # Message codes for KIS API
    MSG_SUBSCRIBE = "H0STCNT0"      # Real-time execution data subscription
    MSG_UNSUBSCRIBE = "H0STCNT9"    # Unsubscribe
    MSG_LOGIN = "CSPAT00600001"      # Login
    
    def __init__(self, auth: KISAuth, is_virtual: bool = False):
        """
        Initialize KIS WebSocket Provider
        
        Args:
            auth: KISAuth instance for authentication
            is_virtual: Use simulation/virtual mode
        """
        self.auth = auth
        self.is_virtual = is_virtual
        # Choose WebSocket endpoint
        # CRITICAL FIX: Correct endpoint mapping per KIS official docs
        # Real: ws://ops.koreainvestment.com:21000
        # Virtual: ws://ops.koreainvestment.com:31000
        env_ws = os.getenv("KIS_WEBSOCKET_URL")
        default_candidates = (
            [
                "ws://ops.koreainvestment.com:31000",  # Virtual endpoint
                self.WEBSOCKET_URL,
            ]
            if is_virtual
            else [
                "ws://ops.koreainvestment.com:21000",  # Real endpoint
                self.WEBSOCKET_URL,
            ]
        )
        self.websocket_candidates = [env_ws] if env_ws else []
        self.websocket_candidates.extend(default_candidates)
        # Track the last attempted URL for visibility
        self.websocket_url = self.websocket_candidates[0]
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.reconnector = WebSocketReconnector()
        
        # Subscription management
        self.subscribed_symbols: Set[str] = set()
        self.pending_symbols: Set[str] = set()
        
        # Connection state
        self.is_connected = False
        self.connection_lock = asyncio.Lock()
        
        # Event callbacks
        self.on_price_update: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_connection: Optional[Callable[[], None]] = None
        self.on_disconnection: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        
        # Background tasks
        self._receive_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None
    
    async def connect(self) -> bool:
        """
        Establish WebSocket connection to KIS
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        async with self.connection_lock:
            if self.is_connected:
                logger.info("Already connected to KIS WebSocket")
                return True
            
            try:
                # Ensure valid token and approval key
                token = await self.auth.ensure_token()
                approval_key = await self.auth.get_approval_key()

                last_error: Optional[Exception] = None
                for ws_url in self.websocket_candidates:
                    self.websocket_url = ws_url
                    try:
                        logger.info("Connecting to KIS WebSocket: %s", ws_url)
                        ssl_required = None if ws_url.startswith("ws://") else True
                        self.websocket = await websockets.connect(
                            ws_url,
                            ssl=ssl_required,
                            ping_interval=10,  # Send ping every 10 seconds
                            ping_timeout=5,
                            close_timeout=5,
                        )
                        break
                    except Exception as conn_err:
                        last_error = conn_err
                        logger.warning("WebSocket attempt failed for %s: %s", ws_url, conn_err)
                        continue

                if not self.websocket:
                    raise last_error or RuntimeError("WebSocket connection failed")
                
                logger.info("✅ WebSocket connected successfully")
                self.is_connected = True
                self.reconnector.reset()
                
                # Send login message
                await self._send_login()
                
                # Start receiving messages
                self._receive_task = asyncio.create_task(self._receive_messages())
                
                # Trigger connection callback
                if self.on_connection:
                    self.on_connection()
                
                # Resubscribe to previous symbols
                if self.pending_symbols or self.subscribed_symbols:
                    await self._resubscribe()
                
                return True
                
            except Exception as e:
                logger.error(f"❌ WebSocket connection failed: {e}")
                self.is_connected = False
                if self.on_error:
                    self.on_error(f"Connection failed: {str(e)}")
                return False
    
    async def disconnect(self) -> None:
        """Disconnect from WebSocket"""
        async with self.connection_lock:
            if not self.is_connected:
                return
            
            try:
                logger.info("Disconnecting from KIS WebSocket...")
                
                # Cancel receiving task
                if self._receive_task and not self._receive_task.done():
                    self._receive_task.cancel()
                    try:
                        await self._receive_task
                    except asyncio.CancelledError:
                        pass
                
                # Close WebSocket
                if self.websocket:
                    await self.websocket.close()
                    self.websocket = None
                
                self.is_connected = False
                self.subscribed_symbols.clear()
                self.pending_symbols.clear()
                
                logger.info("✅ WebSocket disconnected")
                
                if self.on_disconnection:
                    self.on_disconnection()
                    
            except Exception as e:
                logger.error(f"❌ Error during disconnection: {e}")
    
    async def subscribe(self, symbol: str) -> bool:
        """
        Subscribe to real-time data for a symbol
        
        Args:
            symbol: Stock symbol (e.g., "005930" for Samsung)
        
        Returns:
            bool: True if subscription successful
        """
        if len(self.subscribed_symbols) >= self.MAX_SUBSCRIPTIONS:
            logger.error(f"Cannot subscribe: Maximum {self.MAX_SUBSCRIPTIONS} subscriptions reached")
            return False
        
        if symbol in self.subscribed_symbols:
            logger.debug(f"Already subscribed to {symbol}")
            return True
        
        if not self.is_connected:
            logger.warning(f"Not connected, adding {symbol} to pending subscriptions")
            self.pending_symbols.add(symbol)
            return False
        
        try:
            await self._send_subscription_request(symbol)
            self.subscribed_symbols.add(symbol)
            self.pending_symbols.discard(symbol)
            logger.info(f"✅ Subscribed to {symbol}")
            return True
        except Exception as e:
            logger.error(f"❌ Subscription failed for {symbol}: {e}")
            return False
    
    async def unsubscribe(self, symbol: str) -> bool:
        """
        Unsubscribe from real-time data for a symbol
        
        Args:
            symbol: Stock symbol
        
        Returns:
            bool: True if unsubscription successful
        """
        if symbol not in self.subscribed_symbols:
            logger.debug(f"Not subscribed to {symbol}")
            return True
        
        if not self.is_connected:
            self.subscribed_symbols.discard(symbol)
            self.pending_symbols.discard(symbol)
            return True
        
        try:
            await self._send_unsubscription_request(symbol)
            self.subscribed_symbols.discard(symbol)
            self.pending_symbols.discard(symbol)
            logger.info(f"✅ Unsubscribed from {symbol}")
            return True
        except Exception as e:
            logger.error(f"❌ Unsubscription failed for {symbol}: {e}")
            return False
    
    async def unsubscribe_all(self) -> None:
        """Unsubscribe from all symbols"""
        symbols = list(self.subscribed_symbols)
        for symbol in symbols:
            await self.unsubscribe(symbol)
    
    async def _send_login(self) -> None:
        """Optional: KIS may not require explicit login over WS."""
        logger.debug("Skipping explicit WebSocket login per docs")
    
    async def _send_subscription_request(self, symbol: str) -> None:
        """Send subscription request for a symbol (per official docs)"""
        # Get approval key (required by KIS WebSocket API)
        approval_key = await self.auth.get_approval_key()
        
        subscription_msg = {
            "header": {
                "approval_key": approval_key,  # ← CRITICAL: Use approval_key, not appkey/appsecret
                "custtype": "P",
                "tr_type": "1",
                "content-type": "utf-8",
            },
            "body": {
                "input": {
                    "tr_id": self.MSG_SUBSCRIBE,
                    "tr_key": symbol,
                }
            }
        }
        await self._send_message(json.dumps(subscription_msg))
        logger.debug(f"📤 Subscription request sent for {symbol}")
    
    async def _send_unsubscription_request(self, symbol: str) -> None:
        """Send unsubscription request for a symbol (per official docs)"""
        # Get approval key (required by KIS WebSocket API)
        approval_key = await self.auth.get_approval_key()
        
        unsubscription_msg = {
            "header": {
                "approval_key": approval_key,  # ← CRITICAL: Use approval_key
                "custtype": "P",
                "tr_type": "0",  # ← CRITICAL: "0" for unsubscribe, NOT "1" (which is subscribe)
                "content-type": "utf-8",
            },
            "body": {
                "input": {
                    "tr_id": self.MSG_SUBSCRIBE,  # Use H0STCNT0 (same as subscribe)
                    "tr_key": symbol,
                }
            }
        }
        await self._send_message(json.dumps(unsubscription_msg))
        logger.debug(f"📤 Unsubscription request sent for {symbol}")
    
    async def _send_message(self, message: str) -> None:
        """Send message through WebSocket (UTF-8 text)"""
        if not self.websocket or not self.is_connected:
            raise RuntimeError("WebSocket not connected")
        try:
            await self.websocket.send(message)
        except Exception as e:
            logger.error(f"❌ Error sending message: {e}")
            raise
    
    async def _receive_messages(self) -> None:
        """Background task: receive and process WebSocket messages"""
        try:
            if not self.websocket:
                raise RuntimeError("WebSocket not initialized")
            
            async for message in self.websocket:
                try:
                    await self._process_message(message)
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
                    if self.on_error:
                        self.on_error(f"Message processing error: {str(e)}")
        
        except asyncio.CancelledError:
            logger.debug("📥 Message receive task cancelled")
        except Exception as e:
            logger.error(f"❌ WebSocket receive error: {e}")
            self.is_connected = False
            if self.on_error:
                self.on_error(f"WebSocket error: {str(e)}")
            if self.on_disconnection:
                self.on_disconnection()
            
            # Trigger reconnection
            await self._schedule_reconnection()
    
    async def _process_message(self, raw_message: bytes | str) -> None:
        """
        Process received WebSocket message
        
        KIS sends two types of messages:
        1. System/JSON: {"header": {...}, "body": {...}}
        2. Real-time/Pipe-delimited: 0|H0STCNT0|count|data^data^...
        
        Args:
            raw_message: Raw message bytes from WebSocket
        """
        try:
            # Decode message (ws client may yield str already)
            if isinstance(raw_message, bytes):
                message_str = raw_message.decode('euc-kr')
            else:
                message_str = raw_message
            
            # CRITICAL FIX: Handle PINGPONG for keep-alive
            if message_str == "PINGPONG":
                logger.debug("📍 PINGPONG received, echoing back...")
                await self._send_message("PINGPONG")
                return
            
            # CRITICAL FIX: Check message type - pipe-delimited vs JSON
            if message_str.startswith('0') or message_str.startswith('1'):
                # Real-time data: pipe-delimited format
                await self._process_realtime_data(message_str)
            else:
                # System message or subscription response: JSON format
                message_data = json.loads(message_str)
                
                # Extract price data (for JSON responses, e.g., H0UNASP0 bid/ask)
                if "body" in message_data and isinstance(message_data["body"], dict):
                    price_data = self._normalize_price_data(message_data)
                    
                    if price_data:
                        logger.debug(f"📊 Price update: {price_data['symbol']}")
                        
                        # Trigger callback
                        if self.on_price_update:
                            self.on_price_update(price_data)
        
        except UnicodeDecodeError as e:
            logger.debug(f"⚠️ Could not decode message as EUC-KR: {e}")
            # Some system messages might not be decodable
        except json.JSONDecodeError as e:
            logger.debug(f"⚠️ Could not parse message as JSON: {e}")
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
    
    def _normalize_price_data(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Normalize WebSocket message to standard price data format
        
        Args:
            message: Raw message from WebSocket
        
        Returns:
            Normalized price data or None if invalid
        """
        try:
            body = message.get("body", {})
            if not body:
                return None
            
            # Extract key fields from KIS WebSocket response
            symbol = body.get("tr_key", "")
            if not symbol:
                return None
            
            # Real-time execution data fields
            price_data = {
                "symbol": symbol,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "price": {
                    "close": int(body.get("stck_prpr", 0)),  # Current price
                    "open": int(body.get("stck_oprc", 0)),   # Open price
                    "high": int(body.get("stck_hgpr", 0)),   # High price
                    "low": int(body.get("stck_lwpr", 0)),    # Low price
                },
                "volume": int(body.get("acml_vol", 0)),       # Accumulated volume
                "bid_price": int(body.get("bidp", 0)),        # Bid price
                "ask_price": int(body.get("askp", 0)),        # Ask price
                "trade_count": int(body.get("acml_tr_pbut", 0)),  # Trade count
                "source": "kis_websocket"
            }
            
            return price_data
        
        except Exception as e:
            logger.error(f"❌ Error normalizing price data: {e}")
            return None
    
    async def _process_realtime_data(self, data_str: str) -> None:
        """
        CRITICAL FIX: Process pipe-delimited real-time data (H0STCNT0)
        
        Format: 0|H0STCNT0|data_count|record1^record2^...
        Example: 0|H0STCNT0|2|005930|123000|...|051910|156000|...|
        
        Args:
            data_str: Pipe-delimited data string
        """
        try:
            parts = data_str.split('|')
            if len(parts) < 4:
                logger.warning(f"⚠️ Invalid data format: {data_str[:50]}")
                return
            
            msg_type = parts[0]      # '0' for real-time, '1' for notification
            tr_id = parts[1]         # 'H0STCNT0' or other
            try:
                data_cnt = int(parts[2])  # Number of records
            except ValueError:
                logger.warning(f"⚠️ Invalid data count in: {data_str[:50]}")
                return
            
            payload = parts[3] if len(parts) > 3 else ""
            
            # Only process execution data (H0STCNT0)
            if tr_id != "H0STCNT0":
                logger.debug(f"Ignoring non-execution data: {tr_id}")
                return
            
            # Parse records (separated by '^')
            if not payload:
                logger.debug("Empty payload for H0STCNT0")
                return
            
            records = payload.split('^')
            logger.debug(f"📊 Processing {len(records)} records (count={data_cnt})")
            
            for i, record in enumerate(records):
                if i >= data_cnt:
                    break
                
                if not record.strip():
                    continue
                
                # Parse individual fields (pipe-separated within record)
                fields = record.split('|')
                if len(fields) >= 3:
                    price_data = self._parse_execution_record(fields)
                    if price_data and self.on_price_update:
                        logger.debug(f"📡 Real-time tick: {price_data['symbol']} @ {price_data['price']['close']}")
                        self.on_price_update(price_data)
        
        except Exception as e:
            logger.error(f"❌ Error processing real-time data: {e}")
    
    def _parse_execution_record(self, fields: list[str]) -> Optional[Dict[str, Any]]:
        """
        Parse H0STCNT0 execution record fields
        
        H0STCNT0 fields (pipe-delimited):
        0: 시장구분 (market)
        1: 종목코드 (symbol)
        2: 체결시간 (execution time HHMMSS)
        3: 현재가 (current price)
        4: 전일대비부호 (sign)
        5: 전일대비 (change amount)
        6: 등락율 (change rate)
        7: 시가 (open price)
        8: 고가 (high price)
        9: 저가 (low price)
        10: 누적체결량 (accumulated volume)
        11: 누적거래대금 (accumulated trade value)
        12: 매도호가 (ask price)
        13: 매수호가 (bid price)
        14: (remaining fields...)
        
        Args:
            fields: Pipe-delimited fields from execution record
        
        Returns:
            Normalized price data dict or None if invalid
        """
        try:
            if len(fields) < 11:
                return None
            
            symbol = fields[1]  # Symbol code
            
            return {
                "symbol": symbol,
                "execution_time": fields[2],  # HHMMSS
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "price": {
                    "close": int(fields[3] or 0),    # Current price
                    "change_amount": int(fields[5] or 0),
                    "change_rate": float(fields[6] or 0),
                    "open": int(fields[7] or 0),    # Open price
                    "high": int(fields[8] or 0),    # High price
                    "low": int(fields[9] or 0),     # Low price
                },
                "volume": {
                    "accumulated": int(fields[10] or 0),  # Accumulated volume
                    "trade_value": int(fields[11] or 0) if len(fields) > 11 else 0,
                },
                "bid_ask": {
                    "ask_price": int(fields[12] or 0) if len(fields) > 12 else 0,  # Ask/Sell
                    "bid_price": int(fields[13] or 0) if len(fields) > 13 else 0,  # Bid/Buy
                },
                "source": "kis_websocket"
            }
        
        except (ValueError, IndexError) as e:
            logger.debug(f"⚠️ Error parsing execution record: {e}")
            return None
    
    async def _resubscribe(self) -> None:
        """Resubscribe to all symbols after reconnection"""
        symbols = list(self.subscribed_symbols | self.pending_symbols)
        self.subscribed_symbols.clear()
        self.pending_symbols.clear()
        
        for symbol in symbols:
            await asyncio.sleep(0.1)  # Small delay between subscriptions
            await self.subscribe(symbol)
    
    async def _schedule_reconnection(self) -> None:
        """Schedule automatic reconnection attempt"""
        if not self.reconnector.should_retry():
            logger.error("❌ Maximum reconnection attempts exceeded")
            return
        
        delay = self.reconnector.get_delay()
        self.reconnector.increment()
        
        logger.info(f"⏳ Reconnecting in {delay:.1f} seconds... (attempt {self.reconnector.retry_count}/{self.reconnector.max_retries})")
        await asyncio.sleep(delay)
        
        await self.connect()
    
    async def close(self) -> None:
        """Close provider and cleanup resources"""
        logger.info("Closing KIS WebSocket Provider...")
        
        # Cancel pending tasks
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
        
        # Disconnect
        await self.disconnect()
        
        logger.info("✅ KIS WebSocket Provider closed")
    
    @property
    def subscription_count(self) -> int:
        """Get current number of subscriptions"""
        return len(self.subscribed_symbols)
    
    @property
    def available_slots(self) -> int:
        """Get number of available subscription slots"""
        return self.MAX_SUBSCRIPTIONS - self.subscription_count
