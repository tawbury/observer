"""
Test symbol file generation logic - verify how symbols should be generated/cached
"""
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from universe.universe_manager import UniverseManager


async def test_cache_symbols_to_file():
    """Test the _cache_symbols_to_file method"""
    print("=" * 80)
    print("TEST 1: Cache Symbols To File")
    print("=" * 80)
    
    # Create a mock provider engine
    class MockProviderEngine:
        async def fetch_stock_list(self, market: str):
            # Return some test symbols
            return ["000020", "000040", "000050", "005930", "000660"] * 100  # 500 symbols
    
    # Create UniverseManager with mock engine
    um = UniverseManager(MockProviderEngine())
    
    # Test the cache function directly
    test_symbols = ["000020", "000040", "000050", "005930", "000660"] * 100
    
    print(f"\n1. Testing _cache_symbols_to_file with {len(test_symbols)} symbols")
    await um._cache_symbols_to_file(test_symbols)
    
    # Check if file was created
    base_dir = os.path.abspath(os.path.join(os.path.dirname(um.__class__.__module__), "..", "..", "config"))
    symbols_dir = os.path.join(base_dir, "symbols")
    cache_path = os.path.join(symbols_dir, "kr_all_symbols.txt")
    
    _root = Path(__file__).resolve().parents[1]
    actual_path = _root / "config" / "symbols" / "kr_all_symbols.txt"
    print(f"Expected path: {actual_path}")
    
    if actual_path.exists():
        with open(actual_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        print(f"✅ File created successfully with {len(lines)} lines")
        print(f"First 5 lines: {[line.strip() for line in lines[:5]]}")
        print(f"Last 5 lines: {[line.strip() for line in lines[-5:]]}")
    else:
        print(f"❌ File NOT created at {actual_path}")
    
    print()


async def test_load_candidates():
    """Test _load_candidates method"""
    print("=" * 80)
    print("TEST 2: Load Candidates Priority Chain")
    print("=" * 80)
    
    class MockProviderEngine:
        async def fetch_stock_list(self, market: str):
            raise Exception("API temporarily unavailable")
    
    # Test with no constructor symbols first
    um1 = UniverseManager(MockProviderEngine())
    
    print("\n1. Load candidates (API fails, no file, no constructor symbols)")
    candidates = await um1._load_candidates()
    print(f"Fallback symbols returned: {len(candidates)} symbols")
    print(f"Symbols: {candidates}")
    
    # Test with file-based fallback
    print("\n2. Load candidates (with existing kr_all_symbols.txt)")
    
    _root = Path(__file__).resolve().parents[1]
    # First ensure the file exists
    actual_path = _root / "config" / "symbols" / "kr_all_symbols.txt"
    if actual_path.exists():
        um2 = UniverseManager(MockProviderEngine())
        candidates = await um2._load_candidates()
        print(f"✅ Loaded {len(candidates)} symbols from kr_all_symbols.txt")
        print(f"First 5: {candidates[:5]}")
        print(f"Last 5: {candidates[-5:]}")
    else:
        print(f"⚠️  File not found at {actual_path}")
    
    # Test with constructor symbols
    print("\n3. Load candidates (with constructor symbols)")
    test_constructor_symbols = ["123456", "234567", "345678"]
    um3 = UniverseManager(MockProviderEngine(), candidate_symbols=test_constructor_symbols)
    candidates = await um3._load_candidates()
    print(f"✅ Loaded {len(candidates)} symbols from constructor")
    print(f"Symbols: {candidates}")
    
    print()


async def test_snapshot_generation_logic():
    """Test how universe snapshots are generated"""
    print("=" * 80)
    print("TEST 3: Universe Snapshot Structure")
    print("=" * 80)
    
    # Create a sample snapshot structure
    target_date = datetime.now().date()
    market = "kr_stocks"
    
    sample_snapshot = {
        "date": target_date.isoformat(),
        "market": market,
        "filter_criteria": {
            "min_price": 4000,
            "prev_trading_day": (target_date.replace(day=target_date.day - 1)).isoformat() if target_date.day > 1 else target_date.isoformat(),
        },
        "symbols": ["000020", "000040", "000050", "005930", "000660"],
        "count": 5,
    }
    
    print("\n1. Sample Snapshot Structure:")
    print(json.dumps(sample_snapshot, indent=2, ensure_ascii=False))
    
    # Check where this would be saved
    um = UniverseManager(None)
    snapshot_path = um._snapshot_path(target_date)
    print(f"\n2. Snapshot would be saved at: {snapshot_path}")
    
    # Test file reading
    print("\n3. Test snapshot loading:")
    _root = Path(__file__).resolve().parents[1]
    sample_snapshot_path = _root / "config" / "universe" / f"{target_date.strftime('%Y%m%d')}_kr_stocks.json"
    
    if sample_snapshot_path.exists():
        with open(sample_snapshot_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        print(f"✅ Snapshot exists and loads successfully")
        print(f"   Symbols count: {loaded.get('count')}")
        print(f"   First 3 symbols: {loaded.get('symbols', [])[:3]}")
    else:
        print(f"⚠️  Sample snapshot not found at {sample_snapshot_path}")
    
    print()


async def test_symbol_file_paths():
    """Verify path calculations"""
    print("=" * 80)
    print("TEST 4: Path Calculation Verification")
    print("=" * 80)
    
    um = UniverseManager(None)
    
    # Show configured paths
    print(f"\n1. Universe Directory: {um.universe_dir}")
    print(f"   Exists: {os.path.exists(um.universe_dir)}")
    
    # Show symbol cache path logic
    _root = Path(__file__).resolve().parents[1]
    base_dir = str(_root / "config")
    symbols_dir = os.path.join(base_dir, "symbols")
    txt_path = os.path.join(symbols_dir, "kr_all_symbols.txt")
    
    print(f"\n2. Symbol Cache Path: {txt_path}")
    print(f"   Exists: {os.path.exists(txt_path)}")
    
    if os.path.exists(txt_path):
        with open(txt_path, "r", encoding="utf-8") as f:
            lines = len(f.readlines())
        print(f"   Content: {lines} symbols")
    
    print()


async def main():
    print("\n")
    print("█" * 80)
    print("SYMBOL FILE GENERATION LOGIC VERIFICATION")
    print("█" * 80)
    
    try:
        # await test_cache_symbols_to_file()
        await test_load_candidates()
        await test_snapshot_generation_logic()
        await test_symbol_file_paths()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 80)
    print("TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
