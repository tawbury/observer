"""
Data Directory Structure Test
생성일: 2026-01-28
설명: 데이터 디렉토리 구조 및 JSONL 파일 위치 검증
"""

import pytest
from pathlib import Path


def test_data_directory_structure():
    """데이터 디렉토리 구조 검증"""
    project_root = Path(__file__).parent.parent
    
    # 필수 디렉토리 경로 (소스: config, 저장소: data)
    scalp_source_dir = project_root / 'config' / 'observer' / 'scalp'
    swing_source_dir = project_root / 'config' / 'observer' / 'swing'
    
    # 소스 디렉토리 존재 확인
    assert scalp_source_dir.exists(), f"Scalp 소스 디렉토리 없음: {scalp_source_dir}"
    assert swing_source_dir.exists(), f"Swing 소스 디렉토리 없음: {swing_source_dir}"
    
    print(f"✓ Scalp Source Dir: {scalp_source_dir}")
    print(f"✓ Swing Source Dir: {swing_source_dir}")


def test_scalp_data_files():
    """Scalp 소스 데이터 파일 검증"""
    project_root = Path(__file__).parent.parent
    scalp_source_dir = project_root / 'config' / 'observer' / 'scalp'
    
    if scalp_source_dir.exists():
        jsonl_files = list(scalp_source_dir.glob("*.jsonl"))
        
        print(f"\nScalp JSONL 파일 개수: {len(jsonl_files)}")
        for f in jsonl_files:
            print(f"  - {f.name}")
        
        # 적어도 하나의 JSONL 파일이 있어야 함
        assert len(jsonl_files) > 0, "Scalp 소스 디렉토리에 JSONL 파일이 없음"
    else:
        pytest.skip(f"Scalp 소스 디렉토리 없음: {scalp_source_dir}")


def test_swing_data_files():
    """Swing 소스 데이터 파일 검증"""
    project_root = Path(__file__).parent.parent
    swing_source_dir = project_root / 'config' / 'observer' / 'swing'
    
    if swing_source_dir.exists():
        jsonl_files = list(swing_source_dir.glob("*.jsonl"))
        
        print(f"\nSwing JSONL 파일 개수: {len(jsonl_files)}")
        for f in jsonl_files:
            print(f"  - {f.name}")
        
        # 적어도 하나의 JSONL 파일이 있어야 함
        assert len(jsonl_files) > 0, "Swing 소스 디렉토리에 JSONL 파일이 없음"
    else:
        pytest.skip(f"Swing 소스 디렉토리 없음: {swing_source_dir}")


def test_migration_script_paths():
    """마이그레이션 스크립트 경로 설정 검증"""
    from pathlib import Path
    
    # 마이그레이션 스크립트의 경로 계산 시뮬레이션
    # migrate_jsonl_to_db.py가 위치한 경로: src/db/migrate_jsonl_to_db.py
    script_path = Path(__file__).parent.parent / 'src' / 'db' / 'migrate_jsonl_to_db.py'
    
    if script_path.exists():
        # script_path에서 project_root까지: parent x 3
        # migrate_jsonl_to_db.py -> db/ -> src/ -> prj_obs/
        project_root = script_path.parent.parent.parent
        scalp_source_dir = project_root / 'config' / 'observer' / 'scalp'
        swing_source_dir = project_root / 'config' / 'observer' / 'swing'
        
        print(f"\nScript Path: {script_path}")
        print(f"Project Root: {project_root}")
        print(f"Scalp Source Dir: {scalp_source_dir}")
        print(f"Swing Source Dir: {swing_source_dir}")
        
        # 경로가 올바르게 계산되었는지 확인
        assert scalp_source_dir.exists(), f"Scalp 소스 경로 오류: {scalp_source_dir}"
        assert swing_source_dir.exists(), f"Swing 소스 경로 오류: {swing_source_dir}"
    else:
        print(f"마이그레이션 스크립트 없음: {script_path}")


def test_data_vs_test_data_separation():
    """소스 데이터와 테스트 데이터 분리 확인"""
    project_root = Path(__file__).parent.parent
    
    # 소스 데이터 디렉토리 (config)
    scalp_source_dir = project_root / 'config' / 'observer' / 'scalp'
    swing_source_dir = project_root / 'config' / 'observer' / 'swing'
    
    # 테스트 데이터 디렉토리
    test_data_dir = project_root / 'tests' / 'test_data'
    
    assert test_data_dir.exists(), "테스트 데이터 디렉토리 없음"
    assert scalp_source_dir != test_data_dir, "Scalp 소스 데이터와 테스트 데이터 경로가 같음"
    assert swing_source_dir != test_data_dir, "Swing 소스 데이터와 테스트 데이터 경로가 같음"
    
    print(f"\n✓ Scalp 소스 데이터: {scalp_source_dir}")
    print(f"✓ Swing 소스 데이터: {swing_source_dir}")
    print(f"✓ 테스트 데이터: {test_data_dir}")
    print("✓ 데이터 경로 분리 확인 완료")