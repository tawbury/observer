from __future__ import annotations

"""
kis_rest_provider.py

KIS REST API Provider for Market Data

Responsibilities:
- Fetch current price data (FHKST01010100)
- Fetch daily historical prices (FHKST01010400)
- Rate limiting with conservative settings (15 req/sec, 900 req/min)
- Error handling and retry logic with exponential backoff
- Data normalization to MarketDataContract

Official KIS API Rate Limits (2023.01.11):
- REST API: 20 requests/sec, 1,000 requests/min, 500,000 requests/day
- Reference: https://apiportal.koreainvestment.com/community-notice
- GitHub samples: https://github.com/koreainvestment/open-trading-api

Implementation Notes:
- Using conservative limits (15/sec, 900/min) to prevent burst traffic errors
- Token bucket algorithm with asyncio locks for concurrency
- Exponential backoff on rate limit errors (429)
- Automatic token refresh on 401 errors

Reference:
- backup/c0a7118/test_kis_api.py - API call patterns
- docs/dev/archi/kis_api_specification_v1.0.md - API details
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional
import aiohttp

from .kis_auth import KISAuth

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for KIS API.
    
    Official KIS API Rate Limits (as of 2023.01.11):
    - REST API: 20 requests/sec, 1,000 requests/min, 500,000 requests/day
    - Reference: https://apiportal.koreainvestment.com/community-notice
    
    Conservative Settings (to prevent rate limit errors):
    - Using 15 req/sec (75% of limit) to account for burst traffic
    - Using 900 req/min (90% of limit) for safety margin
    """
    
    def __init__(self, requests_per_second: int = 5, requests_per_minute: int = 900):
        """
        Initialize rate limiter with conservative defaults.
        
        Args:
            requests_per_second: Max requests per second (default: 15, official limit: 20)
            requests_per_minute: Max requests per minute (default: 900, official limit: 1000)
        """
        self.rps_limit = requests_per_second
        self.rpm_limit = requests_per_minute
        
        # Token buckets
        self.second_tokens = requests_per_second
        self.minute_tokens = requests_per_minute
        
        # Last refill times
        from zoneinfo import ZoneInfo
        self.last_second_refill = datetime.now(ZoneInfo("Asia/Seoul"))
        self.last_minute_refill = datetime.now(ZoneInfo("Asia/Seoul"))
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        logger.info(f"RateLimiter initialized: {requests_per_second} req/sec, {requests_per_minute} req/min")
    
    async def acquire(self) -> None:
        """Wait until a request can be made within rate limits."""
        async with self._lock:
            while True:
                from zoneinfo import ZoneInfo
                now = datetime.now(ZoneInfo("Asia/Seoul"))
                
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
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol,
        }
        
        # Session is managed by KISAuth singleton
        session = await self.auth.get_session()
        
        # Retry loop
        for attempt in range(self.max_retries):
            try:
                # HEADERS MUST BE GENERATED INSIDE THE LOOP
                # This ensures that if a 401 refresh happens, the next retry uses the NEW token.
                headers = self.auth.get_headers(tr_id="FHKST01010100")
                
                async with session.get(url, headers=headers, params=params) as response:
                    data = await response.json()
                    
                    # Check for API errors
                    if data.get("rt_cd") != "0":
                        error_msg = data.get("msg1", "Unknown error")
                        rt_cd = data.get("rt_cd")
                        
                        # Handle 401 Unauthorized
                        if response.status == 401:
                            logger.warning(f"401 Unauthorized for {symbol}, triggering emergency refresh...")
                            await self.auth.emergency_refresh()
                            continue  # Loop will restart, headers will be re-generated with NEW token
                        
                        # Handle rate limit errors
                        if rt_cd == "1" or response.status == 429 or "초당" in error_msg or "초과" in error_msg:
                            wait_time = min(2 ** (attempt + 1), 16)
                            logger.warning(f"Rate limit hit for {symbol}, waiting {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            continue
                        
                        raise RuntimeError(f"API error: {error_msg} (rt_cd: {rt_cd})")
                    
                    return self._normalize_current_price(data, symbol)
            
            except aiohttp.ClientError as e:
                logger.error(f"Network error for {symbol} (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
        
        raise RuntimeError(f"Max retries reached for {symbol}")
    
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
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        
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
        from zoneinfo import ZoneInfo
        if not end_date:
            end_date = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d")
        if not start_date:
            start_dt = datetime.now(ZoneInfo("Asia/Seoul")) - timedelta(days=days)
            start_date = start_dt.strftime("%Y%m%d")
        
        url = f"{self.auth.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-price"
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol,
            "FID_PERIOD_DIV_CODE": "D",     # D: 일봉
            "FID_ORG_ADJ_PRC": "0",         # 0: 수정주가 미반영
        }
        
        # Session is managed by KISAuth singleton
        session = await self.auth.get_session()
        
        for attempt in range(self.max_retries):
            try:
                # HEADERS MUST BE GENERATED INSIDE THE LOOP
                headers = self.auth.get_headers(tr_id="FHKST01010400")
                
                async with session.get(url, headers=headers, params=params) as response:
                    data = await response.json()
                    
                    if data.get("rt_cd") != "0":
                        error_msg = data.get("msg1", "Unknown error")
                        rt_cd = data.get("rt_cd")
                        
                        if response.status == 401:
                            logger.warning(f"401 Unauthorized for {symbol}, triggering emergency refresh...")
                            await self.auth.emergency_refresh()
                            continue
                        
                        # Handle rate limit errors
                        if rt_cd == "1" or response.status == 429 or "초당" in error_msg or "초과" in error_msg:
                            wait_time = min(2 ** (attempt + 1), 16)
                            logger.warning(f"Rate limit hit for {symbol}, waiting {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            continue
                        
                        raise RuntimeError(f"API error: {error_msg} (rt_cd: {rt_cd})")
                    
                    return self._normalize_daily_prices(data, symbol)
            
            except aiohttp.ClientError as e:
                logger.error(f"Network error for {symbol} (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
        
        raise RuntimeError(f"Max retries reached for {symbol}")
    
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
            from zoneinfo import ZoneInfo
            if len(date_str) == 8:
                date_obj = datetime.strptime(date_str, "%Y%m%d")
                timestamp = date_obj.replace(tzinfo=ZoneInfo("Asia/Seoul")).isoformat()
            else:
                timestamp = datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
            
            results.append({
                "meta": {
                    "source": "kis",
                    "market": "kr_stocks",
                    "captured_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
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
        주식 종목 리스트를 가져옵니다.
        
        [중요] KIS API의 종목 전체 조회 엔드포인트(inquire-search-item, TR_ID: HHKST01010100)는
        더 이상 존재하지 않으며 404 에러를 반환합니다.
        
        현재 전략:
        1. 로컬 캐시 파일에서 로드 (Primary - 가장 안정적)
        2. KIS 마스터 파일(CSV) 다운로드 시도 (Secondary)
        
        Args:
            market: 시장 구분 - "KOSPI", "KOSDAQ", 또는 "ALL" (기본값, 현재 미사용)
            
        Returns:
            주식 코드 리스트
        """
        logger.info(f"Fetching stock list for market: {market}")
        
        # [전략 변경] 잘못된 API 호출 제거 - 바로 파일 기반 방식 사용
        # KIS API의 inquire-search-item (HHKST01010100) 엔드포인트는 404 반환
        # 따라서 파일 기반 방식으로 직접 진행
        
        symbols = await self._fetch_stock_list_from_file()
        
        if symbols:
            unique_symbols = sorted(list(set(symbols)))
            logger.info(f"✅ Successfully fetched total {len(unique_symbols)} symbols (file-based)")
            return unique_symbols
        
        logger.error("Failed to fetch stock list from any source")
        return []

    async def _fetch_market_symbols(self, mkt_code: str) -> List[str]:
        """
        특정 시장의 모든 종목 코드를 페이지네이션을 통해 수집합니다.
        
        API: GET /uapi/domestic-stock/v2/quotations/inquire-search-item
        TR_ID: HHKST01010100
        """
        import time
        import random

        url = f"{self.auth.base_url}/uapi/domestic-stock/v2/quotations/inquire-search-item"
        symbols = []
        
        # KIS API pagination usually uses some indicator for next data
        # However, for this specific API, we might need to check the exact spec.
        # Based on typical KIS patterns:
        tr_cont = ""
        
        while True:
            await self.rate_limiter.acquire()
            await self.auth.ensure_token()
            
            params = {
                "FID_COND_MRKT_DIV_CODE": mkt_code,
                "FID_INPUT_ISCD": "", # Empty for all
            }
            
            # Retry loop with exponential backoff
            data = None
            for attempt in range(3): # Max 3 retries
                try:
                    headers = self.auth.get_headers(tr_id="HHKST01010100")
                    if tr_cont:
                        headers["tr_cont"] = tr_cont
                        
                    session = await self.auth.get_session()
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("rt_cd") == "0":
                                break # Success
                            else:
                                error_msg = data.get("msg1", "Unknown error")
                                logger.error(f"API Error (Market {mkt_code}, Attempt {attempt+1}): {error_msg}")
                        elif response.status == 401:
                            await self.auth.emergency_refresh()
                        elif response.status == 404:
                            logger.error(f"❌ 404 Not Found (Market {mkt_code}): Endpoint may have been deprecated or moved to v2. TR_ID: HHKST01010100")
                            raise RuntimeError(f"KIS API 404: {url}")
                        else:
                            logger.error(f"HTTP Error (Market {mkt_code}, Attempt {attempt+1}): {response.status}")
                            
                except Exception as e:
                    logger.error(f"Request Exception (Market {mkt_code}, Attempt {attempt+1}): {e}")
                    # [Fast Fail] Propagate 404 immediately
                    if "404" in str(e):
                        raise
                
                # Exponential backoff
                wait_time = (2 ** attempt) + random.random()
                await asyncio.sleep(wait_time)
            
            if not data or data.get("rt_cd") != "0":
                logger.error(f"Failed to fetch data for market {mkt_code} after retries. Data: {data}")
                break
                
            # Extract symbols
            output = data.get("output", [])
            if not output:
                logger.warning(f"Empty output for market {mkt_code}, response keys: {list(data.keys())}")
            for item in output:
                # KIS API uses different field names: stck_shrn_iscd, mksc_shrn_iscd, or pdno
                code = item.get("stck_shrn_iscd") or item.get("mksc_shrn_iscd") or item.get("pdno")
                if code and len(code) == 6:
                    symbols.append(code)
            
            # Check for next page
            # KIS API pagination: "M" = More data available, others ("F", "D", "") = Last page
            tr_cont = response.headers.get("tr_cont", "")
            if tr_cont != "M":
                logger.debug(f"Pagination complete for market {mkt_code}: tr_cont={tr_cont!r}")
                break
                
        logger.info(f"Fetched {len(symbols)} symbols for market {mkt_code}")
        return symbols
    
    async def _fetch_stock_list_from_file(self) -> List[str]:
        """
        Download and parse stock information from official sources.
        
        APPROACH: Try multiple sources in order:
        1. GitHub official KIS repository
        2. KIS API portal CSV
        3. Alternative public data sources
        
        Returns:
            List of 6-digit stock codes (symbols)
        """
        import csv
        import io
        
        # URLs to try in order of preference
        urls = [
            # GitHub - Official KIS repository  
            "https://raw.githubusercontent.com/koreainvestment/open-trading-api/main/stock_info/stock_codes.csv",
            # KIS official portal
            "https://www.koreainvestment.com/web/contents/down/openapi/stock-code.csv",
        ]
        
        for file_url in urls:
            try:
                logger.info(f"Downloading from: {file_url}")
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        file_url, 
                        timeout=aiohttp.ClientTimeout(total=30),
                        allow_redirects=True
                    ) as response:
                        if response.status == 200:
                            content = await response.text(errors='ignore')
                            logger.info(f"Downloaded {len(content)} bytes")
                            
                            # Parse CSV
                            symbols = []
                            try:
                                reader = csv.DictReader(io.StringIO(content))
                                
                                for row in reader:
                                    if not row:
                                        continue
                                    
                                    # Try multiple field names
                                    code = (
                                        row.get('종목코드') or 
                                        row.get('Code') or 
                                        row.get('code') or
                                        row.get('Symbol') or
                                        row.get('symbol') or
                                        row.get('SYMBOL') or
                                        row.get('stck_shrn_iscd')
                                    )
                                    
                                    if code and len(str(code).strip()) == 6:
                                        symbols.append(code.strip())
                                
                                if symbols:
                                    logger.info(f"✅ Parsed {len(symbols)} symbols from {file_url}")
                                    return list(set(symbols))  # Remove duplicates
                                    
                            except csv.Error as e:
                                logger.warning(f"CSV parse error: {e}")
                                continue
                        else:
                            logger.warning(f"HTTP {response.status} from {file_url}")
                            
            except asyncio.TimeoutError:
                logger.warning(f"Timeout downloading from {file_url}")
                continue
            except aiohttp.ClientError as e:
                logger.warning(f"Network error from {file_url}: {e}")
                continue
            except Exception as e:
                logger.warning(f"Error downloading from {file_url}: {e}")
                continue
        
        # All URLs failed, try fallback
        logger.warning("All primary URLs failed, trying fallback...")
        return await self._fetch_stock_list_from_alternative_source()
    
    async def _fetch_stock_list_from_alternative_source(self) -> List[str]:
        """
        Fallback: Load stock list from local cache file.
        
        When all remote sources fail:
        1. Try to load from config/symbols/kr_all_symbols.txt (PRIMARY)
        2. Try to load from repo root kr_all_symbols.txt (legacy location)
        3. As last resort, raise error
        
        Returns:
            List of stock codes from cache (includes preferred stocks with English letters)
        """
        logger.info("Attempting fallback: loading from local cache...")
        
        # Try multiple cache locations (PRIMARY FIRST)
        from observer.paths import config_dir, project_root
        cache_locations = [
            project_root() / "config" / "symbols" / "kr_all_symbols.txt",  # 1. Image Built-in (via /opt/platform/observer)
            config_dir() / "symbols" / "kr_all_symbols.txt",               # 2. Production K8s Mount (via /opt/platform/runtime)
            Path.cwd() / "kr_all_symbols.txt",                             # 3. Fallback
        ]
        
        for cache_file in cache_locations:
            try:
                logger.info(f"Checking cache location: {cache_file}")
                if cache_file.exists():
                    logger.info(f"✅ Found cache file at: {cache_file}")
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        symbols = [line.strip() for line in f if line.strip()]  # Include all (6-digit AND preferred stocks)
                    
                    if symbols:
                        logger.info(f"✅ Loaded {len(symbols)} symbols from cache: {cache_file}")
                        return symbols
                    else:
                        logger.warning(f"Cache file exists but is empty: {cache_file}")
                        
            except Exception as e:
                logger.warning(f"Error loading cache from {cache_file}: {e}")
                continue
        
        # No cache found
        logger.error("No cache file found and all remote sources failed")
        logger.error("Please run: python -c \"from src.provider.kis.kis_rest_provider import *; ...\"")
        logger.error("Or download stock codes from: https://www.koreainvestment.com/web/contents/down/openapi/")
        
        raise RuntimeError(
            "Could not fetch stock list from any source (online or cache). "
            "Please ensure you have internet access or a local cache file."
        )
    
    # ============================================================
    # Lifecycle Management
    # ============================================================
    
    async def close(self) -> None:
        """Clean up resources."""
        await self.auth.close()
        logger.info("KISRestProvider closed")
