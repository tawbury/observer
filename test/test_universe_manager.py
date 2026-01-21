import asyncio
import os
from datetime import date
from pathlib import Path
import sys

# Configure path like other tests
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
from universe import UniverseManager


async def main():
    app_key = os.getenv("KIS_APP_KEY")
    app_secret = os.getenv("KIS_APP_SECRET")
    assert app_key and app_secret, "KIS_APP_KEY/SECRET missing"

    auth = KISAuth(app_key, app_secret, is_virtual=False)
    engine = ProviderEngine(auth, is_virtual=False)

    # Test with file-based candidate list (avoids API rate limits)
    # Use min_price=4000 for price filter (Task 6.1 requirement), min_count=100 for validation
    manager = UniverseManager(engine, min_price=4000, min_count=100)

    today = date.today().isoformat()
    try:
        print("Creating universe snapshot from file-based candidates...")
        print("  min_price=4000 (Task 6.1 price filter), min_count=100")
        path = await manager.create_daily_snapshot(today)
        
        # Load and verify
        universe = manager.load_universe(today)
        
        print({
            "ok": True,
            "snapshot_path": path,
            "universe_count": len(universe),
            "message": f"Universe snapshot created with {len(universe)} symbols",
        })
        
        if len(universe) >= 100:
            print(f"✅ Validation passed: Universe has {len(universe)} symbols (>= 100)")
        else:
            print(f"❌ Validation failed: Only {len(universe)} symbols (need >= 100)")
            
    except Exception as e:
        print({
            "ok": False,
            "error": str(e),
        })
    finally:
        await engine.close()


if __name__ == "__main__":
    # PYTHONPATH is expected to include app/obs_deploy/app/src for imports
    asyncio.run(main())
