
import asyncio
import logging
import json
import os
from pathlib import Path
from datetime import datetime
from src.universe.symbol_generator import SymbolGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Test")

class MockEngine:
    async def fetch_stock_list(self, market="ALL"):
        # Simulate API failure for testing retry/fallback
        # raise Exception("API Connection Failed")
        return ["005930", "000660"] + [f"TEST{i}" for i in range(500)]

    async def _fetch_stock_list_from_file(self):
        return ["MASTER1", "MASTER2"] + [f"TEST{i}" for i in range(500)]

async def run_test():
    engine = MockEngine()
    # Use a test directory
    test_base = Path("d:/development/prj_obs/test_data")
    test_base.mkdir(parents=True, exist_ok=True)
    os.environ["OBSERVER_DATA_DIR"] = str(test_base)
    
    generator = SymbolGenerator(engine)
    
    logger.info("--- Test 1: Normal Execution ---")
    filepath = await generator.execute()
    logger.info(f"Generated filepath: {filepath}")
    
    if generator.state_file.exists():
        with open(generator.state_file, "r") as f:
            logger.info(f"State: {f.read()}")
            
    if generator.health_file.exists():
        with open(generator.health_file, "r") as f:
            logger.info(f"Health: {f.read()}")

    logger.info("--- Test 2: Skip Execution (Already Success) ---")
    filepath_skip = await generator.execute()
    logger.info(f"Skip execution result: {filepath_skip}")

if __name__ == "__main__":
    asyncio.run(run_test())
