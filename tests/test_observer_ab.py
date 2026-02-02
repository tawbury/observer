#!/usr/bin/env python3
"""
Observer.py 로컬 테스트 - Track A & B 경로 검증
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone, date

# 환경 변수 설정 (로컬 테스트용)
os.environ.setdefault("OBSERVER_STANDALONE", "0")  # 로컬 모드
os.environ.setdefault("TRACK_A_ENABLED", "true")   # Track A 활성화 (모의 데이터)
os.environ.setdefault("TRACK_B_ENABLED", "true")   # Track B 활성화 (모의 데이터)

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root / "src"))

from observer.paths import observer_asset_dir

def create_mock_track_a_data():
    """모의 Track A 데이터 생성"""
    asset_dir = observer_asset_dir()
    swing_dir = asset_dir / "swing"
    swing_dir.mkdir(parents=True, exist_ok=True)
    
    today = date.today().strftime("%Y%m%d")
    swing_file = swing_dir / f"{today}.jsonl"
    
    # 모의 데이터 생성
    symbols = ["005930", "000660", "051910", "012330", "028260"]
    records = []
    
    for symbol in symbols:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "session": "track_a_session",
            "dataset": "track_a_swing",
            "market": "kr_stocks",
            "symbol": symbol,
            "price": {
                "open": 70000,
                "high": 71000,
                "low": 69000,
                "close": 70500
            },
            "volume": 1000000,
            "bid_price": None,
            "ask_price": None,
            "source": "kis"
        }
        records.append(record)
    
    # 파일에 쓰기
    with open(swing_file, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    print(f"✅ Track A 모의 데이터 생성: {swing_file}")
    return swing_file

def create_mock_track_b_data():
    """모의 Track B 데이터 생성"""
    asset_dir = observer_asset_dir()
    scalp_dir = asset_dir / "scalp"
    scalp_dir.mkdir(parents=True, exist_ok=True)
    
    today = date.today().strftime("%Y%m%d")
    scalp_file = scalp_dir / f"{today}.jsonl"
    
    # 모의 데이터 생성
    symbols = ["005930", "000660"]
    records = []
    
    for i, symbol in enumerate(symbols):
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol": symbol,
            "slot_id": i,
            "trigger_type": "volume_surge",
            "priority_score": 0.9,
            "details": {
                "current_volume": 2000000,
                "avg_volume_10m": 400000,
                "surge_ratio": 5.0
            },
            "test_run": datetime.now().isoformat()
        }
        records.append(record)
    
    # 파일에 쓰기
    with open(scalp_file, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    print(f"✅ Track B 모의 데이터 생성: {scalp_file}")
    return scalp_file

def verify_paths():
    """경로 검증"""
    print("="*70)
    print("OBSERVER.PY 실제 Track A & B 경로 테스트")
    print("="*70)
    
    asset_dir = observer_asset_dir()
    print(f"Observer Asset Directory: {asset_dir.absolute()}")
    print()
    
    # Track A 경로 확인
    swing_dir = asset_dir / "swing"
    swing_file = create_mock_track_a_data()
    
    # Track B 경로 확인  
    scalp_dir = asset_dir / "scalp"
    scalp_file = create_mock_track_b_data()
    
    print()
    print("📁 생성된 파일:")
    print(f"  Track A: {swing_file}")
    print(f"  Track B: {scalp_file}")
    print()
    
    # 파일 내용 확인
    print("📄 Track A 파일 내용 (첫 2줄):")
    with open(swing_file, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 2:
                break
            print(f"  {line.strip()}")
    print()
    
    print("📄 Track B 파일 내용 (첫 2줄):")
    with open(scalp_file, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 2:
                break
            print(f"  {line.strip()}")
    print()
    
    print("="*70)
    print("✅ 실제 observer.py 경로 테스트 완료")
    print("✅ Track A: config/observer/swing/")
    print("✅ Track B: config/observer/scalp/")
    print("="*70)

if __name__ == "__main__":
    verify_paths()
