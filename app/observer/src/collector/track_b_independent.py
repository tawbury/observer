"""
Track B Independent - 독립적인 실시간 스캐너 메인 컬렉터

Track A와 독립적인 실시간 스캐닝 및 스켈프 데이터 수집
KIS 공식 API 기반으로 구현
"""
from __future__ import annotations

import asyncio
import logging
from datetime import time
from typing import Optional

from shared.time_helpers import TimeAwareMixin
from shared.trading_hours import in_trading_hours
from collector.independent_track_b_scanner import IndependentTrackBScanner

log = logging.getLogger("TrackBIndependent")


class TrackBIndependent(TimeAwareMixin):
    """독립적인 Track B 컬렉터"""
    
    def __init__(self, market: str = "kr_stocks", max_slots: int = 41):
        self._tz_name = "Asia/Seoul"
        self.market = market
        self.max_slots = max_slots
        
        # 독립 스캐너
        self.scanner = IndependentTrackBScanner(market, max_slots)
        
        # 상태
        self._running = False
        self._on_error = None
    
    async def start(self) -> None:
        """독립 Track B 시작"""
        log.info("TrackBIndependent started (market=%s, max_slots=%d)", self.market, self.max_slots)
        self._running = True
        
        try:
            await self.scanner.start()
            
        except Exception as e:
            log.error(f"TrackBIndependent error: {e}", exc_info=True)
            if self._on_error:
                self._on_error(str(e))
    
    async def stop(self) -> None:
        """독립 Track B 중지"""
        log.info("TrackBIndependent stopping...")
        self._running = False
        await self.scanner.stop()
    
    def set_error_callback(self, callback: Optional[callable]) -> None:
        """에러 콜백 설정"""
        self._on_error = callback
    
    def get_stats(self) -> dict:
        """통계 정보"""
        return self.scanner.get_stats()


class TrackBIndependentConfig:
    """독립 Track B 설정"""
    
    def __init__(self):
        self.market = "kr_stocks"
        self.max_slots = 41
        self.trading_start = time(9, 30)
        self.trading_end = time(15, 30)
        self.scan_interval_seconds = 30
        self.volume_surge_threshold = 5.0
        self.volatility_threshold = 0.05
