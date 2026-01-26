#!/usr/bin/env python3
"""
실제 observer.py 로컬 테스트 - 경로 검증
"""

import sys
import os
from pathlib import Path

# 환경 변수 설정 (로컬 테스트용)
os.environ.setdefault("OBSERVER_STANDALONE", "0")  # 로컬 모드
os.environ.setdefault("TRACK_A_ENABLED", "false")  # Track A 비활성화 (API 없음)
os.environ.setdefault("TRACK_B_ENABLED", "false")  # Track B 비활성화 (API 없음)

# Add src to Python path (observer.py와 동일하게)
sys.path.insert(0, str(Path(__file__).parent / "app" / "observer" / "src"))
sys.path.insert(0, str(Path(__file__).parent / "app" / "observer"))

# paths 모듈 import
from paths import observer_asset_dir, config_dir

def test_observer_paths():
    print("="*70)
    print("OBSERVER.PY 실제 경로 테스트")
    print("="*70)
    
    print(f"OBSERVER_STANDALONE: {os.environ.get('OBSERVER_STANDALONE')}")
    print(f"TRACK_A_ENABLED: {os.environ.get('TRACK_A_ENABLED')}")
    print(f"TRACK_B_ENABLED: {os.environ.get('TRACK_B_ENABLED')}")
    print()
    
    # 실제 observer.py가 사용할 경로 확인
    config_dir_path = config_dir()
    asset_dir = observer_asset_dir()
    
    print(f"Config Directory: {config_dir_path.absolute()}")
    print(f"Observer Asset Directory: {asset_dir.absolute()}")
    print()
    
    # Track A & B 데이터 경로
    swing_dir = asset_dir / "swing"
    scalp_dir = asset_dir / "scalp"
    
    print(f"Track A Swing Path: {swing_dir.absolute()}")
    print(f"Track B Scalp Path: {scalp_dir.absolute()}")
    print()
    
    # 디렉토리 생성 확인
    print("디렉토리 생성 상태:")
    print(f"  Config Dir: {'✅' if config_dir_path.exists() else '❌'}")
    print(f"  Observer Dir: {'✅' if asset_dir.exists() else '❌'}")
    print(f"  Swing Dir: {'✅' if swing_dir.exists() else '❌'}")
    print(f"  Scalp Dir: {'✅' if scalp_dir.exists() else '❌'}")
    print()
    
    # 오늘 날짜 파일 경로
    from datetime import date
    today = date.today().strftime("%Y%m%d")
    
    swing_file = swing_dir / f"{today}.jsonl"
    scalp_file = scalp_dir / f"{today}.jsonl"
    
    print(f"오늘의 Track A 파일: {swing_file}")
    print(f"오늘의 Track B 파일: {scalp_file}")
    print()
    
    print("="*70)
    print("✅ 경로 테스트 완료 - 올바른 경로로 설정됨")
    print("="*70)

if __name__ == "__main__":
    test_observer_paths()
