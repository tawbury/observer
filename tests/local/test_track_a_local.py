#!/usr/bin/env python3
"""
Local Test Script for Track A Collector

Usage:
  python test_track_a_local.py --run-once    # Single collection cycle
  python test_track_a_local.py                # Continuous collection (trading hours only)
"""

import sys
import os
import asyncio
import argparse
import logging
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("TestTrackA")

# Load env if available - check multiple locations
from dotenv import load_dotenv
env_paths = [
    PROJECT_ROOT / ".env",
    PROJECT_ROOT / ".env",  # project root .env
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        log.info(f"Loaded .env from {env_path}")
        break
else:
    log.warning(f".env not found in {[str(p) for p in env_paths]}")

from provider import KISAuth, ProviderEngine
from collector.track_a_collector import TrackACollector, TrackAConfig


async def main():
    parser = argparse.ArgumentParser(description="Track A Collector - Local Test")
    parser.add_argument("--run-once", action="store_true", help="Run single collection and exit")
    args = parser.parse_args()
    
    # Get credentials
    app_key = os.getenv("KIS_APP_KEY") or os.getenv("REAL_APP_KEY")
    app_secret = os.getenv("KIS_APP_SECRET") or os.getenv("REAL_APP_SECRET")
    
    if not app_key or not app_secret:
        log.error("KIS_APP_KEY/SECRET not found in environment")
        sys.exit(1)
    
    log.info("Initializing Track A Collector...")
    
    # Initialize provider
    auth = KISAuth(app_key, app_secret, is_virtual=False)
    engine = ProviderEngine(auth, is_virtual=False)
    
    # Create collector with config
    config = TrackAConfig(
        interval_minutes=10,
        market="kr_stocks",
        session_id="track_a_local_test",
        mode="TEST",
        semaphore_limit=20
    )
    
    def on_error(msg: str):
        log.error(f"Track A Error: {msg}")
    
    collector = TrackACollector(engine, config=config, on_error=on_error)
    
    try:
        if args.run_once:
            log.info("Running Track A collection (once)...")
            result = await collector.collect_once()
            log.info(f"✅ Collection result: {result}")
        else:
            log.info("Starting Track A collector (continuous mode)...")
            await collector.start()
    except KeyboardInterrupt:
        log.info("Track A collector stopped by user")
    except Exception as e:
        log.exception(f"Track A collector error: {e}")
        sys.exit(1)
    finally:
        await engine.close()
        log.info("Track A collector cleanup complete")


if __name__ == "__main__":
    asyncio.run(main())
