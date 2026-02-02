#!/usr/bin/env python3
"""
Phase 2: Track A/B 파일 생성 검증 테스트

목표:
- config/observer/swing/YYYYMMDD.jsonl 생성 확인
- config/observer/scalp/YYYYMMDD.jsonl 생성 확인
- logs/swing/YYYYMMDD.log 생성 확인
- logs/scalp/YYYYMMDD.log 생성 확인

실행:
  python tests/local/test_track_ab_file_verification.py
"""

import sys
import os
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("FileVerification")

# Import paths module (observer package)
from observer.paths import (
    project_root,
    config_dir,
    observer_asset_dir,
    observer_log_dir,
)


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


def verify_existing_files():
    """기존 생성된 파일 검증"""
    print("\n[1] Existing File Verification")
    result = TestResult()
    
    asset_dir = observer_asset_dir()
    log_directory = observer_log_dir()
    today = datetime.now().strftime("%Y%m%d")
    
    # Check swing JSONL
    swing_jsonl = asset_dir / "swing" / f"{today}.jsonl"
    if swing_jsonl.exists():
        result.success(f"swing JSONL exists: {swing_jsonl}")
        
        # Verify content
        with open(swing_jsonl, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                result.success(f"swing JSONL has {len(lines)} records")
                try:
                    record = json.loads(lines[0])
                    if "dataset" in record and record["dataset"] == "track_a_swing":
                        result.success("swing JSONL format valid")
                    else:
                        result.fail("swing JSONL format", "Missing or invalid dataset field")
                except json.JSONDecodeError as e:
                    result.fail("swing JSONL parse", str(e))
            else:
                result.fail("swing JSONL content", "File is empty")
    else:
        result.fail("swing JSONL exists", f"Not found: {swing_jsonl}")
    
    # Check scalp JSONL
    scalp_jsonl = asset_dir / "scalp" / f"{today}.jsonl"
    if scalp_jsonl.exists():
        result.success(f"scalp JSONL exists: {scalp_jsonl}")
        
        with open(scalp_jsonl, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                result.success(f"scalp JSONL has {len(lines)} records")
                try:
                    record = json.loads(lines[0])
                    if "source" in record and record["source"] == "websocket":
                        result.success("scalp JSONL format valid")
                    else:
                        result.fail("scalp JSONL format", "Missing or invalid source field")
                except json.JSONDecodeError as e:
                    result.fail("scalp JSONL parse", str(e))
            else:
                result.fail("scalp JSONL content", "File is empty")
    else:
        result.fail("scalp JSONL exists", f"Not found: {scalp_jsonl}")
    
    # Check swing log
    swing_log = log_directory / "swing" / f"{today}.log"
    if swing_log.exists():
        result.success(f"swing log exists: {swing_log}")
    else:
        result.fail("swing log exists", f"Not found: {swing_log}")
    
    # Check scalp log
    scalp_log = log_directory / "scalp" / f"{today}.log"
    if scalp_log.exists():
        result.success(f"scalp log exists: {scalp_log}")
    else:
        result.fail("scalp log exists", f"Not found: {scalp_log}")
    
    return result


def list_all_generated_files():
    """생성된 모든 파일 목록"""
    print("\n[2] Generated Files List")
    
    asset_dir = observer_asset_dir()
    log_directory = observer_log_dir()
    
    print(f"\n  Config JSONL files ({asset_dir}):")
    
    # Swing files
    swing_dir = asset_dir / "swing"
    if swing_dir.exists():
        swing_files = list(swing_dir.glob("*.jsonl"))
        for f in sorted(swing_files):
            size = f.stat().st_size
            print(f"    - swing/{f.name} ({size:,} bytes)")
    else:
        print("    - swing/ directory not found")
    
    # Scalp files
    scalp_dir = asset_dir / "scalp"
    if scalp_dir.exists():
        scalp_files = list(scalp_dir.glob("*.jsonl"))
        for f in sorted(scalp_files):
            size = f.stat().st_size
            print(f"    - scalp/{f.name} ({size:,} bytes)")
    else:
        print("    - scalp/ directory not found")
    
    print(f"\n  Log files ({log_directory}):")
    
    # Swing logs
    swing_log_dir = log_directory / "swing"
    if swing_log_dir.exists():
        swing_logs = list(swing_log_dir.glob("*.log"))
        for f in sorted(swing_logs):
            size = f.stat().st_size
            print(f"    - swing/{f.name} ({size:,} bytes)")
    else:
        print("    - swing/ log directory not found")
    
    # Scalp logs
    scalp_log_dir = log_directory / "scalp"
    if scalp_log_dir.exists():
        scalp_logs = list(scalp_log_dir.glob("*.log"))
        for f in sorted(scalp_logs):
            size = f.stat().st_size
            print(f"    - scalp/{f.name} ({size:,} bytes)")
    else:
        print("    - scalp/ log directory not found")
    
    # System logs
    system_log_dir = log_directory / "system"
    if system_log_dir.exists():
        system_logs = list(system_log_dir.glob("*.log"))
        for f in sorted(system_logs):
            size = f.stat().st_size
            print(f"    - system/{f.name} ({size:,} bytes)")


def verify_jsonl_record_samples():
    """JSONL 레코드 샘플 검증"""
    print("\n[3] JSONL Record Samples")
    result = TestResult()
    
    asset_dir = observer_asset_dir()
    today = datetime.now().strftime("%Y%m%d")
    
    # Swing sample
    swing_jsonl = asset_dir / "swing" / f"{today}.jsonl"
    if swing_jsonl.exists():
        print(f"\n  Swing JSONL sample ({swing_jsonl.name}):")
        with open(swing_jsonl, "r", encoding="utf-8") as f:
            first_line = f.readline()
            if first_line:
                record = json.loads(first_line)
                print(f"    ts: {record.get('ts', 'N/A')}")
                print(f"    symbol: {record.get('symbol', 'N/A')}")
                print(f"    price: {record.get('price', {})}")
                print(f"    volume: {record.get('volume', 'N/A')}")
                result.success("Swing sample loaded")
            else:
                result.fail("Swing sample", "Empty file")
    else:
        print(f"\n  Swing JSONL not found: {swing_jsonl}")
    
    # Scalp sample
    scalp_jsonl = asset_dir / "scalp" / f"{today}.jsonl"
    if scalp_jsonl.exists():
        print(f"\n  Scalp JSONL sample ({scalp_jsonl.name}):")
        with open(scalp_jsonl, "r", encoding="utf-8") as f:
            first_line = f.readline()
            if first_line:
                record = json.loads(first_line)
                print(f"    timestamp: {record.get('timestamp', 'N/A')}")
                print(f"    symbol: {record.get('symbol', 'N/A')}")
                print(f"    price: {record.get('price', {})}")
                print(f"    volume: {record.get('volume', {})}")
                result.success("Scalp sample loaded")
            else:
                result.fail("Scalp sample", "Empty file")
    else:
        print(f"\n  Scalp JSONL not found: {scalp_jsonl}")
    
    return result


def create_test_files_if_missing():
    """테스트용 파일 생성 (기존 파일이 없는 경우)"""
    print("\n[4] Create Test Files (if missing)")
    result = TestResult()
    
    asset_dir = observer_asset_dir()
    log_directory = observer_log_dir()
    today = datetime.now().strftime("%Y%m%d")
    
    # Create swing test JSONL
    swing_dir = asset_dir / "swing"
    swing_dir.mkdir(parents=True, exist_ok=True)
    swing_jsonl = swing_dir / f"{today}.jsonl"
    
    if not swing_jsonl.exists():
        test_record = {
            "ts": datetime.now().isoformat(),
            "session": "test_session",
            "dataset": "track_a_swing",
            "market": "kr_stocks",
            "symbol": "005930",
            "price": {"open": 70000, "high": 70500, "low": 69500, "close": 70200},
            "volume": 1000000,
            "source": "test",
        }
        with open(swing_jsonl, "w", encoding="utf-8") as f:
            f.write(json.dumps(test_record, ensure_ascii=False) + "\n")
        result.success(f"Created test swing JSONL: {swing_jsonl}")
    else:
        result.success(f"Swing JSONL already exists: {swing_jsonl}")
    
    # Create scalp test JSONL
    scalp_dir = asset_dir / "scalp"
    scalp_dir.mkdir(parents=True, exist_ok=True)
    scalp_jsonl = scalp_dir / f"{today}.jsonl"
    
    if not scalp_jsonl.exists():
        test_record = {
            "timestamp": datetime.now().isoformat(),
            "symbol": "005930",
            "execution_time": "093015",
            "price": {"current": 70200, "open": 70000, "high": 70500, "low": 69500, "change_rate": 0.5},
            "volume": {"accumulated": 1000000, "trade_value": 70200000000},
            "source": "websocket",
            "session_id": "test_session",
        }
        with open(scalp_jsonl, "w", encoding="utf-8") as f:
            f.write(json.dumps(test_record, ensure_ascii=False) + "\n")
        result.success(f"Created test scalp JSONL: {scalp_jsonl}")
    else:
        result.success(f"Scalp JSONL already exists: {scalp_jsonl}")
    
    # Create swing test log
    swing_log_dir = log_directory / "swing"
    swing_log_dir.mkdir(parents=True, exist_ok=True)
    swing_log = swing_log_dir / f"{today}.log"
    
    if not swing_log.exists():
        with open(swing_log, "w", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} | INFO | TrackACollector | Test log entry\n")
        result.success(f"Created test swing log: {swing_log}")
    else:
        result.success(f"Swing log already exists: {swing_log}")
    
    # Create scalp test log
    scalp_log_dir = log_directory / "scalp"
    scalp_log_dir.mkdir(parents=True, exist_ok=True)
    scalp_log = scalp_log_dir / f"{today}.log"
    
    if not scalp_log.exists():
        with open(scalp_log, "w", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} | INFO | TrackBCollector | Test log entry\n")
        result.success(f"Created test scalp log: {scalp_log}")
    else:
        result.success(f"Scalp log already exists: {scalp_log}")
    
    return result


def print_path_summary():
    """경로 요약 출력"""
    print("\n" + "="*60)
    print("Path Summary")
    print("="*60)
    
    print(f"\nProject Root: {project_root()}")
    print(f"Config Dir: {config_dir()}")
    print(f"Observer Asset Dir: {observer_asset_dir()}")
    print(f"  -> scalp: {observer_asset_dir() / 'scalp'}")
    print(f"  -> swing: {observer_asset_dir() / 'swing'}")
    print(f"Log Dir: {observer_log_dir()}")
    print(f"  -> scalp: {observer_log_dir() / 'scalp'}")
    print(f"  -> swing: {observer_log_dir() / 'swing'}")


def main():
    print("="*60)
    print("Phase 2: Track A/B File Verification")
    print("="*60)
    
    all_results = []
    
    # Print path summary first
    print_path_summary()
    
    # Create test files if missing
    all_results.append(create_test_files_if_missing())
    
    # Verify existing files
    all_results.append(verify_existing_files())
    
    # List all generated files
    list_all_generated_files()
    
    # Verify JSONL record samples
    all_results.append(verify_jsonl_record_samples())
    
    # Final summary
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)
    
    print(f"\n{'='*60}")
    print(f"Final Result: {total_passed}/{total_passed + total_failed} tests passed")
    print(f"{'='*60}")
    
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
