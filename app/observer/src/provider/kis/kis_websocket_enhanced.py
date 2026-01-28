"""
Enhanced KIS WebSocket Provider - KIS 공식 API 기반 개선

독립적인 Track B 스캐너를 위한 향상된 WebSocket 프로바이더
참고: https://github.com/koreainvestment/open-trading-api
"""
from __future__ import annotations

import asyncio
import json
import logging
import websockets
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from zoneinfo import ZoneInfo

from provider.kis.kis_auth import KISAuth

log = logging.getLogger("KISWebSocketEnhanced")


class KISWebSocketEnhanced:
    """향상된 KIS WebSocket 프로바이더"""
    
    def __init__(self, auth: KISAuth):
        self.auth = auth
        self.websocket = None
        self.price_callbacks: List[Callable] = []
        self.subscribed_symbols: Dict[str, bool] = {}
        self._running = False
        
        # KIS WebSocket 엔드포인트
        self.ws_url = "ws://ops.koreainvestment.com:21000"
        
    async def connect(self) -> None:
        """WebSocket 연결"""
        try:
            # WebSocket 승인키 발급
            approval_key = await self.auth.get_websocket_approval_key()
            
            # WebSocket 연결
            self.websocket = await websockets.connect(
                self.ws_url,
                extra_headers={
                    "Authorization": f"Bearer {approval_key}",
                    "Content-Type": "application/json"
                }
            )
            
            self._running = True
            
            # 메시지 수신 루프 시작
            asyncio.create_task(self._message_loop())
            
            log.info("✅ Enhanced WebSocket connected successfully")
            
        except Exception as e:
            log.error(f"WebSocket connection error: {e}", exc_info=True)
            raise
    
    async def disconnect(self) -> None:
        """WebSocket 연결 종료"""
        self._running = False
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        log.info("WebSocket disconnected")
    
    def register_price_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """가격 업데이트 콜백 등록"""
        self.price_callbacks.append(callback)
        log.info("Price update callback registered")
    
    async def subscribe(self, symbol: str) -> None:
        """종목 구독"""
        try:
            if not self.websocket:
                log.warning("WebSocket not connected")
                return
            
            # KIS WebSocket 구독 요청 형식
            subscribe_request = {
                "header": {
                    "approval_key": await self.auth.get_websocket_approval_key(),
                    "tr_id": "H0STCNT0"
                },
                "body": {
                    "tr_key": symbol
                }
            }
            
            await self.websocket.send(json.dumps(subscribe_request))
            self.subscribed_symbols[symbol] = True
            log.debug(f"Subscribed to {symbol}")
            
        except Exception as e:
            log.error(f"Error subscribing to {symbol}: {e}", exc_info=True)
    
    async def unsubscribe(self, symbol: str) -> None:
        """종목 구독 해제"""
        try:
            if not self.websocket:
                log.warning("WebSocket not connected")
                return
            
            # KIS WebSocket 구독 해제 요청 형식
            unsubscribe_request = {
                "header": {
                    "approval_key": await self.auth.get_websocket_approval_key(),
                    "tr_id": "H0STCNT0"
                },
                "body": {
                    "tr_key": symbol
                }
            }
            
            await self.websocket.send(json.dumps(unsubscribe_request))
            self.subscribed_symbols[symbol] = False
            log.debug(f"Unsubscribed from {symbol}")
            
        except Exception as e:
            log.error(f"Error unsubscribing from {symbol}: {e}", exc_info=True)
    
    async def _message_loop(self) -> None:
        """메시지 수신 루프"""
        try:
            while self._running and self.websocket:
                message = await self.websocket.recv()
                await self._process_message(message)
                
        except websockets.exceptions.ConnectionClosed:
            log.info("WebSocket connection closed")
        except Exception as e:
            log.error(f"Error in message loop: {e}", exc_info=True)
    
    async def _process_message(self, message: str) -> None:
        """메시지 처리"""
        try:
            data = json.loads(message)
            
            # 응답 메시지 처리
            if "header" in data and "body" in data:
                header = data["header"]
                body = data["body"]
                
                # 구독 응답 처리
                if header.get("tr_cd") == "0":
                    tr_key = body.get("tr_key")
                    if tr_key:
                        log.debug(f"Subscription confirmed for {tr_key}")
                
                # 실시간 가격 데이터 처리
                elif header.get("tr_cd") == "1":
                    await self._handle_price_data(body)
                
                # 에러 처리
                elif header.get("tr_cd") in ["2", "3"]:
                    log.warning(f"WebSocket error: {data}")
                    
        except Exception as e:
            log.error(f"Error processing message: {e}", exc_info=True)
    
    async def _handle_price_data(self, body: Dict[str, Any]) -> None:
        """실시간 가격 데이터 처리"""
        try:
            # KIS WebSocket 가격 데이터 파싱
            symbol = body.get("tr_key")
            if not symbol:
                return
            
            # 가격 데이터 정규화
            price_data = {
                "symbol": symbol,
                "price": float(body.get("stck_prpr", 0)),
                "volume": int(body.get("acml_vol", 0)),
                "bid_price": float(body.get("bidp", 0)),
                "ask_price": float(body.get("askp", 0)),
                "high": float(body.get("stck_hgpr", 0)),
                "low": float(body.get("stck_lwpr", 0)),
                "open": float(body.get("stck_oprc", 0)),
                "timestamp": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
                "change": float(body.get("prdy_vrss", 0)),
                "change_rate": float(body.get("prdy_ctrt", 0)),
            }
            
            # 콜백 호출
            for callback in self.price_callbacks:
                try:
                    callback(symbol, price_data)
                except Exception as e:
                    log.error(f"Error in price callback: {e}", exc_info=True)
                    
        except Exception as e:
            log.error(f"Error handling price data: {e}", exc_info=True)
    
    def get_subscribed_symbols(self) -> List[str]:
        """구독된 종목 목록"""
        return [symbol for symbol, subscribed in self.subscribed_symbols.items() if subscribed]
    
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self._running and self.websocket is not None
