from __future__ import annotations

"""
kis_rest_provider.py

KIS REST API Provider for Market Data

Responsibilities:
- Fetch current price data (FHKST01010100)
- Fetch daily historical prices (FHKST01010400)
- Rate limiting (20 req/sec, 1000 req/min)
- Error handling and retry logic
- Data normalization to MarketDataContract

API Rate Limits:
- 20 requests per second
- 1,000 requests per minute
- 500,000 requests per day

Reference:
- backup/c0a7118/test_kis_api.py - API call patterns
- docs/dev/archi/kis_api_specification_v1.0.md - API details
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import aiohttp

from .kis_auth import KISAuth

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for KIS API.
    
    Limits:
    - 20 requests per second
    - 1,000 requests per minute
    """
    
    def __init__(self, requests_per_second: int = 20, requests_per_minute: int = 1000):
        self.rps_limit = requests_per_second
        self.rpm_limit = requests_per_minute
        
        # Token buckets
        self.second_tokens = requests_per_second
        self.minute_tokens = requests_per_minute
        
        # Last refill times
        self.last_second_refill = datetime.now(timezone.utc)
        self.last_minute_refill = datetime.now(timezone.utc)
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Wait until a request can be made within rate limits."""
        async with self._lock:
            while True:
                now = datetime.now(timezone.utc)
                
                # Refill second bucket
                if (now - self.last_second_refill).total_seconds() >= 1.0:
                    self.second_tokens = self.rps_limit
                    self.last_second_refill = now
                
                # Refill minute bucket
                if (now - self.last_minute_refill).total_seconds() >= 60.0:
                    self.minute_tokens = self.rpm_limit
                    self.last_minute_refill = now
                
                # Check if we can make a request
                if self.second_tokens > 0 and self.minute_tokens > 0:
                    self.second_tokens -= 1
                    self.minute_tokens -= 1
                    return
                
                # Wait a bit before retrying
                await asyncio.sleep(0.1)


class KISRestProvider:
    """
    KIS REST API Provider for market data.
    
    Features:
    - Current price queries
    - Daily historical price queries
    - Automatic rate limiting
    - Retry logic with exponential backoff
    - Data normalization
    """
    
    def __init__(
        self,
        auth: KISAuth,
        rate_limiter: Optional[RateLimiter] = None,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize KIS REST provider.
        
        Args:
            auth: KIS authentication manager
            rate_limiter: Rate limiter (creates default if not provided)
            max_retries: Maximum retry attempts on failure
        """
        self.auth = auth
        self.rate_limiter = rate_limiter or RateLimiter()
        self.max_retries = max_retries
        
        logger.info("KISRestProvider initialized")
    
    # ============================================================
    # Current Price API
    # ============================================================
    
    async def fetch_current_price(self, symbol: str) -> Dict:
        """
        Fetch current price data for a symbol.
        
        API: GET /uapi/domestic-stock/v1/quotations/inquire-price
        TR_ID: FHKST01010100
        
        Args:
            symbol: Stock symbol (6-digit code, e.g., "005930")
            
        Returns:
            Normalized market data contract
            
        Example:
            {
                "meta": {
                    "source": "kis",
                    "market": "kr_stocks",
                    "captured_at": "2026-01-22T10:30:00Z",
                    "schema_version": "1.0"
                },
                "instruments": [{
                    "symbol": "005930",
                    "timestamp": "2026-01-22T10:30:00Z",
                    "price": {
                        "open": 71000,
                        "high": 72000,
                        "low": 70500,
                        "close": 71500
                    },
                    "volume": 1000000,
                    "bid_price": 71400,
                    "ask_price": 71600
                }]
            }
        """
        await self.rate_limiter.acquire()
        await self.auth.ensure_token()
        
        url = f"{self.auth.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        
        # Query parameters
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # 시장 구분 (J: 주식)
            "FID_INPUT_ISCD": symbol,       # 종목 코드
        }
        
        # Headers with TR_ID for current price
        headers = self.auth.get_headers(tr_id="FHKST01010100")
        
        # Retry loop
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, params=params) as response:
                        data = await response.json()
                        
                        # Check for API errors
                        if data.get("rt_cd") != "0":
                            error_msg = data.get("msg1", "Unknown error")
                            
                            # Handle 401 Unauthorized
                            if response.status == 401:
                                logger.warning("Token expired, refreshing...")
                                await self.auth._refresh_token()
                                continue  # Retry with new token
                            
                            # Handle 429 Rate Limit
                            if response.status == 429:
                                wait_time = 2 ** attempt  # Exponential backoff
                                logger.warning(f"Rate limit exceeded, waiting {wait_time}s...")
                                await asyncio.sleep(wait_time)
                                continue
                            
                            raise RuntimeError(f"API error: {error_msg} (rt_cd: {data.get('rt_cd')})")
                        
                        # Normalize data
                        return self._normalize_current_price(data, symbol)
            
            except aiohttp.ClientError as e:
                logger.error(f"Network error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise RuntimeError(f"Failed after {self.max_retries} attempts") from e
            
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise
        
        raise RuntimeError("Max retries exceeded")
    
    def _normalize_current_price(self, data: Dict, symbol: str) -> Dict:
        """
        Normalize KIS current price response to MarketDataContract.
        
        Args:
            data: Raw KIS API response
            symbol: Stock symbol
            
        Returns:
            Normalized market data contract
        """
        output = data.get("output", {})
        
        # Extract price data
        current_price = int(output.get("stck_prpr", 0))      # 현재가
        open_price = int(output.get("stck_oprc", 0))         # 시가
        high_price = int(output.get("stck_hgpr", 0))         # 고가
        low_price = int(output.get("stck_lwpr", 0))          # 저가
        volume = int(output.get("acml_vol", 0))              # 누적 거래량
        
        # Bid/Ask data
        bid_price = int(output.get("bidp1", 0))              # 매수호가1
        ask_price = int(output.get("askp1", 0))              # 매도호가1
        
        # Timestamp
        now = datetime.now(timezone.utc)
        
        return {
            "meta": {
                "source": "kis",
                "market": "kr_stocks",
                "captured_at": now.isoformat(),
                "schema_version": "1.0",
            },
            "instruments": [
                {
                    "symbol": symbol,
                    "timestamp": now.isoformat(),
                    "price": {
                        "open": open_price,
                        "high": high_price,
                        "low": low_price,
                        "close": current_price,
                    },
                    "volume": volume,
                    "bid_price": bid_price if bid_price > 0 else None,
                    "ask_price": ask_price if ask_price > 0 else None,
                }
            ],
        }
    
    # ============================================================
    # Daily Historical Price API
    # ============================================================
    
    async def fetch_daily_prices(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 30,
    ) -> List[Dict]:
        """
        Fetch daily historical price data.
        
        API: GET /uapi/domestic-stock/v1/quotations/inquire-daily-price
        TR_ID: FHKST01010400
        
        Args:
            symbol: Stock symbol (6-digit code)
            start_date: Start date (YYYYMMDD format)
            end_date: End date (YYYYMMDD format)
            days: Number of days to fetch (if dates not provided)
            
        Returns:
            List of normalized daily data
        """
        await self.rate_limiter.acquire()
        await self.auth.ensure_token()
        
        # Calculate date range if not provided
        if not end_date:
            end_date = datetime.now(timezone.utc).strftime("%Y%m%d")
        if not start_date:
            start_dt = datetime.now(timezone.utc) - timedelta(days=days)
            start_date = start_dt.strftime("%Y%m%d")
        
        url = f"{self.auth.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-price"
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol,
            "FID_PERIOD_DIV_CODE": "D",     # D: 일봉
            "FID_ORG_ADJ_PRC": "0",         # 0: 수정주가 미반영
        }
        
        headers = self.auth.get_headers(tr_id="FHKST01010400")
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, params=params) as response:
                        data = await response.json()
                        
                        if data.get("rt_cd") != "0":
                            error_msg = data.get("msg1", "Unknown error")
                            
                            if response.status == 401:
                                logger.warning("Token expired, refreshing...")
                                await self.auth._refresh_token()
                                continue
                            
                            if response.status == 429:
                                wait_time = 2 ** attempt
                                logger.warning(f"Rate limit exceeded, waiting {wait_time}s...")
                                await asyncio.sleep(wait_time)
                                continue
                            
                            raise RuntimeError(f"API error: {error_msg}")
                        
                        # Normalize daily data
                        return self._normalize_daily_prices(data, symbol)
            
            except aiohttp.ClientError as e:
                logger.error(f"Network error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise RuntimeError(f"Failed after {self.max_retries} attempts") from e
        
        raise RuntimeError("Max retries exceeded")
    
    def _normalize_daily_prices(self, data: Dict, symbol: str) -> List[Dict]:
        """
        Normalize KIS daily price response to list of MarketDataContracts.
        
        Args:
            data: Raw KIS API response
            symbol: Stock symbol
            
        Returns:
            List of normalized daily data
        """
        output_list = data.get("output", [])
        results = []
        
        for item in output_list:
            date_str = item.get("stck_bsop_date", "")  # 영업일자
            open_price = int(item.get("stck_oprc", 0))
            high_price = int(item.get("stck_hgpr", 0))
            low_price = int(item.get("stck_lwpr", 0))
            close_price = int(item.get("stck_clpr", 0))
            volume = int(item.get("acml_vol", 0))
            
            # Convert date to ISO format
            if len(date_str) == 8:
                date_obj = datetime.strptime(date_str, "%Y%m%d")
                timestamp = date_obj.replace(tzinfo=timezone.utc).isoformat()
            else:
                timestamp = datetime.now(timezone.utc).isoformat()
            
            results.append({
                "meta": {
                    "source": "kis",
                    "market": "kr_stocks",
                    "captured_at": datetime.now(timezone.utc).isoformat(),
                    "schema_version": "1.0",
                },
                "instruments": [
                    {
                        "symbol": symbol,
                        "timestamp": timestamp,
                        "price": {
                            "open": open_price,
                            "high": high_price,
                            "low": low_price,
                            "close": close_price,
                        },
                        "volume": volume,
                    }
                ],
            })
        
        return results
    
    # ============================================================
    # Stock List APIs
    # ============================================================
    
    async def fetch_stock_list(self, market: str = "ALL") -> List[str]:
        """
        Fetch all stock symbols from KIS API.
        
        Note: KIS doesn't provide a direct stock list API, so we use a workaround:
        1. Try fetching from KIS sector/condition search API (if available)
        2. Fallback to fetching popular stocks and caching
        3. Ultimate fallback to predefined list
        
        Args:
            market: Market filter - "KOSPI", "KOSDAQ", or "ALL" (default)
            
        Returns:
            List of stock codes (6-digit strings)
        """
        await self.rate_limiter.acquire()
        await self.auth.ensure_token()
        
        # KIS API doesn't have a direct "get all stocks" endpoint
        # We'll use the condition search API with minimal filters
        # TR_ID: HHKST03900300 (조건검색)
        
        url = f"{self.auth.base_url}/uapi/domestic-stock/v1/quotations/inquire-search"
        headers = self.auth.get_headers(tr_id="HHKST03900300")
        
        # Query for all stocks with minimal filters
        params = {
            "FID_COND_MRKT_DIV_CODE": market if market in ["KOSPI", "KOSDAQ"] else "ALL",
            "FID_COND_SCR_DIV_CODE": "20171",  # 전체 종목
            "FID_INPUT_ISCD": "",
            "FID_DIV_CLS_CODE": "0",
            "FID_TRGT_CLS_CODE": "0",
            "FID_TRGT_EXLS_CLS_CODE": "0",
        }
        
        symbols = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    data = await response.json()
                    
                    # ✅ 강화된 로깅: KIS API 응답 상태 기록
                    logger.info(
                        f"KIS stock list API response | "
                        f"market={market} | "
                        f"http_status={response.status} | "
                        f"rt_cd={data.get('rt_cd', 'N/A')} | "
                        f"msg={data.get('msg1', data.get('msg', 'N/A'))} | "
                        f"output_count={len(data.get('output', []))}"
                    )
                    
                    if data.get("rt_cd") == "0":
                        output = data.get("output", [])
                        for item in output:
                            symbol = item.get("stck_shrn_iscd") or item.get("mksc_shrn_iscd")
                            if symbol:
                                symbols.append(symbol.strip())
                        
                        # ✅ 성공: API로부터 종목 조회됨
                        logger.info(f"✅ Successfully fetched {len(symbols)} symbols from KIS API (market={market})")
                        return symbols
                    else:
                        # ❌ API 에러 코드: rt_cd != "0"
                        logger.warning(
                            f"❌ KIS stock list API returned error | "
                            f"rt_cd={data.get('rt_cd')} | "
                            f"msg={data.get('msg1', 'N/A')} | "
                            f"market={market}"
                        )
        
        except Exception as e:
            # ❌ 네트워크/파싱 에러
            logger.warning(f"❌ Exception during stock list fetch: {type(e).__name__}: {e}")
        
        # 🔄 폴백: 캐시 파일 또는 내장 폴백으로 처리하도록
        logger.warning("Stock list fetch failed - fallback to file-based list or built-in symbols")
        return []
    
    # ============================================================
    # Lifecycle Management
    # ============================================================
    
    async def close(self) -> None:
        """Clean up resources."""
        await self.auth.close()
        logger.info("KISRestProvider closed")
