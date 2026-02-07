"""Quick test for symbol fetching after fix."""
import os
import sys
import asyncio
from pathlib import Path

# Setup - add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

os.environ["RUN_MODE"] = "local"

from src.observer.paths import load_env_by_run_mode
env_result = load_env_by_run_mode()
print(f"Environment: {env_result['run_mode']}, loaded: {len(env_result['files_loaded'])} files")

from src.provider.kis.kis_auth import KISAuth
from src.provider.kis.kis_rest_provider import KISRestProvider

async def test():
    auth = KISAuth()
    provider = KISRestProvider(auth)
    
    print("Fetching stock list...")
    symbols = await provider.fetch_stock_list()
    
    print(f"✅ Loaded {len(symbols)} symbols")
    if symbols:
        print(f"   Sample: {symbols[:5]}")
    
    await auth.close()
    print("✅ Test completed")

if __name__ == "__main__":
    asyncio.run(test())
