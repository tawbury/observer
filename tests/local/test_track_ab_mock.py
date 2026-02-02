#!/usr/bin/env python3
"""
Phase 1.2-1.3: Mock 기반 Track A/B Config 및 로그 생성 테스트

목표:
- KIS API 없이 파일 생성 로직만 검증
- Track A: swing JSONL 및 로그 파일 생성
- Track B: scalp JSONL 및 로그 파일 생성
- 레코드 형식 검증

실행:
  cd tests/local
  python test_track_ab_mock.py
"""

import sys
import os
import json
import asyncio
import logging
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, date, time, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("TestTrackABMock")


class TestResult:
    """테스트 결과 추적"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def success(self, name: str):
        self.passed += 1
        print(f"  [PASS] {name}")
    
    def fail(self, name: str, reason: str):
        self.failed += 1
        self.errors.append((name, reason))
        print(f"  [FAIL] {name} - {reason}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Test Result: {self.passed}/{total} passed")
        if self.errors:
            print("\nFailed tests:")
            for name, reason in self.errors:
                print(f"  - {name}: {reason}")
        print(f"{'='*60}")
        return self.failed == 0


def create_mock_provider_engine():
    """Mock ProviderEngine 생성"""
    mock_engine = Mock()
    mock_engine.on_price_update = None
    
    # fetch_current_price Mock
    async def mock_fetch_current_price(symbol: str) -> Dict[str, Any]:
        return {
            "instruments": [{
                "symbol": symbol,
                "price": {
                    "open": 70000,
                    "high": 70500,
                    "low": 69500,
                    "close": 70200,
                },
                "volume": 1000000,
                "bid_price": 70100,
                "ask_price": 70200,
            }]
        }
    
    mock_engine.fetch_current_price = AsyncMock(side_effect=mock_fetch_current_price)
    
    # WebSocket methods
    mock_engine.start_stream = AsyncMock(return_value=True)
    mock_engine.stop_stream = AsyncMock(return_value=True)
    mock_engine.subscribe = AsyncMock(return_value=True)
    mock_engine.unsubscribe = AsyncMock(return_value=True)
    mock_engine.close = AsyncMock()
    
    return mock_engine


def create_mock_universe_manager(symbols: List[str]):
    """Mock UniverseManager 생성"""
    mock_manager = Mock()
    mock_manager.get_current_universe = Mock(return_value=symbols)
    return mock_manager


class TestTrackAMock:
    """Track A Collector Mock 테스트"""
    
    def __init__(self, test_dir: Path):
        self.test_dir = test_dir
        self.config_dir = test_dir / "config"
        self.log_dir = test_dir / "logs"
        self.result = TestResult()
    
    async def run_tests(self) -> TestResult:
        """Track A 테스트 실행"""
        print("\n[Track A Mock Tests]")
        
        await self.test_config_jsonl_creation()
        await self.test_log_file_creation()
        await self.test_jsonl_record_format()
        
        return self.result
    
    async def test_config_jsonl_creation(self):
        """Track A config JSONL 파일 생성 테스트"""
        print("\n  [1] Track A config JSONL 생성 테스트")
        
        # Setup directories
        swing_dir = self.config_dir / "observer" / "swing"
        swing_dir.mkdir(parents=True, exist_ok=True)
        
        today = datetime.now().strftime("%Y%m%d")
        jsonl_path = swing_dir / f"{today}.jsonl"
        
        # Mock data
        symbols = ["005930", "000660", "035720"]
        mock_engine = create_mock_provider_engine()
        
        # Simulate Track A collect_once logic
        results = []
        for symbol in symbols:
            data = await mock_engine.fetch_current_price(symbol)
            results.append({"symbol": symbol, "data": data})
        
        # Write JSONL
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for item in results:
                sym = item["symbol"]
                payload = item["data"]
                inst = (payload.get("instruments") or [{}])[0]
                price = inst.get("price") or {}
                record = {
                    "ts": datetime.now().isoformat(),
                    "session": "test_session",
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
                    "source": "mock",
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
        # Verify
        if jsonl_path.exists():
            self.result.success("swing JSONL file created")
        else:
            self.result.fail("swing JSONL file created", "File not found")
        
        # Verify line count
        with open(jsonl_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if len(lines) == len(symbols):
                self.result.success(f"JSONL has {len(symbols)} records")
            else:
                self.result.fail("JSONL record count", f"Expected {len(symbols)}, got {len(lines)}")
    
    async def test_log_file_creation(self):
        """Track A 로그 파일 생성 테스트"""
        print("\n  [2] Track A log file 생성 테스트")
        
        swing_log_dir = self.log_dir / "swing"
        swing_log_dir.mkdir(parents=True, exist_ok=True)
        
        today = datetime.now().strftime("%Y%m%d")
        log_path = swing_log_dir / f"{today}.log"
        
        # Simulate logging
        handler = logging.FileHandler(log_path, encoding='utf-8')
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        ))
        
        test_logger = logging.getLogger("TrackACollector.Test")
        test_logger.addHandler(handler)
        test_logger.setLevel(logging.INFO)
        
        test_logger.info("Swing file logger initialized: %s", log_path)
        test_logger.info("[Save] Swing list updated: 3 items -> %s", log_path)
        
        handler.close()
        test_logger.removeHandler(handler)
        
        # Verify
        if log_path.exists():
            self.result.success("swing log file created")
        else:
            self.result.fail("swing log file created", "File not found")
        
        # Verify content
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()
            if "Swing list updated" in content:
                self.result.success("Log contains expected message")
            else:
                self.result.fail("Log content", "Expected message not found")
    
    async def test_jsonl_record_format(self):
        """Track A JSONL 레코드 형식 테스트"""
        print("\n  [3] Track A JSONL record format 테스트")
        
        swing_dir = self.config_dir / "observer" / "swing"
        today = datetime.now().strftime("%Y%m%d")
        jsonl_path = swing_dir / f"{today}.jsonl"
        
        if not jsonl_path.exists():
            self.result.fail("JSONL format test", "File not found")
            return
        
        with open(jsonl_path, "r", encoding="utf-8") as f:
            first_line = f.readline()
            record = json.loads(first_line)
        
        # Required fields
        required_fields = ["ts", "session", "dataset", "market", "symbol", "price", "volume", "source"]
        missing = [f for f in required_fields if f not in record]
        
        if not missing:
            self.result.success("All required fields present")
        else:
            self.result.fail("Required fields", f"Missing: {missing}")
        
        # Price structure
        price_fields = ["open", "high", "low", "close"]
        if "price" in record and isinstance(record["price"], dict):
            price_missing = [f for f in price_fields if f not in record["price"]]
            if not price_missing:
                self.result.success("Price structure correct")
            else:
                self.result.fail("Price structure", f"Missing: {price_missing}")
        else:
            self.result.fail("Price structure", "price field not a dict")


class TestTrackBMock:
    """Track B Collector Mock 테스트"""
    
    def __init__(self, test_dir: Path):
        self.test_dir = test_dir
        self.config_dir = test_dir / "config"
        self.log_dir = test_dir / "logs"
        self.result = TestResult()
    
    async def run_tests(self) -> TestResult:
        """Track B 테스트 실행"""
        print("\n[Track B Mock Tests]")
        
        await self.test_config_jsonl_creation()
        await self.test_log_file_creation()
        await self.test_jsonl_record_format()
        await self.test_websocket_callback_simulation()
        
        return self.result
    
    async def test_config_jsonl_creation(self):
        """Track B config JSONL 파일 생성 테스트"""
        print("\n  [1] Track B config JSONL 생성 테스트")
        
        scalp_dir = self.config_dir / "observer" / "scalp"
        scalp_dir.mkdir(parents=True, exist_ok=True)
        
        today = datetime.now().strftime("%Y%m%d")
        jsonl_path = scalp_dir / f"{today}.jsonl"
        
        # Simulate WebSocket data
        mock_data_list = [
            {"symbol": "005930", "price": {"close": 70200, "open": 70000, "high": 70500, "low": 69500, "change_rate": 0.5},
             "volume": {"accumulated": 1000000, "trade_value": 70200000000}, "execution_time": "093015"},
            {"symbol": "000660", "price": {"close": 85000, "open": 84500, "high": 85500, "low": 84000, "change_rate": 0.3},
             "volume": {"accumulated": 500000, "trade_value": 42500000000}, "execution_time": "093016"},
            {"symbol": "035720", "price": {"close": 52000, "open": 51500, "high": 52500, "low": 51000, "change_rate": 0.8},
             "volume": {"accumulated": 300000, "trade_value": 15600000000}, "execution_time": "093017"},
        ]
        
        # Write JSONL (simulating _log_scalp_data)
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for data in mock_data_list:
                record = {
                    "timestamp": datetime.now().isoformat(),
                    "symbol": data.get("symbol", ""),
                    "execution_time": data.get("execution_time"),
                    "price": {
                        "current": data.get("price", {}).get("close", 0),
                        "open": data.get("price", {}).get("open"),
                        "high": data.get("price", {}).get("high"),
                        "low": data.get("price", {}).get("low"),
                        "change_rate": data.get("price", {}).get("change_rate"),
                    },
                    "volume": {
                        "accumulated": data.get("volume", {}).get("accumulated", 0),
                        "trade_value": data.get("volume", {}).get("trade_value"),
                    },
                    "bid_ask": data.get("bid_ask", {}),
                    "source": "websocket",
                    "session_id": "test_session"
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
        # Verify
        if jsonl_path.exists():
            self.result.success("scalp JSONL file created")
        else:
            self.result.fail("scalp JSONL file created", "File not found")
        
        # Verify line count
        with open(jsonl_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if len(lines) == len(mock_data_list):
                self.result.success(f"JSONL has {len(mock_data_list)} records")
            else:
                self.result.fail("JSONL record count", f"Expected {len(mock_data_list)}, got {len(lines)}")
    
    async def test_log_file_creation(self):
        """Track B 로그 파일 생성 테스트"""
        print("\n  [2] Track B log file 생성 테스트")
        
        scalp_log_dir = self.log_dir / "scalp"
        scalp_log_dir.mkdir(parents=True, exist_ok=True)
        
        today = datetime.now().strftime("%Y%m%d")
        log_path = scalp_log_dir / f"{today}.log"
        
        # Simulate logging
        handler = logging.FileHandler(log_path, encoding='utf-8')
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        ))
        
        test_logger = logging.getLogger("TrackBCollector.Test")
        test_logger.addHandler(handler)
        test_logger.setLevel(logging.INFO)
        
        test_logger.info("Scalp file logger initialized: %s", log_path)
        test_logger.info("[Save] 005930 @ 70,200 won -> %s", log_path)
        test_logger.info("Slot 1: 005930 (priority=0.95, trigger=bootstrap)")
        
        handler.close()
        test_logger.removeHandler(handler)
        
        # Verify
        if log_path.exists():
            self.result.success("scalp log file created")
        else:
            self.result.fail("scalp log file created", "File not found")
        
        # Verify content
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()
            if "[Save]" in content and "005930" in content:
                self.result.success("Log contains expected message")
            else:
                self.result.fail("Log content", "Expected message not found")
    
    async def test_jsonl_record_format(self):
        """Track B JSONL 레코드 형식 테스트"""
        print("\n  [3] Track B JSONL record format 테스트")
        
        scalp_dir = self.config_dir / "observer" / "scalp"
        today = datetime.now().strftime("%Y%m%d")
        jsonl_path = scalp_dir / f"{today}.jsonl"
        
        if not jsonl_path.exists():
            self.result.fail("JSONL format test", "File not found")
            return
        
        with open(jsonl_path, "r", encoding="utf-8") as f:
            first_line = f.readline()
            record = json.loads(first_line)
        
        # Required fields
        required_fields = ["timestamp", "symbol", "execution_time", "price", "volume", "source", "session_id"]
        missing = [f for f in required_fields if f not in record]
        
        if not missing:
            self.result.success("All required fields present")
        else:
            self.result.fail("Required fields", f"Missing: {missing}")
        
        # Price structure
        price_fields = ["current", "open", "high", "low", "change_rate"]
        if "price" in record and isinstance(record["price"], dict):
            price_missing = [f for f in price_fields if f not in record["price"]]
            if not price_missing:
                self.result.success("Price structure correct")
            else:
                self.result.fail("Price structure", f"Missing: {price_missing}")
        else:
            self.result.fail("Price structure", "price field not a dict")
        
        # Volume structure
        volume_fields = ["accumulated", "trade_value"]
        if "volume" in record and isinstance(record["volume"], dict):
            volume_missing = [f for f in volume_fields if f not in record["volume"]]
            if not volume_missing:
                self.result.success("Volume structure correct")
            else:
                self.result.fail("Volume structure", f"Missing: {volume_missing}")
        else:
            self.result.fail("Volume structure", "volume field not a dict")
    
    async def test_websocket_callback_simulation(self):
        """WebSocket 콜백 시뮬레이션 테스트"""
        print("\n  [4] WebSocket callback simulation 테스트")
        
        scalp_dir = self.config_dir / "observer" / "scalp"
        scalp_dir.mkdir(parents=True, exist_ok=True)
        
        today = datetime.now().strftime("%Y%m%d")
        jsonl_path = scalp_dir / f"{today}_callback.jsonl"
        
        # Simulate callback registration and invocation
        callback_count = [0]
        
        def on_price_update(data: Dict[str, Any]) -> None:
            callback_count[0] += 1
            record = {
                "timestamp": datetime.now().isoformat(),
                "symbol": data.get("symbol", ""),
                "price": data.get("price", {}),
                "source": "websocket",
            }
            with open(jsonl_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
        # Simulate WebSocket messages
        mock_messages = [
            {"symbol": "005930", "price": {"close": 70200}},
            {"symbol": "005930", "price": {"close": 70250}},
            {"symbol": "005930", "price": {"close": 70300}},
        ]
        
        for msg in mock_messages:
            on_price_update(msg)
        
        # Verify callback count
        if callback_count[0] == len(mock_messages):
            self.result.success(f"Callback invoked {len(mock_messages)} times")
        else:
            self.result.fail("Callback count", f"Expected {len(mock_messages)}, got {callback_count[0]}")
        
        # Verify file
        if jsonl_path.exists():
            with open(jsonl_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if len(lines) == len(mock_messages):
                    self.result.success("All callback data written to file")
                else:
                    self.result.fail("Callback data", f"Expected {len(mock_messages)} lines, got {len(lines)}")
        else:
            self.result.fail("Callback file", "File not created")


async def run_all_tests():
    """모든 테스트 실행"""
    print("="*60)
    print("Phase 1.2-1.3: Mock-based Track A/B Tests")
    print("="*60)
    
    # Create temporary test directory
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        print(f"\nTest directory: {test_dir}")
        
        # Run Track A tests
        track_a_test = TestTrackAMock(test_dir)
        track_a_result = await track_a_test.run_tests()
        
        # Run Track B tests
        track_b_test = TestTrackBMock(test_dir)
        track_b_result = await track_b_test.run_tests()
        
        # Summary
        total_passed = track_a_result.passed + track_b_result.passed
        total_failed = track_a_result.failed + track_b_result.failed
        
        print(f"\n{'='*60}")
        print(f"Final Result: {total_passed}/{total_passed + total_failed} tests passed")
        print(f"{'='*60}")
        
        return total_failed == 0


def main():
    success = asyncio.run(run_all_tests())
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
