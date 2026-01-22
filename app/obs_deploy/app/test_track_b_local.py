#!/usr/bin/env python3
"""
Local Test Script for Track B Collector

Usage:
  python test_track_b_local.py --run-once    # Single trigger check cycle
  python test_track_b_local.py                # Continuous mode (trading hours only)
"""

import sys
import os
import asyncio
import argparse
import logging
from pathlib import Path

# Setup paths
APP_ROOT = str(Path(__file__).resolve().parent)
sys.path.insert(0, str(Path(APP_ROOT) / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("TestTrackB")

# Load env if available - check both app root and obs_deploy root
from dotenv import load_dotenv
env_paths = [
    Path(APP_ROOT) / ".env",  # app/ root
    Path(APP_ROOT).parent / ".env",  # obs_deploy/ root
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        log.info(f"Loaded .env from {env_path}")
        break
else:
    log.warning(f".env not found in {[str(p) for p in env_paths]}")

from provider import KISAuth, ProviderEngine
from trigger.trigger_engine import TriggerEngine, TriggerConfig
from slot.slot_manager import SlotManager
from collector.track_b_collector import TrackBCollector, TrackBConfig


async def main():
    parser = argparse.ArgumentParser(description="Track B Collector - Local Test")
    parser.add_argument("--run-once", action="store_true", help="Run single trigger check and exit")
    args = parser.parse_args()
    
    # Get credentials
    app_key = os.getenv("KIS_APP_KEY") or os.getenv("REAL_APP_KEY")
    app_secret = os.getenv("KIS_APP_SECRET") or os.getenv("REAL_APP_SECRET")
    
    if not app_key or not app_secret:
        log.error("KIS_APP_KEY/SECRET not found in environment")
        sys.exit(1)
    
    log.info("Initializing Track B Collector...")
    
    # Initialize provider
    auth = KISAuth(app_key, app_secret, is_virtual=False)
    engine = ProviderEngine(auth, is_virtual=False)
    
    # Initialize trigger engine and slot manager
    trigger_config = TriggerConfig(
        volume_surge_ratio=5.0,
        volatility_spike_threshold=0.05,
        max_candidates=100
    )
    trigger_engine = TriggerEngine(config=trigger_config)
    
    slot_manager = SlotManager(max_slots=41, min_dwell_seconds=120)
    
    # Create collector with config
    config = TrackBConfig(
        market="kr_stocks",
        session_id="track_b_local_test",
        mode="TEST",
        max_slots=41,
        track_a_check_interval_seconds=60
    )
    
    def on_error(msg: str):
        log.error(f"Track B Error: {msg}")
    
    collector = TrackBCollector(
        engine, 
        trigger_engine=trigger_engine,
        config=config, 
        on_error=on_error
    )
    
    try:
        if args.run_once:
            log.info("Running Track B trigger check (once)...")
            # Simulate one check cycle
            await collector._check_triggers()
            stats = collector.get_stats()
            log.info(f"✅ Track B stats: {stats}")
        else:
            log.info("Starting Track B collector (continuous mode)...")
            await collector.start()
    except KeyboardInterrupt:
        log.info("Track B collector stopped by user")
    except Exception as e:
        log.exception(f"Track B collector error: {e}")
        sys.exit(1)
    finally:
        collector.stop()
        await engine.close()
        log.info("Track B collector cleanup complete")


if __name__ == "__main__":
    asyncio.run(main())
