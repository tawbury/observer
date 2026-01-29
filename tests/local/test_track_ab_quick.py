#!/usr/bin/env python3
"""
Track A/B Quick Test - 소수 심볼로 빠른 테스트

실행:
  python tests/local/test_track_ab_quick.py
"""

import sys
import os
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
APP_ROOT = PROJECT_ROOT / "app" / "observer"
sys.path.insert(0, str(APP_ROOT / "src"))
sys.path.insert(0, str(APP_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("QuickTest")

# Load .env
from dotenv import load_dotenv
env_path = APP_ROOT / ".env"
if env_path.exists():
    load_dotenv(env_path)
    log.info(f"Loaded .env from {env_path}")

from paths import observer_asset_dir, observer_log_dir


async def test_track_a_quick():
    """Track A 빠른 테스트 - 3개 심볼만"""
    log.info("="*60)
    log.info("Track A Quick Test")
    log.info("="*60)
    
    from provider import KISAuth, ProviderEngine
    
    app_key = os.getenv("KIS_APP_KEY") or os.getenv("REAL_APP_KEY")
    app_secret = os.getenv("KIS_APP_SECRET") or os.getenv("REAL_APP_SECRET")
    
    if not app_key or not app_secret:
        log.error("KIS credentials not found")
        return False
    
    # Initialize
    auth = KISAuth(app_key, app_secret, is_virtual=False)
    engine = ProviderEngine(auth, is_virtual=False)
    
    # Test symbols (대표 종목 3개)
    test_symbols = ["005930", "000660", "035720"]  # 삼성전자, SK하이닉스, 카카오
    
    today = datetime.now().strftime("%Y%m%d")
    swing_dir = observer_asset_dir() / "swing"
    swing_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = swing_dir / f"{today}.jsonl"
    
    log.info(f"Testing {len(test_symbols)} symbols: {test_symbols}")
    log.info(f"Output: {jsonl_path}")
    
    results = []
    for symbol in test_symbols:
        try:
            log.info(f"Fetching {symbol}...")
            data = await engine.fetch_current_price(symbol)
            results.append({"symbol": symbol, "data": data})
            log.info(f"  [OK] {symbol}")
        except Exception as e:
            log.error(f"  [FAIL] {symbol}: {e}")
    
    # Write JSONL
    written = 0
    with open(jsonl_path, "a", encoding="utf-8") as f:
        for item in results:
            sym = item["symbol"]
            payload = item["data"]
            inst = (payload.get("instruments") or [{}])[0]
            price = inst.get("price") or {}
            record = {
                "ts": datetime.now().isoformat(),
                "session": "quick_test",
                "dataset": "track_a_swing",
                "market": "kr_stocks",
                "symbol": sym,
                "price": {
                    "open": price.get("open"),
                    "high": price.get("high"),
                    "low": price.get("low"),
                    "close": price.get("close"),
                },
                "volume": inst.get("volume"),
                "source": "kis_api_test",
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1
    
    await engine.close()
    
    log.info(f"Written {written} records to {jsonl_path}")
    
    # Verify
    if jsonl_path.exists():
        size = jsonl_path.stat().st_size
        log.info(f"[PASS] swing JSONL created: {size} bytes")
        return True
    else:
        log.error("[FAIL] swing JSONL not created")
        return False


async def test_track_b_quick():
    """Track B 빠른 테스트 - 로그 파일 생성만"""
    log.info("="*60)
    log.info("Track B Quick Test (Log only)")
    log.info("="*60)
    
    today = datetime.now().strftime("%Y%m%d")
    scalp_dir = observer_asset_dir() / "scalp"
    scalp_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = scalp_dir / f"{today}.jsonl"
    
    # Simulate scalp data
    test_records = [
        {"symbol": "005930", "price": {"current": 71000, "open": 70500, "high": 71200, "low": 70300}},
        {"symbol": "000660", "price": {"current": 185000, "open": 184000, "high": 186000, "low": 183500}},
        {"symbol": "035720", "price": {"current": 52500, "open": 52000, "high": 53000, "low": 51800}},
    ]
    
    log.info(f"Writing {len(test_records)} simulated scalp records")
    log.info(f"Output: {jsonl_path}")
    
    with open(jsonl_path, "a", encoding="utf-8") as f:
        for data in test_records:
            record = {
                "timestamp": datetime.now().isoformat(),
                "symbol": data["symbol"],
                "execution_time": datetime.now().strftime("%H%M%S"),
                "price": {
                    "current": data["price"]["current"],
                    "open": data["price"]["open"],
                    "high": data["price"]["high"],
                    "low": data["price"]["low"],
                    "change_rate": 0.5,
                },
                "volume": {"accumulated": 100000, "trade_value": 7100000000},
                "source": "websocket_test",
                "session_id": "quick_test",
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    if jsonl_path.exists():
        size = jsonl_path.stat().st_size
        log.info(f"[PASS] scalp JSONL created: {size} bytes")
        return True
    else:
        log.error("[FAIL] scalp JSONL not created")
        return False


def verify_files():
    """생성된 파일 검증"""
    log.info("="*60)
    log.info("File Verification")
    log.info("="*60)
    
    today = datetime.now().strftime("%Y%m%d")
    asset_dir = observer_asset_dir()
    
    files_to_check = [
        ("swing JSONL", asset_dir / "swing" / f"{today}.jsonl"),
        ("scalp JSONL", asset_dir / "scalp" / f"{today}.jsonl"),
    ]
    
    all_ok = True
    for name, path in files_to_check:
        if path.exists():
            size = path.stat().st_size
            with open(path, "r", encoding="utf-8") as f:
                lines = len(f.readlines())
            log.info(f"[PASS] {name}: {path.name} ({size:,} bytes, {lines} records)")
        else:
            log.error(f"[FAIL] {name}: not found")
            all_ok = False
    
    return all_ok


async def main():
    log.info("="*60)
    log.info("Track A/B Quick Test")
    log.info(f"Time: {datetime.now().isoformat()}")
    log.info("="*60)
    
    results = {}
    
    # Track A test
    results["Track A"] = await test_track_a_quick()
    
    # Track B test
    results["Track B"] = await test_track_b_quick()
    
    # Verify
    results["Verification"] = verify_files()
    
    # Summary
    log.info("="*60)
    log.info("SUMMARY")
    log.info("="*60)
    
    for name, ok in results.items():
        status = "[PASS]" if ok else "[FAIL]"
        log.info(f"  {status} {name}")
    
    all_passed = all(results.values())
    log.info(f"\nOverall: {'PASS' if all_passed else 'FAIL'}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
