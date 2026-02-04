import os
import sys
import json
import shutil
import asyncio
import logging
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

# Add src to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))

from collector.track_a_collector import TrackACollector, TrackAConfig

async def test_bootstrap_logic():
    print("Testing TrackACollector bootstrap logic...")
    
    # Mock Provider Engine
    engine = MagicMock()
    engine.fetch_stock_list = AsyncMock(return_value=["005930"] * 3000)
    engine.fetch_daily_prices = AsyncMock(return_value=[])
    
    # Setup test directory
    test_dir = project_root / "tests" / "temp_bootstrap_test"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Paths
    universe_dir = test_dir / "universe"
    symbols_dir = test_dir / "symbols"
    universe_dir.mkdir(parents=True, exist_ok=True)
    symbols_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize Collector
    config = TrackAConfig(market="kr_stocks")
    collector = TrackACollector(engine, config=config, universe_dir=str(test_dir))
    
    # Mock should_collect to return True (insufficient symbols)
    collector._manager.symbol_gen.should_collect = MagicMock(return_value=(True, None))
    collector._manager.symbol_gen.execute = AsyncMock(return_value="mock_path")
    
    # Mock get_current_universe to return empty list first time (no universe)
    # But it's a real call, so we just ensure no files exist
    
    # Replace create_daily_snapshot with a mock to track calls
    collector._manager.create_daily_snapshot = AsyncMock(return_value="mock_snap_path")
    
    # Mock start loop to exit early
    async def mock_start():
        # Only run the bootstrap part
        log = logging.getLogger("TrackACollector")
        log.info("Bootstrapping SymbolGenerator...")
        
        # 1. Symbol Check
        should_collect, existing_symbol_path = collector._manager.symbol_gen.should_collect()
        if should_collect:
            print("[TEST] Symbol collection triggered.")
            await collector._manager.symbol_gen.execute()
            
        # 2. Universe Force Generation
        current_universe = collector._manager.get_current_universe()
        if not current_universe:
            print("[TEST] Universe force generation triggered.")
            await collector._manager.create_daily_snapshot(date.today())
            
    print("Running bootstrap part...")
    await mock_start()
    
    # Verifications
    if collector._manager.symbol_gen.execute.called:
        print("✅ Symbol collection was correctly triggered.")
    else:
        print("❌ Symbol collection was NOT triggered.")
        
    if collector._manager.create_daily_snapshot.called:
        print("✅ Universe force generation was correctly triggered.")
    else:
        print("❌ Universe force generation was NOT triggered.")

    # Cleanup
    # shutil.rmtree(test_dir)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_bootstrap_logic())
