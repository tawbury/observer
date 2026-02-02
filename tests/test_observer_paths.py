#!/usr/bin/env python3
"""
경로 테스트 스크립트 - observer.py의 실제 경로 동작 확인
"""

import sys
import os
from pathlib import Path

# Add src to Python path (observer 패키지 및 paths 모듈)
_root = Path(__file__).resolve().parents[1]  # repo root
sys.path.insert(0, str(_root / "src"))

from observer.paths import observer_asset_dir, project_root, config_dir

def test_paths():
    print("="*60)
    print("OBSERVER.PY 경로 테스트")
    print("="*60)
    
    # 환경 정보 출력
    print(f"현재 작업 디렉토리: {Path.cwd()}")
    print(f"OBSERVER_STANDALONE: {os.environ.get('OBSERVER_STANDALONE', 'NOT_SET')}")
    print(f"OBSERVER_DATA_DIR: {os.environ.get('OBSERVER_DATA_DIR', 'NOT_SET')}")
    print(f"OBSERVER_DEPLOYMENT_MODE: {os.environ.get('OBSERVER_DEPLOYMENT_MODE', 'NOT_SET')}")
    print()
    
    # 프로젝트 루트 확인
    proj_root = project_root()
    print(f"프로젝트 루트: {proj_root}")
    print(f"프로젝트 루트 절대 경로: {proj_root.absolute()}")
    print()
    
    # config_dir() 테스트
    config_dir_path = config_dir()
    print(f"config_dir() 반환 경로: {config_dir_path}")
    print(f"config_dir 절대 경로: {config_dir_path.absolute()}")
    print(f"config_dir 존재 여부: {config_dir_path.exists()}")
    print()
    
    # observer_asset_dir() 테스트
    asset_dir = observer_asset_dir()
    print(f"observer_asset_dir() 반환 경로: {asset_dir}")
    print(f"observer_asset_dir 절대 경로: {asset_dir.absolute()}")
    print(f"observer_asset_dir 존재 여부: {asset_dir.exists()}")
    print()
    
    # swing/scalp 경로 계산
    swing_dir = asset_dir / "swing"
    scalp_dir = asset_dir / "scalp"
    
    print(f"Swing 데이터 경로: {swing_dir}")
    print(f"Swing 절대 경로: {swing_dir.absolute()}")
    print(f"Swing 존재 여부: {swing_dir.exists()}")
    print()
    
    print(f"Scalp 데이터 경로: {scalp_dir}")
    print(f"Scalp 절대 경로: {scalp_dir.absolute()}")
    print(f"Scalp 존재 여부: {scalp_dir.exists()}")
    print()
    
    print("="*60)
    print("경로 테스트 완료")
    print("="*60)

if __name__ == "__main__":
    test_paths()
