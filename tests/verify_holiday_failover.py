import os
import sys
import json
import shutil
import asyncio
from datetime import date, timedelta
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))

from universe.universe_manager import UniverseManager

class MockProvider:
    async def fetch_daily_prices(self, sym, days=2):
        return []

async def test_holiday_failover():
    print("Testing UniverseManager 7-day failover...")
    
    # Setup test directory
    test_dir = project_root / "tests" / "temp_failover_test"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True, exist_ok=True)
    
    universe_dir = test_dir / "universe"
    universe_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a universe file from 4 days ago
    four_days_ago = date.today() - timedelta(days=4)
    ymd = four_days_ago.strftime("%Y%m%d")
    market = "kr_stocks"
    filename = f"{ymd}_{market}.json"
    
    data = {
        "metadata": {"date": ymd, "count": 2},
        "symbols": ["005930", "000660"]
    }
    
    with open(universe_dir / filename, "w") as f:
        json.dump(data, f)
        
    print(f"Created mock universe file: {filename}")
    
    # Initialize Manager
    manager = UniverseManager(MockProvider(), data_dir=str(test_dir), market=market)
    
    # Try to get current universe (today and yesterday are missing)
    print("Attempting to get current universe (expecting failover to 4 days ago)...")
    symbols = manager.get_current_universe()
    
    print(f"Symbols found: {symbols}")
    
    if symbols == ["005930", "000660"]:
        print("✅ Success: Successfully failed over to 4 days ago.")
    else:
        print(f"❌ Failure: Expected ['005930', '000660'], got {symbols}")

    # Cleanup
    # shutil.rmtree(test_dir)

if __name__ == "__main__":
    asyncio.run(test_holiday_failover())
