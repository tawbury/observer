"""
실시간 DB 저장 유틸리티

Track A/B collector에서 공통으로 사용하는 DB 저장 클래스.
JSONL 파일 저장과 병행하여 PostgreSQL에 실시간 저장.
"""
import asyncpg
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

log = logging.getLogger("RealtimeDBWriter")


class RealtimeDBWriter:
    """Track A/B 공통 DB 저장 클래스"""
    
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
        self._connected = False
    
    async def connect(self) -> bool:
        """DB 연결 풀 초기화"""
        try:
            # 환경변수에서 DB 설정 로드
            db_host = os.environ.get("DB_HOST", "postgres")
            db_user = os.environ.get("DB_USER", "postgres")
            db_password = os.environ.get("DB_PASSWORD")
            db_name = os.environ.get("DB_NAME", "observer")
            db_port = int(os.environ.get("DB_PORT", "5432"))
            
            # 비밀번호 미설정 시 경고 (프로덕션에서는 필수)
            if not db_password:
                log.warning("DB_PASSWORD not set, using default (not recommended for production)")
                db_password = "observer_db_pwd"
            
            self._pool = await asyncpg.create_pool(
                host=db_host,
                user=db_user,
                password=db_password,
                database=db_name,
                port=db_port,
                min_size=2,
                max_size=10
            )
            self._connected = True
            log.info("DB connection pool initialized (host=%s, db=%s)", db_host, db_name)
            return True
        except Exception as e:
            log.error(f"DB connection failed: {e}")
            self._connected = False
            return False
    
    async def close(self):
        """연결 풀 종료"""
        if self._pool:
            await self._pool.close()
            self._connected = False
            log.info("DB connection pool closed")
    
    @property
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self._connected and self._pool is not None
    
    async def save_scalp_tick(self, data: Dict[str, Any], session_id: str) -> bool:
        """
        Track B: scalp_ticks 테이블에 저장
        
        Args:
            data: WebSocket에서 받은 가격 데이터
            session_id: 세션 ID
            
        Returns:
            저장 성공 여부
        """
        if not self._pool:
            return False
        try:
            # timestamp 파싱
            ts_str = data.get("timestamp", "")
            if ts_str:
                event_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            else:
                event_time = datetime.now()
            
            # bid/ask 가격 추출
            bid_ask = data.get("bid_ask", {})
            bid_price = float(bid_ask.get("bid_price") or 0)
            ask_price = float(bid_ask.get("ask_price") or 0)
            
            # 현재가 추출
            price_data = data.get("price", {})
            last_price = float(price_data.get("current") or 0)
            
            # 거래량 추출
            volume_data = data.get("volume", {})
            volume = int(volume_data.get("accumulated") or 0)
            
            async with self._pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO scalp_ticks 
                    (symbol, event_time, bid_price, ask_price, last_price, volume, session_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                    data.get("symbol"),
                    event_time,
                    bid_price,
                    ask_price,
                    last_price,
                    volume,
                    session_id
                )
            return True
        except Exception as e:
            log.error(f"Failed to save scalp tick: {e}")
            return False
    
    async def save_swing_bar(self, record: Dict[str, Any], session_id: str) -> bool:
        """
        Track A: swing_bars_10m 테이블에 저장
        
        Args:
            record: collect_once()에서 생성한 레코드
            session_id: 세션 ID
            
        Returns:
            저장 성공 여부
        """
        if not self._pool:
            return False
        try:
            # timestamp 파싱
            ts_str = record.get("ts", "")
            if ts_str:
                bar_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            else:
                bar_time = datetime.now()
            
            # 가격 데이터 추출
            price = record.get("price", {})
            open_price = float(price.get("open") or 0)
            high_price = float(price.get("high") or 0)
            low_price = float(price.get("low") or 0)
            close_price = float(price.get("close") or 0)
            
            # 거래량
            volume = int(record.get("volume") or 0)
            
            # bid/ask (optional)
            bid_price = float(record.get("bid_price") or 0) if record.get("bid_price") else None
            ask_price = float(record.get("ask_price") or 0) if record.get("ask_price") else None
            
            async with self._pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO swing_bars_10m 
                    (symbol, bar_time, open, high, low, close, volume, 
                     bid_price, ask_price, session_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                    record.get("symbol"),
                    bar_time,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    volume,
                    bid_price,
                    ask_price,
                    session_id
                )
            return True
        except Exception as e:
            log.error(f"Failed to save swing bar: {e}")
            return False
