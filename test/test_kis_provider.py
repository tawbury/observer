#!/usr/bin/env python3
"""
test_kis_provider.py

KIS Provider Integration Test

Tests:
1. KIS OAuth authentication
2. Current price fetch
3. Daily prices fetch
4. Rate limiting
5. Error handling

Usage:
    python test_kis_provider.py

Environment Variables Required:
    KIS_APP_KEY - KIS application key
    KIS_APP_SECRET - KIS application secret
    KIS_BASE_URL - KIS API base URL (optional)
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "app" / "obs_deploy" / "app" / "src"))

# Load .env manually to ensure KIS creds are available when running locally
env_path = project_root / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key, value)

# Fallback: map REAL_* keys to KIS_* keys if not explicitly set
if os.getenv("KIS_APP_KEY") is None and os.getenv("REAL_APP_KEY"):
    os.environ["KIS_APP_KEY"] = os.environ["REAL_APP_KEY"]
if os.getenv("KIS_APP_SECRET") is None and os.getenv("REAL_APP_SECRET"):
    os.environ["KIS_APP_SECRET"] = os.environ["REAL_APP_SECRET"]
if os.getenv("KIS_BASE_URL") is None and os.getenv("REAL_BASE_URL"):
    os.environ["KIS_BASE_URL"] = os.environ["REAL_BASE_URL"]
# Map to paper trading env vars for virtual mode tests
if os.getenv("KIS_PAPER_APP_KEY") is None and os.getenv("REAL_APP_KEY"):
    os.environ["KIS_PAPER_APP_KEY"] = os.environ["REAL_APP_KEY"]
if os.getenv("KIS_PAPER_APP_SECRET") is None and os.getenv("REAL_APP_SECRET"):
    os.environ["KIS_PAPER_APP_SECRET"] = os.environ["REAL_APP_SECRET"]
if os.getenv("KIS_PAPER_BASE_URL") is None and os.getenv("REAL_BASE_URL"):
    os.environ["KIS_PAPER_BASE_URL"] = os.environ["REAL_BASE_URL"]

from provider.kis.kis_auth import KISAuth
from provider.kis.kis_rest_provider import KISRestProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("KIS_PROVIDER_TEST")

logger.info(
    "Env loaded | KIS_APP_KEY:%s REAL_APP_KEY:%s",
    bool(os.getenv("KIS_APP_KEY")),
    bool(os.getenv("REAL_APP_KEY")),
)

_shared_auth: KISAuth | None = None


async def get_auth() -> KISAuth:
    """Return a shared KISAuth instance to avoid hitting token issuance limits."""
    global _shared_auth
    if _shared_auth is None:
        _shared_auth = KISAuth(is_virtual=True)
    await _shared_auth.ensure_token()
    return _shared_auth


async def test_authentication():
    """Test KIS OAuth authentication."""
    logger.info("=" * 60)
    logger.info("TEST 1: KIS OAuth Authentication")
    logger.info("=" * 60)
    
    try:
        auth = await get_auth()
        
        # Request token (already ensured)
        token = auth.access_token
        
        logger.info("✅ Authentication successful")
        logger.info(f"   Token: {token[:20]}...")
        logger.info(f"   Issued at: {auth.token_issued_at}")
        logger.info(f"   Expires at: {auth.token_expires_at}")
        
        # Test approval key (for WebSocket)
        approval_key = await auth.get_approval_key()
        logger.info(f"✅ Approval key obtained: {approval_key[:20]}...")
        
        await auth.close()
        return True
    
    except Exception as e:
        logger.error(f"❌ Authentication failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_current_price():
    """Test current price fetch."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Current Price Fetch")
    logger.info("=" * 60)
    
    try:
        auth = await get_auth()
        provider = KISRestProvider(auth)
        
        # Test symbols
        test_symbols = [
            ("005930", "삼성전자"),
            ("000660", "SK하이닉스"),
            ("373220", "LG에너지솔루션"),
        ]
        
        for symbol, name in test_symbols:
            logger.info(f"\n📊 Fetching {name} ({symbol})...")
            
            data = await provider.fetch_current_price(symbol)
            
            instrument = data["instruments"][0]
            price = instrument["price"]
            
            logger.info(f"✅ {name} data received:")
            logger.info(f"   시가: {price['open']:,}원")
            logger.info(f"   고가: {price['high']:,}원")
            logger.info(f"   저가: {price['low']:,}원")
            logger.info(f"   현재가: {price['close']:,}원")
            logger.info(f"   거래량: {instrument['volume']:,}주")
            logger.info(f"   Timestamp: {instrument['timestamp']}")
            
            if instrument.get("bid_price"):
                logger.info(f"   매수호가: {instrument['bid_price']:,}원")
            if instrument.get("ask_price"):
                logger.info(f"   매도호가: {instrument['ask_price']:,}원")
        
        await provider.close()
        return True
    
    except Exception as e:
        logger.error(f"❌ Current price fetch failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_daily_prices():
    """Test daily historical prices fetch."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Daily Historical Prices")
    logger.info("=" * 60)
    
    try:
        auth = await get_auth()
        provider = KISRestProvider(auth)
        
        symbol = "005930"  # 삼성전자
        days = 5
        
        logger.info(f"📈 Fetching {days} days of historical data for {symbol}...")
        
        daily_data = await provider.fetch_daily_prices(symbol, days=days)
        
        logger.info(f"✅ Received {len(daily_data)} days of data:")
        
        for i, data in enumerate(daily_data[:5], 1):  # Show first 5
            instrument = data["instruments"][0]
            price = instrument["price"]
            date = instrument["timestamp"][:10]
            
            logger.info(
                f"   {i}. {date}: "
                f"시가 {price['open']:,}, "
                f"고가 {price['high']:,}, "
                f"저가 {price['low']:,}, "
                f"종가 {price['close']:,}, "
                f"거래량 {instrument['volume']:,}"
            )
        
        await provider.close()
        return True
    
    except Exception as e:
        logger.error(f"❌ Daily prices fetch failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_rate_limiting():
    """Test rate limiter."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Rate Limiting")
    logger.info("=" * 60)
    
    try:
        auth = await get_auth()
        provider = KISRestProvider(auth)
        
        # Test rapid requests (should be rate-limited)
        symbol = "005930"
        num_requests = 25  # Exceeds 20 req/sec limit
        
        logger.info(f"📊 Making {num_requests} rapid requests...")
        start_time = asyncio.get_event_loop().time()
        
        tasks = [provider.fetch_current_price(symbol) for _ in range(num_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        
        logger.info(f"✅ Rate limiting test completed:")
        logger.info(f"   Duration: {duration:.2f}s")
        logger.info(f"   Successful requests: {success_count}/{num_requests}")
        logger.info(f"   Effective rate: {success_count/duration:.2f} req/sec")
        
        # Should be close to 20 req/sec
        if 15 < success_count/duration < 25:
            logger.info(f"   ✅ Rate limiting working correctly")
        else:
            logger.warning(f"   ⚠️ Rate may be outside expected range")
        
        await provider.close()
        return True
    
        # Cleanup shared auth
        global _shared_auth
        if _shared_auth:
            await _shared_auth.close()
            _shared_auth = None
    except Exception as e:
        logger.error(f"❌ Rate limiting test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_handling():
    """Test error handling."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 5: Error Handling")
    logger.info("=" * 60)
    
    try:
        auth = await get_auth()
        provider = KISRestProvider(auth)
        
        # Test invalid symbol
        logger.info("📊 Testing invalid symbol...")
        try:
            invalid_symbol = "999999"
            await provider.fetch_current_price(invalid_symbol)
            logger.warning("   ⚠️ Expected error but succeeded")
        except Exception as e:
            logger.info(f"   ✅ Correctly handled error: {str(e)[:50]}...")
        
        # Test with expired token (simulate)
        logger.info("\n📊 Testing token refresh...")
        auth.access_token = "invalid_token"
        try:
            data = await provider.fetch_current_price("005930")
            logger.info("   ✅ Token refresh handled correctly")
        except Exception as e:
            logger.error(f"   ❌ Token refresh failed: {e}")
        
        await provider.close()
        return True
    
    except Exception as e:
        logger.error(f"❌ Error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests."""
    logger.info("\n" + "=" * 60)
    logger.info("KIS PROVIDER INTEGRATION TEST SUITE")
    logger.info("=" * 60)
    
    # Check environment variables
    required_vars = ["KIS_APP_KEY", "KIS_APP_SECRET"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        logger.error("   Please set them in .env file or environment")
        return
    
    results = {
        "Authentication": await test_authentication(),
        "Current Price": await test_current_price(),
        "Daily Prices": await test_daily_prices(),
        "Rate Limiting": await test_rate_limiting(),
        "Error Handling": await test_error_handling(),
    }
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    logger.info("\n" + "=" * 60)
    logger.info(f"TOTAL: {passed_tests}/{total_tests} tests passed")
    logger.info("=" * 60)
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
