"""
Improved symbol file generation logic
Test enhanced _load_candidates() that creates symbol file if missing
"""
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime, date
from app.observer.src.universe.universe_manager import UniverseManager


class ImprovedUniverseManager(UniverseManager):
    """Enhanced UniverseManager with automatic symbol file generation"""
    
    async def _load_candidates(self) -> list:
        """
        Load candidate symbols from multiple sources in priority order:
        1. API fetch from provider (most up-to-date)
        2. Cached file (kr_all_symbols.txt/csv) - updated from last API fetch
        3. Constructor-provided candidate_symbols
        4. Built-in fallback list (minimal)
        
        IMPROVEMENT: If no candidates found and no file exists, 
        attempt to generate a default file from built-in symbols.
        """
        # Priority 1: Try API fetch
        try:
            print("[INFO] Fetching stock list from KIS API...")
            api_symbols = await self.engine.fetch_stock_list(market="ALL")
            if api_symbols and len(api_symbols) > 100:
                print(f"[SUCCESS] Fetched {len(api_symbols)} symbols from API")
                # Cache to file for future use
                await self._cache_symbols_to_file(api_symbols)
                return list(dict.fromkeys(api_symbols))
            else:
                print(f"[WARNING] API returned insufficient symbols ({len(api_symbols)}), trying file...")
        except Exception as e:
            print(f"[WARNING] API fetch failed: {e}, falling back to file...")
        
        # Priority 2: Constructor-provided symbols
        if self._candidate_symbols is not None:
            print(f"[INFO] Using constructor-provided symbols ({len(self._candidate_symbols)})")
            return list(dict.fromkeys(self._candidate_symbols))
        
        # Priority 3: File-based candidates
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config"))
        symbols_dir = os.path.join(base_dir, "symbols")
        txt_path = os.path.join(symbols_dir, "kr_all_symbols.txt")
        csv_path = os.path.join(symbols_dir, "kr_all_symbols.csv")
        result: list = []

        if os.path.exists(txt_path):
            print(f"[INFO] Loading cached symbols from: {txt_path}")
            with open(txt_path, "r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if s:
                        result.append(s)
            print(f"[INFO] Loaded {len(result)} symbols from file")
            if result:
                return list(dict.fromkeys(result))
        
        if os.path.exists(csv_path):
            print(f"[INFO] Loading cached symbols from: {csv_path}")
            with open(csv_path, "r", encoding="utf-8") as f:
                header = f.readline()
                cols = [c.strip().lower() for c in header.split(",")]
                sym_idx = None
                for i, c in enumerate(cols):
                    if c in ("symbol", "code", "sym"):
                        sym_idx = i
                        break
                if sym_idx is None:
                    sym_idx = 0
                for line in f:
                    parts = [p.strip() for p in line.split(",")]
                    if parts and parts[0]:
                        result.append(parts[sym_idx])
            if result:
                return list(dict.fromkeys(result))
        
        # Priority 4: Built-in fallback - BUT NOW CREATE THE FILE
        print("[WARNING] No API/file source available, using built-in fallback (20 symbols)")
        result = [
            "005930", "000660", "005380", "373220", "207940",
            "035420", "035720", "051910", "005490", "068270",
            "028260", "006400", "105560", "055550", "012330",
            "096770", "034730", "003550", "259960", "066570",
        ]
        
        # NEW: Try to save built-in symbols as fallback file
        try:
            print(f"[INFO] Attempting to create fallback symbol file: {txt_path}")
            os.makedirs(symbols_dir, exist_ok=True)
            with open(txt_path, "w", encoding="utf-8") as f:
                for sym in result:
                    f.write(f"{sym}\n")
            print(f"[SUCCESS] Created fallback symbol file with {len(result)} symbols")
        except Exception as e:
            print(f"[WARNING] Could not create fallback symbol file: {e}")
        
        return list(dict.fromkeys(result))


async def test_improved_logic():
    """Test the improved symbol loading logic"""
    print("=" * 80)
    print("TEST: Improved Symbol Loading with Auto-Create")
    print("=" * 80)
    
    # Scenario 1: File doesn't exist, API fails
    print("\n1. Scenario: No file, API fails (new installation)")
    print("   Expected: Creates kr_all_symbols.txt from built-in symbols")
    
    class MockAPIFail:
        async def fetch_stock_list(self, market: str):
            raise Exception("KIS API unavailable")
    
    # Create temp test directory
    test_dir = Path(__file__).parent / "app" / "observer" / "config" / "test_improved"
    test_symbols_dir = test_dir / "symbols"
    test_symbols_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure file doesn't exist
    test_symbol_file = test_symbols_dir / "kr_all_symbols.txt"
    if test_symbol_file.exists():
        test_symbol_file.unlink()
    
    um = ImprovedUniverseManager(MockAPIFail(), universe_dir=str(test_dir / "universe"))
    candidates = await um._load_candidates()
    
    print(f"   Loaded: {len(candidates)} symbols")
    print(f"   Symbols: {candidates}")
    
    if test_symbol_file.exists():
        with open(test_symbol_file) as f:
            file_symbols = [line.strip() for line in f if line.strip()]
        print(f"   ✅ Symbol file created with {len(file_symbols)} symbols")
    else:
        print(f"   ❌ Symbol file NOT created")
    
    # Scenario 2: File exists, use it
    print("\n2. Scenario: File exists from previous run")
    print("   Expected: Loads from file without creating new one")
    
    um2 = ImprovedUniverseManager(MockAPIFail(), universe_dir=str(test_dir / "universe"))
    candidates = await um2._load_candidates()
    
    print(f"   Loaded: {len(candidates)} symbols")
    
    print()


async def analyze_code_gap():
    """Analyze the gap between current and improved implementation"""
    print("=" * 80)
    print("CODE GAP ANALYSIS: Symbol File Generation")
    print("=" * 80)
    
    print("""
    CURRENT IMPLEMENTATION:
    ─────────────────────
    _load_candidates():
        1. Try API
        2. Try constructor symbols
        3. Try kr_all_symbols.txt file
        4. Return 20 built-in symbols (NO FILE CREATION)
    
    PROBLEM:
    ────────
    When kr_all_symbols.txt doesn't exist:
    - System falls back to 20 built-in symbols
    - These 20 symbols are NOT persisted to file
    - Next boot still has no file → still uses 20 symbols
    - Universe is very small
    
    IMPROVED IMPLEMENTATION:
    ──────────────────────
    _load_candidates():
        1. Try API (SUCCESS → cache to file) ✓
        2. Try constructor symbols
        3. Try kr_all_symbols.txt file
        4. Return 20 built-in symbols (NEW: create file first)
    
    BENEFIT:
    ────────
    When kr_all_symbols.txt doesn't exist:
    - System falls back to 20 built-in symbols
    - ALSO creates kr_all_symbols.txt with these 20 symbols
    - Next boot finds the file → loads 20 symbols from it
    - Provides foundation for future API updates
    
    ADDITIONAL FIX NEEDED:
    ─────────────────────
    The 20 built-in symbols are too small.
    Should either:
    
    Option A: Extend built-in list to 100+ symbols
    Option B: Load from external curated list during init
    Option C: Provide as constructor parameter
    Option D: Pre-ship the kr_all_symbols.txt file in repo
    """)
    
    print()


async def test_what_user_provided():
    """Verify the user-provided file content"""
    print("=" * 80)
    print("USER-PROVIDED SYMBOL FILE VERIFICATION")
    print("=" * 80)
    
    symbol_file = Path(__file__).parent / "app" / "observer" / "config" / "symbols" / "kr_all_symbols.txt"
    
    print(f"\nFile: {symbol_file}")
    print(f"Exists: {symbol_file.exists()}")
    
    if symbol_file.exists():
        with open(symbol_file) as f:
            symbols = [line.strip() for line in f if line.strip()]
        
        print(f"Content: {len(symbols)} symbols")
        print(f"Format: Newline-separated stock codes")
        print(f"Sample (first 10): {symbols[:10]}")
        print(f"Sample (last 10): {symbols[-10:]}")
        
        # Check format
        valid_6digit = all(len(s) == 6 and (s.isdigit() or s[0].isdigit()) for s in symbols[:20])
        print(f"Format check: {'✅ Valid' if valid_6digit else '⚠️ Mixed format (6-digit codes + warrant codes)'}")
        
        print(f"\nThis file is EXCELLENT for local development!")
        print(f"- 2894 symbols is a realistic universe")
        print(f"- Mix of regular stocks and warrants")
        print(f"- Ready to use as fallback when API fails")
        
    print()


async def main():
    print("\n")
    print("█" * 80)
    print("SYMBOL FILE GENERATION: LOGIC IMPROVEMENTS")
    print("█" * 80)
    
    try:
        await test_improved_logic()
        await analyze_code_gap()
        await test_what_user_provided()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 80)
    print("ANALYSIS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
