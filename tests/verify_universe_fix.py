import asyncio
import json
import logging
from pathlib import Path
from datetime import date
from unittest.mock import MagicMock, patch

from universe.universe_manager import UniverseManager
from collector.track_a_collector import TrackACollector, TrackAConfig
from observer.paths import snapshot_dir

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyFix")

async def test_universe_manager_glob(tmp_path):
    # Setup mock snapshot_dir
    with patch("observer.paths.snapshot_dir", return_value=tmp_path):
        manager = UniverseManager(provider_engine=MagicMock(), market="k3_stocks")
        
        today_str = date.today().strftime("%Y%m%d")
        universe_file = tmp_path / f"{today_str}_extra_k3_stocks.json"
        universe_data = {"symbols": ["005930", "000660"], "metadata": {"date": today_str}}
        
        with open(universe_file, "w") as f:
            json.dump(universe_data, f)
            
        symbols = manager.get_current_universe()
        logger.info(f"Loaded symbols: {symbols}")
        assert symbols == ["005930", "000660"]
        logger.info("✅ UniverseManager glob-based loading test passed")

async def test_collector_retry(tmp_path):
    with patch("collector.track_a_collector.observer_asset_dir", return_value=tmp_path / "assets"), \
         patch("collector.track_a_collector.observer_log_dir", return_value=tmp_path / "logs"):
        
        mock_engine = MagicMock()
        mock_manager = MagicMock()
        
        # Scenario: Empty symbols first, then data
        mock_manager.get_current_universe.side_effect = [[], ["005930"]]
        
        collector = TrackACollector(engine=mock_engine)
        collector._manager = mock_manager
        
        # Fast-forward sleep
        with patch("asyncio.sleep", return_value=None) as mock_sleep:
            # We only want to test the retry loop in collect_once
            # Mock collect_once's internal fetch to return something
            mock_engine.fetch_current_price = asyncio.Future()
            mock_engine.fetch_current_price.set_result({"instruments": [{"price": {"close": 100}}]})
            
            result = await collector.collect_once()
            
            logger.info(f"Collector result: {result}")
            assert result["symbols"] == 1
            assert mock_sleep.call_count == 1
            logger.info("✅ TrackACollector retry logic test passed")

async def main():
    tmp = Path("./tmp_test_dir").resolve()
    tmp.mkdir(parents=True, exist_ok=True)
    try:
        await test_universe_manager_glob(tmp)
        await test_collector_retry(tmp)
    finally:
        # On Windows, logs might still be open for a brief moment
        import shutil
        import time
        for _ in range(3):
            try:
                shutil.rmtree(tmp)
                break
            except Exception:
                time.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
