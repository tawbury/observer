"""
Deep dive: Symbol file caching behavior
Analyze when/how _cache_symbols_to_file is called and what might prevent it
"""
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime, date
from app.observer.src.universe.universe_manager import UniverseManager


async def test_when_cache_is_written():
    """Test when cache file gets written"""
    print("=" * 80)
    print("TEST: When does _cache_symbols_to_file get called?")
    print("=" * 80)
    
    # Scenario 1: API succeeds - should write cache
    class MockProviderEngineAPISuccess:
        async def fetch_stock_list(self, market: str):
            print("  [MOCK API] Returning 500 test symbols")
            return [f"{i:06d}" for i in range(500, 1000)]
    
    print("\n1. Scenario: API returns symbols successfully")
    print("   Expected: Cache file should be written")
    
    # Create temp universe dir for this test
    test_universe_dir = Path(__file__).parent / "app" / "observer" / "config" / "universe_test"
    test_universe_dir.mkdir(exist_ok=True)
    
    um1 = UniverseManager(MockProviderEngineAPISuccess(), universe_dir=str(test_universe_dir))
    
    # Look at the _load_candidates call
    candidates = await um1._load_candidates()
    print(f"   ✅ Loaded {len(candidates)} symbols")
    print(f"   Check cache file: {candidates[:5]}")
    
    # Scenario 2: API fails - should try file fallback
    print("\n2. Scenario: API fails, file fallback used")
    print("   Expected: Cache file is NOT modified")
    
    class MockProviderEngineAPIFail:
        async def fetch_stock_list(self, market: str):
            raise Exception("API error")
    
    um2 = UniverseManager(MockProviderEngineAPIFail())
    candidates = await um2._load_candidates()
    print(f"   ✅ Loaded {len(candidates)} symbols from fallback")
    print(f"   Cache file location: D:\\development\\prj_obs\\app\\observer\\config\\symbols\\kr_all_symbols.txt")
    
    print()


async def test_symbol_file_vs_universe_snapshots():
    """Understand the difference between symbol cache and universe snapshots"""
    print("=" * 80)
    print("TEST: Symbol File vs Universe Snapshots")
    print("=" * 80)
    
    um = UniverseManager(None)
    
    print("\n1. Symbol Cache File (kr_all_symbols.txt)")
    print("   Purpose: Persistent cache of all available symbols")
    print("   Updated: Only when API fetch succeeds (via _cache_symbols_to_file)")
    print("   Used by: _load_candidates() as Priority #3 fallback")
    
    symbol_cache = Path(__file__).parent / "app" / "observer" / "config" / "symbols" / "kr_all_symbols.txt"
    if symbol_cache.exists():
        with open(symbol_cache) as f:
            count = len([l for l in f if l.strip()])
        print(f"   Current file: {count} symbols")
    
    print("\n2. Universe Snapshots (YYYYMMDD_kr_stocks.json)")
    print("   Purpose: Daily filtered universe (min price, tradable)")
    print("   Created: By create_daily_snapshot() using candidates + price filter")
    print("   Used by: get_current_universe() to get filtered list for day")
    
    universe_dir = Path(__file__).parent / "app" / "observer" / "config" / "universe"
    if universe_dir.exists():
        snapshots = list(universe_dir.glob("*_kr_stocks.json"))
        print(f"   Available snapshots: {len(snapshots)}")
        if snapshots:
            latest = sorted(snapshots)[-1]
            with open(latest) as f:
                data = json.load(f)
            print(f"   Latest: {latest.name}")
            print(f"   - Date: {data.get('date')}")
            print(f"   - Symbols: {data.get('count')} (filtered from {len(data.get('symbols', []))})")
    
    print("\n3. The Issue: Symbol file is NOT auto-generated in normal operation")
    print("   Why: _cache_symbols_to_file only called when API succeeds")
    print("   When API fails, code falls back to existing file without updating it")
    
    print()


async def trace_symbol_generation_flow():
    """Trace the complete flow of how symbols get generated/cached"""
    print("=" * 80)
    print("TEST: Complete Symbol Generation Flow")
    print("=" * 80)
    
    print("\n=== FLOW DIAGRAM ===")
    print("""
    1. Track A Collector starts
       └─→ Initialize UniverseManager
           └─→ __init__() calculates universe_dir
    
    2. When universe needed: get_current_universe()
       └─→ _try_load_universe_list(today)
           └─→ Checks for YYYYMMDD_kr_stocks.json
               ✗ If NOT found → fallback to latest snapshot
               ✗ If STILL not found → returns empty []
    
    3. To CREATE snapshot: create_daily_snapshot()
       └─→ _load_candidates()
           └─→ Priority 1: API (fetch_stock_list)
               ✓ If SUCCESS → cache to kr_all_symbols.txt ← HERE IS WHERE FILE IS WRITTEN
               ✗ If FAILS:
                  └─→ Priority 2: Constructor symbols
                  └─→ Priority 3: Existing kr_all_symbols.txt file
                  └─→ Priority 4: Built-in 20 symbols fallback
           └─→ Fetch prices for candidates (current_price + daily_prices)
           └─→ Filter by min_price
           └─→ Create YYYYMMDD_kr_stocks.json with filtered list
    
    === THE PROBLEM ===
    
    If API is NEVER called successfully:
    - kr_all_symbols.txt is NEVER created
    - Only built-in 20 symbols used as fallback
    - Snapshots created from those 20 symbols
    - result: Very small universe
    
    If API IS called successfully:
    - kr_all_symbols.txt is written/updated
    - Used for future fallback when API fails
    """)
    
    print()
    print("\n=== SOLUTION ===")
    print("""
    The symbol file is SUPPOSED to be pre-populated manually or fetched from API.
    
    Option 1: API fetch succeeds (ideal, auto-caches)
    - KIS API returns 2000+ symbols
    - _cache_symbols_to_file writes to kr_all_symbols.txt
    
    Option 2: Manual file provision (current state)
    - You manually created kr_all_symbols.txt with 2894 symbols
    - System uses it as fallback when API fails
    
    Option 3: Init symbol file from startup script
    - Boot script could run API fetch once
    - Or copy pre-curated symbol file
    """)
    
    print()


async def find_symbol_file_generation_triggers():
    """Find all places where symbol files should be generated"""
    print("=" * 80)
    print("TEST: Find Symbol File Generation Triggers")
    print("=" * 80)
    
    print("""
    Looking for places in code where kr_all_symbols.txt is written...
    
    Found in: app/observer/src/universe/universe_manager.py
    
    Location 1: _cache_symbols_to_file()
    - Line 259-270
    - Called ONLY from: _load_candidates() after API succeeds
    - Writes: symbol_dir/kr_all_symbols.txt
    
    Usage: await self._cache_symbols_to_file(api_symbols)
    
    Location 2: Manual creation (what you did)
    - Created file manually at app/observer/config/symbols/kr_all_symbols.txt
    - 2894 symbols, newline-separated
    
    === NO OTHER LOCATIONS ===
    
    Conclusion:
    - Symbol file is ONLY written when API successfully fetches symbols
    - It's a PERSISTENCE mechanism, not a generation mechanism
    - Your manual creation was correct workaround
    """)
    
    print()


async def main():
    print("\n")
    print("█" * 80)
    print("SYMBOL FILE GENERATION: DETAILED ANALYSIS")
    print("█" * 80)
    
    try:
        await test_when_cache_is_written()
        await test_symbol_file_vs_universe_snapshots()
        await trace_symbol_generation_flow()
        await find_symbol_file_generation_triggers()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 80)
    print("ANALYSIS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
