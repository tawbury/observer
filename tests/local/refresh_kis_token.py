#!/usr/bin/env python3
"""
KIS API 토큰 강제 갱신 스크립트

실행:
  python tests/local/refresh_kis_token.py
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
APP_ROOT = PROJECT_ROOT / "app" / "observer"
sys.path.insert(0, str(APP_ROOT / "src"))
sys.path.insert(0, str(APP_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("TokenRefresh")

# Load .env
from dotenv import load_dotenv
env_path = APP_ROOT / ".env"
if env_path.exists():
    load_dotenv(env_path)
    log.info(f"Loaded .env from {env_path}")


async def refresh_token():
    """토큰 강제 갱신"""
    from provider.kis.kis_auth import KISAuth
    
    app_key = os.getenv("KIS_APP_KEY")
    app_secret = os.getenv("KIS_APP_SECRET")
    
    if not app_key or not app_secret:
        log.error("KIS credentials not found")
        return False
    
    log.info("Initializing KISAuth...")
    auth = KISAuth(app_key, app_secret, is_virtual=False)
    
    # Clear cached token
    if auth._token_cache_path and auth._token_cache_path.exists():
        log.info(f"Removing cached token: {auth._token_cache_path}")
        auth._token_cache_path.unlink()
    
    # Force token refresh
    log.info("Requesting new token...")
    auth.access_token = None
    auth.token_issued_at = None
    auth.token_expires_at = None
    
    try:
        token = await auth.ensure_token()
        if token:
            log.info(f"[SUCCESS] New token obtained!")
            log.info(f"  Token prefix: {token[:20]}...")
            log.info(f"  Issued at: {auth.token_issued_at}")
            log.info(f"  Expires at: {auth.token_expires_at}")
            return True
        else:
            log.error("[FAIL] Failed to get token")
            return False
    except Exception as e:
        log.error(f"[FAIL] Token refresh error: {e}")
        return False
    finally:
        await auth.close()


async def test_api_call():
    """API 호출 테스트"""
    from provider import KISAuth, ProviderEngine
    
    app_key = os.getenv("KIS_APP_KEY")
    app_secret = os.getenv("KIS_APP_SECRET")
    
    log.info("Testing API call...")
    auth = KISAuth(app_key, app_secret, is_virtual=False)
    engine = ProviderEngine(auth, is_virtual=False)
    
    try:
        data = await engine.fetch_current_price("005930")
        if data:
            log.info("[SUCCESS] API call successful!")
            instruments = data.get("instruments", [{}])
            if instruments:
                price = instruments[0].get("price", {})
                log.info(f"  Samsung (005930) current price: {price.get('close')}")
            return True
        else:
            log.error("[FAIL] API call returned no data")
            return False
    except Exception as e:
        log.error(f"[FAIL] API call error: {e}")
        return False
    finally:
        await engine.close()


async def main():
    log.info("="*60)
    log.info("KIS Token Refresh")
    log.info("="*60)
    
    # Step 1: Refresh token
    token_ok = await refresh_token()
    
    if not token_ok:
        log.error("Token refresh failed")
        return 1
    
    # Step 2: Test API call
    log.info("")
    api_ok = await test_api_call()
    
    if api_ok:
        log.info("")
        log.info("[SUCCESS] Token refresh and API test completed!")
        return 0
    else:
        log.error("API test failed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
