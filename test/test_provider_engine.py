#!/usr/bin/env python3
import asyncio
import logging
import os
from pathlib import Path
import sys

# Project paths and env
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "app" / "obs_deploy" / "app" / "src"))

from dotenv import load_dotenv
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Prefer REAL_* if present
if os.getenv("KIS_APP_KEY") is None and os.getenv("REAL_APP_KEY"):
    os.environ["KIS_APP_KEY"] = os.environ["REAL_APP_KEY"]
if os.getenv("KIS_APP_SECRET") is None and os.getenv("REAL_APP_SECRET"):
    os.environ["KIS_APP_SECRET"] = os.environ["REAL_APP_SECRET"]

from provider import ProviderEngine, KISAuth

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TEST_PROVIDER_ENGINE")


async def main():
    app_key = os.getenv("KIS_APP_KEY")
    app_secret = os.getenv("KIS_APP_SECRET")
    assert app_key and app_secret, "KIS_APP_KEY/SECRET missing"

    auth = KISAuth(app_key, app_secret, is_virtual=False)
    engine = ProviderEngine(auth, is_virtual=False)

    # REST check
    current = await engine.fetch_current_price("005930")
    assert current["instruments"][0]["symbol"] == "005930"
    logger.info("REST current price ok: %s", current["instruments"][0]["price"]["close"])

    # WS start + subscribe small set
    await engine.start_stream()
    await engine.subscribe_many(["005930"], spacing_sec=0.3)

    # Health snapshot
    health = await engine.health()
    logger.info("Health: %s", health)

    # Short wait for potential updates (not required)
    await asyncio.sleep(5)

    await engine.unsubscribe_all()
    await engine.close()
    print("✅ ProviderEngine smoke test completed")


if __name__ == "__main__":
    asyncio.run(main())
