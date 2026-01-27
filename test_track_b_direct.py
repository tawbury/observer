#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Track B Direct Test

Track B를 직접 실행하고 스켈프 데이터가 기록되는지 테스트합니다.
"""
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# Setup paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "app" / "observer"))
sys.path.insert(0, str(project_root / "app" / "observer" / "src"))

# Load .env
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / "app" / "observer" / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"[INFO] Loaded .env from {env_file}")
except:
    pass

# Set environment for local testing
import os
os.environ["OBSERVER_STANDALONE"] = "0"
os.environ["OBSERVER_CONFIG_DIR"] = str(Path(__file__).parent / "app" / "observer" / "config")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

from collector.track_b_collector import TrackBCollector, TrackBConfig
from provider import ProviderEngine, KISAuth


async def test_track_b():
    """Test Track B collector directly"""
    print("\n" + "="*70)
    print("Track B Direct Test")
    print("="*70)
    
    # Setup auth
    kis_app_key = os.environ.get("KIS_APP_KEY")
    kis_app_secret = os.environ.get("KIS_APP_SECRET")
    kis_is_virtual = os.environ.get("KIS_IS_VIRTUAL", "false").lower() in ("true", "1")
    
    if not kis_app_key or not kis_app_secret:
        print("ERROR: KIS credentials not found in .env")
        return False
    
    print(f"[OK] KIS credentials loaded")
    print(f"[OK] Virtual mode: {kis_is_virtual}")
    
    # Create provider engine
    auth = KISAuth(kis_app_key, kis_app_secret, is_virtual=kis_is_virtual)
    engine = ProviderEngine(auth=auth, is_virtual=kis_is_virtual)
    print(f"[OK] ProviderEngine created")
    
    # Create Track B config
    config = TrackBConfig(
        market="kr_stocks",
        session_id="direct_test",
        max_slots=6,  # Small for testing
        trigger_check_interval_seconds=60
    )
    print(f"[OK] TrackBConfig created: {config.bootstrap_symbols}")
    
    # Create collector
    collector = TrackBCollector(engine=engine, config=config)
    print(f"[OK] TrackBCollector created")
    
    # Check scalp directory
    from paths import observer_asset_dir
    scalp_dir = observer_asset_dir() / "scalp"
    print(f"\n[DIR] Scalp directory: {scalp_dir}")
    
    # Run for 30 seconds
    print(f"\n[START] Starting Track B... (30 second test)")
    print(f"[LOG] Expected scalp log: {scalp_dir / datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m%d')}.jsonl")
    print("="*70)
    
    try:
        collector_task = asyncio.create_task(collector.start())
        await asyncio.sleep(30)
        collector.stop()
        await collector_task
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        collector.stop()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()
    
    # Check results
    print("\n" + "="*70)
    print("TEST RESULTS")
    print("="*70)
    
    date_str = datetime.now(ZoneInfo("Asia/Seoul")).strftime('%Y%m%d')
    log_file = scalp_dir / f"{date_str}.jsonl"
    
    if log_file.exists():
        size = log_file.stat().st_size
        lines = len(open(log_file).readlines())
        print(f"[OK] Scalp log created: {log_file}")
        print(f"     Size: {size} bytes")
        print(f"     Lines: {lines}")
        
        # Show sample
        if lines > 0:
            import json
            with open(log_file) as f:
                first = json.loads(f.readline())
                print(f"\n     Sample entry:")
                print(f"     Symbol: {first.get('symbol')}")
                print(f"     Price: {first.get('price', {}).get('current')}")
        
        return True
    else:
        print(f"[FAIL] Scalp log NOT created: {log_file}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_track_b())
    sys.exit(0 if success else 1)
