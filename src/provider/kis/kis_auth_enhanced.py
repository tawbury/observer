"""
Enhanced KIS Auth - KIS 공식 API 기반 인증 개선

독립적인 Track B 스캐너를 위한 향상된 인증 모듈
참고: https://github.com/koreainvestment/open-trading-api
"""
from __future__ import annotations

import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from zoneinfo import ZoneInfo

log = logging.getLogger("KISAuthEnhanced")


class KISAuthEnhanced:
    """향상된 KIS 인증 클래스"""
    
    def __init__(self, app_key: str, app_secret: str, real: bool = False):
        self.app_key = app_key
        self.app_secret = app_secret
        self.real = real
        
        # API 엔드포인트
        self.base_url = "https://openapivts.koreainvestment.com:9443" if real else "https://openapivts.koreainvestment.com:9443"
        
        # 토큰 캐시
        self._access_token = None
        self._token_expires_at = None
        self._websocket_approval_key = None
        
    async def get_access_token(self) -> str:
        """접근 토큰 발급"""
        try:
            # 토큰 유효성 체크
            if self._is_token_valid():
                return self._access_token
            
            # 새 토큰 발급
            url = f"{self.base_url}/oauth2/tokenP"
            headers = {
                "Content-Type": "application/json"
            }
            data = {
                "grant_type": "client_credentials",
                "client_id": self.app_key,
                "client_secret": self.app_secret
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            token_data = response.json()
            
            self._access_token = token_data["access_token"]
            expires_in = token_data["expires_in"]
            self._token_expires_at = datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(seconds=expires_in - 60)  # 1분 여유
            
            log.info("Access token obtained successfully")
            return self._access_token
            
        except Exception as e:
            log.error(f"Error getting access token: {e}", exc_info=True)
            raise
    
    async def get_websocket_approval_key(self) -> str:
        """WebSocket 승인키 발급"""
        try:
            if self._websocket_approval_key:
                return self._websocket_approval_key
            
            # 접근 토큰 필요
            token = await self.get_access_token()
            
            # WebSocket 승인키 발급
            url = f"{self.base_url}/oauth2/ApprovalP"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
            data = {
                "grant_type": "client_credentials",
                "client_id": self.app_key,
                "client_secret": self.app_secret
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            approval_data = response.json()
            self._websocket_approval_key = approval_data["approval_key"]
            
            log.info("WebSocket approval key obtained successfully")
            return self._websocket_approval_key
            
        except Exception as e:
            log.error(f"Error getting WebSocket approval key: {e}", exc_info=True)
            raise
    
    def _is_token_valid(self) -> bool:
        """토큰 유효성 체크"""
        if not self._access_token or not self._token_expires_at:
            return False
        
        return datetime.now(ZoneInfo("Asia/Seoul")) < self._token_expires_at
    
    async def get_current_price(self, symbol: str) -> Dict[str, Any]:
        """현재가 조회"""
        try:
            token = await self.get_access_token()
            
            url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
                "tr_cd": "F",
                "custtype": "P"
            }
            params = {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": symbol
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            log.error(f"Error getting current price for {symbol}: {e}", exc_info=True)
            raise
    
    def get_domain(self) -> str:
        """도메인 정보"""
        return "real" if self.real else "virtual"
