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

    # Small candidate list just for smoke; set min_count low to avoid failures here
    candidates = [
        "005930", "000660", "005380", "373220", "207940",
        "035420", "035720", "051910", "005490", "068270",
    ]
    manager = UniverseManager(engine, min_price=4000, min_count=1, candidate_symbols=candidates)

    today = date.today().isoformat()
    try:
        path = await manager.create_daily_snapshot(today)
        print({
            "ok": True,
            "snapshot_path": path,
            "message": "Universe snapshot created",
        })
    except Exception as e:
        print({
            "ok": False,
            "error": str(e),
        })


if __name__ == "__main__":
    # PYTHONPATH is expected to include app/obs_deploy/app/src for imports
    asyncio.run(main())
