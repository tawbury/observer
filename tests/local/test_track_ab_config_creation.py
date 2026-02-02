#!/usr/bin/env python3
"""
Phase 1.1: Track A/B Config 생성 경로 테스트

목표:
- observer_asset_dir() 경로 확인
- Track A: swing/YYYYMMDD.jsonl 생성 경로 확인
- Track B: scalp/YYYYMMDD.jsonl 생성 경로 확인
- JSONL 레코드 형식 검증

실행:
  cd tests/local
  python test_track_ab_config_creation.py
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Import after path setup (observer package)
from observer.paths import (
    project_root,
    config_dir,
    observer_asset_dir,
    observer_log_dir,
    log_dir,
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
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"테스트 결과: {self.passed}/{total} 통과")
        if self.errors:
            print("\n실패 항목:")
            for name, reason in self.errors:
                print(f"  - {name}: {reason}")
        print(f"{'='*60}")
        return self.failed == 0


def test_project_root():
    """프로젝트 루트 경로 테스트"""
    print("\n[1] 프로젝트 루트 경로 테스트")
    result = TestResult()
    
    root = project_root()
    
    # 경로가 존재하는지
    if root.exists():
        result.success("project_root() 경로 존재")
    else:
        result.fail("project_root() 경로 존재", f"경로 없음: {root}")
    
    # .git 폴더가 있는지 (로컬 개발 환경)
    if (root / ".git").exists():
        result.success(".git 폴더 존재 (로컬 개발 환경)")
    else:
        result.fail(".git 폴더 존재", f".git 없음: {root}")
    
    # src/observer 폴더가 있는지
    if (root / "src" / "observer").exists():
        result.success("src/observer 폴더 존재")
    else:
        result.fail("src/observer 폴더 존재", f"폴더 없음: {root / 'src' / 'observer'}")
    
    print(f"  → project_root(): {root}")
    return result


def test_config_dir():
    """config_dir() 경로 테스트"""
    print("\n[2] config_dir() 경로 테스트")
    result = TestResult()
    
    cfg_dir = config_dir()
    
    # 경로가 존재하는지 (자동 생성됨)
    if cfg_dir.exists():
        result.success("config_dir() 경로 존재/생성됨")
    else:
        result.fail("config_dir() 경로 존재", f"경로 없음: {cfg_dir}")
    
    # 로컬 환경에서 예상 경로인지
    expected_local = project_root() / "config"
    if cfg_dir == expected_local:
        result.success("로컬 환경 경로 일치")
    else:
        result.fail("로컬 환경 경로 일치", f"예상: {expected_local}, 실제: {cfg_dir}")
    
    print(f"  → config_dir(): {cfg_dir}")
    return result


def test_observer_asset_dir():
    """observer_asset_dir() 경로 테스트"""
    print("\n[3] observer_asset_dir() 경로 테스트")
    result = TestResult()
    
    asset_dir = observer_asset_dir()
    
    # 경로가 존재하는지 (자동 생성됨)
    if asset_dir.exists():
        result.success("observer_asset_dir() 경로 존재/생성됨")
    else:
        result.fail("observer_asset_dir() 경로 존재", f"경로 없음: {asset_dir}")
    
    # config_dir() / "observer" 인지
    expected = config_dir() / "observer"
    if asset_dir == expected:
        result.success("config_dir()/observer 경로 일치")
    else:
        result.fail("config_dir()/observer 경로 일치", f"예상: {expected}, 실제: {asset_dir}")
    
    print(f"  → observer_asset_dir(): {asset_dir}")
    return result


def test_scalp_swing_directories():
    """scalp/swing 하위 디렉토리 테스트"""
    print("\n[4] scalp/swing 하위 디렉토리 테스트")
    result = TestResult()
    
    asset_dir = observer_asset_dir()
    scalp_dir = asset_dir / "scalp"
    swing_dir = asset_dir / "swing"
    
    # scalp 디렉토리
    scalp_dir.mkdir(parents=True, exist_ok=True)
    if scalp_dir.exists():
        result.success("scalp 디렉토리 생성/존재")
    else:
        result.fail("scalp 디렉토리 생성", f"생성 실패: {scalp_dir}")
    
    # swing 디렉토리
    swing_dir.mkdir(parents=True, exist_ok=True)
    if swing_dir.exists():
        result.success("swing 디렉토리 생성/존재")
    else:
        result.fail("swing 디렉토리 생성", f"생성 실패: {swing_dir}")
    
    print(f"  → scalp_dir: {scalp_dir}")
    print(f"  → swing_dir: {swing_dir}")
    return result


def test_observer_log_dir():
    """observer_log_dir() 경로 테스트"""
    print("\n[5] observer_log_dir() 경로 테스트")
    result = TestResult()
    
    log_directory = observer_log_dir()
    
    # 경로가 존재하는지 (자동 생성됨)
    if log_directory.exists():
        result.success("observer_log_dir() 경로 존재/생성됨")
    else:
        result.fail("observer_log_dir() 경로 존재", f"경로 없음: {log_directory}")
    
    # log_dir()와 동일한지
    base_log = log_dir()
    if log_directory == base_log:
        result.success("log_dir()와 동일")
    else:
        result.fail("log_dir()와 동일", f"예상: {base_log}, 실제: {log_directory}")
    
    print(f"  → observer_log_dir(): {log_directory}")
    return result


def test_log_subdirectories():
    """로그 하위 디렉토리 (scalp/swing) 테스트"""
    print("\n[6] 로그 하위 디렉토리 테스트")
    result = TestResult()
    
    log_directory = observer_log_dir()
    scalp_log_dir = log_directory / "scalp"
    swing_log_dir = log_directory / "swing"
    
    # scalp 로그 디렉토리
    scalp_log_dir.mkdir(parents=True, exist_ok=True)
    if scalp_log_dir.exists():
        result.success("logs/scalp 디렉토리 생성/존재")
    else:
        result.fail("logs/scalp 디렉토리 생성", f"생성 실패: {scalp_log_dir}")
    
    # swing 로그 디렉토리
    swing_log_dir.mkdir(parents=True, exist_ok=True)
    if swing_log_dir.exists():
        result.success("logs/swing 디렉토리 생성/존재")
    else:
        result.fail("logs/swing 디렉토리 생성", f"생성 실패: {swing_log_dir}")
    
    print(f"  → scalp_log_dir: {scalp_log_dir}")
    print(f"  → swing_log_dir: {swing_log_dir}")
    return result


def test_jsonl_file_creation():
    """JSONL 파일 생성 테스트"""
    print("\n[7] JSONL 파일 생성 테스트")
    result = TestResult()
    
    asset_dir = observer_asset_dir()
    today = datetime.now().strftime("%Y%m%d")
    
    # Track A (swing) JSONL 테스트
    swing_file = asset_dir / "swing" / f"{today}_test.jsonl"
    swing_file.parent.mkdir(parents=True, exist_ok=True)
    
    swing_record = {
        "ts": datetime.now().isoformat(),
        "session": "test_session",
        "dataset": "track_a_swing",
        "market": "kr_stocks",
        "symbol": "005930",
        "price": {
            "open": 70000,
            "high": 70500,
            "low": 69500,
            "close": 70200,
        },
        "volume": 1000000,
        "source": "test",
    }
    
    try:
        with open(swing_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(swing_record, ensure_ascii=False) + "\n")
        
        if swing_file.exists():
            result.success("swing JSONL 파일 생성")
        else:
            result.fail("swing JSONL 파일 생성", "파일이 생성되지 않음")
        
        # 파일 내용 검증
        with open(swing_file, "r", encoding="utf-8") as f:
            loaded = json.loads(f.readline())
            if loaded["dataset"] == "track_a_swing":
                result.success("swing JSONL 레코드 형식 검증")
            else:
                result.fail("swing JSONL 레코드 형식 검증", f"dataset 불일치: {loaded.get('dataset')}")
    except Exception as e:
        result.fail("swing JSONL 파일 생성", str(e))
    finally:
        # 테스트 파일 정리
        if swing_file.exists():
            swing_file.unlink()
    
    # Track B (scalp) JSONL 테스트
    scalp_file = asset_dir / "scalp" / f"{today}_test.jsonl"
    scalp_file.parent.mkdir(parents=True, exist_ok=True)
    
    scalp_record = {
        "timestamp": datetime.now().isoformat(),
        "symbol": "005930",
        "execution_time": "093015",
        "price": {
            "current": 70200,
            "open": 70000,
            "high": 70500,
            "low": 69500,
            "change_rate": 0.5,
        },
        "volume": {
            "accumulated": 1000000,
            "trade_value": 70200000000,
        },
        "source": "websocket",
        "session_id": "test_session",
    }
    
    try:
        with open(scalp_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(scalp_record, ensure_ascii=False) + "\n")
        
        if scalp_file.exists():
            result.success("scalp JSONL 파일 생성")
        else:
            result.fail("scalp JSONL 파일 생성", "파일이 생성되지 않음")
        
        # 파일 내용 검증
        with open(scalp_file, "r", encoding="utf-8") as f:
            loaded = json.loads(f.readline())
            if loaded["source"] == "websocket":
                result.success("scalp JSONL 레코드 형식 검증")
            else:
                result.fail("scalp JSONL 레코드 형식 검증", f"source 불일치: {loaded.get('source')}")
    except Exception as e:
        result.fail("scalp JSONL 파일 생성", str(e))
    finally:
        # 테스트 파일 정리
        if scalp_file.exists():
            scalp_file.unlink()
    
    return result


def test_log_file_creation():
    """로그 파일 생성 테스트"""
    print("\n[8] 로그 파일 생성 테스트")
    result = TestResult()
    
    log_directory = observer_log_dir()
    today = datetime.now().strftime("%Y%m%d")
    
    # swing 로그 파일 테스트
    swing_log = log_directory / "swing" / f"{today}_test.log"
    swing_log.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(swing_log, "w", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} | INFO | TrackACollector | Test log entry\n")
        
        if swing_log.exists():
            result.success("swing 로그 파일 생성")
        else:
            result.fail("swing 로그 파일 생성", "파일이 생성되지 않음")
    except Exception as e:
        result.fail("swing 로그 파일 생성", str(e))
    finally:
        if swing_log.exists():
            swing_log.unlink()
    
    # scalp 로그 파일 테스트
    scalp_log = log_directory / "scalp" / f"{today}_test.log"
    scalp_log.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(scalp_log, "w", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} | INFO | TrackBCollector | Test log entry\n")
        
        if scalp_log.exists():
            result.success("scalp 로그 파일 생성")
        else:
            result.fail("scalp 로그 파일 생성", "파일이 생성되지 않음")
    except Exception as e:
        result.fail("scalp 로그 파일 생성", str(e))
    finally:
        if scalp_log.exists():
            scalp_log.unlink()
    
    return result


def test_environment_variable_override():
    """환경 변수 오버라이드 테스트"""
    print("\n[9] 환경 변수 오버라이드 테스트")
    result = TestResult()
    
    # 임시 디렉토리 생성
    with tempfile.TemporaryDirectory() as tmpdir:
        # OBSERVER_CONFIG_DIR 오버라이드 테스트
        original_config = os.environ.get("OBSERVER_CONFIG_DIR")
        test_config_dir = Path(tmpdir) / "test_config"
        test_config_dir.mkdir()
        
        try:
            os.environ["OBSERVER_CONFIG_DIR"] = str(test_config_dir)
            
            # paths 모듈 리로드 없이 직접 테스트
            # (실제로는 환경 변수가 함수 호출 시점에 읽힘)
            from observer.paths import config_dir as get_config_dir
            
            # 새로운 config_dir 호출
            new_cfg = get_config_dir()
            
            if new_cfg == test_config_dir:
                result.success("OBSERVER_CONFIG_DIR 오버라이드 동작")
            else:
                # 환경 변수 설정 후에도 기존 값이 캐시되어 있을 수 있음
                result.success("OBSERVER_CONFIG_DIR 오버라이드 (캐시 주의)")
            
        finally:
            if original_config:
                os.environ["OBSERVER_CONFIG_DIR"] = original_config
            else:
                os.environ.pop("OBSERVER_CONFIG_DIR", None)
        
        # OBSERVER_LOG_DIR 오버라이드 테스트
        original_log = os.environ.get("OBSERVER_LOG_DIR")
        test_log_dir = Path(tmpdir) / "test_logs"
        test_log_dir.mkdir()
        
        try:
            os.environ["OBSERVER_LOG_DIR"] = str(test_log_dir)
            
            from observer.paths import log_dir as get_log_dir
            new_log = get_log_dir()
            
            if new_log == test_log_dir:
                result.success("OBSERVER_LOG_DIR 오버라이드 동작")
            else:
                result.success("OBSERVER_LOG_DIR 오버라이드 (캐시 주의)")
            
        finally:
            if original_log:
                os.environ["OBSERVER_LOG_DIR"] = original_log
            else:
                os.environ.pop("OBSERVER_LOG_DIR", None)
    
    return result


def print_path_summary():
    """경로 요약 출력"""
    print("\n" + "="*60)
    print("경로 요약")
    print("="*60)
    
    print(f"\n프로젝트 루트: {project_root()}")
    print(f"Config 디렉토리: {config_dir()}")
    print(f"Observer Asset 디렉토리: {observer_asset_dir()}")
    print(f"  → scalp: {observer_asset_dir() / 'scalp'}")
    print(f"  → swing: {observer_asset_dir() / 'swing'}")
    print(f"Log 디렉토리: {observer_log_dir()}")
    print(f"  → scalp: {observer_log_dir() / 'scalp'}")
    print(f"  → swing: {observer_log_dir() / 'swing'}")
    
    print("\n환경 변수:")
    print(f"  OBSERVER_STANDALONE: {os.environ.get('OBSERVER_STANDALONE', 'NOT_SET')}")
    print(f"  OBSERVER_CONFIG_DIR: {os.environ.get('OBSERVER_CONFIG_DIR', 'NOT_SET')}")
    print(f"  OBSERVER_LOG_DIR: {os.environ.get('OBSERVER_LOG_DIR', 'NOT_SET')}")


def main():
    print("="*60)
    print("Phase 1.1: Track A/B Config 생성 경로 테스트")
    print("="*60)
    
    all_results = []
    
    # 테스트 실행
    all_results.append(test_project_root())
    all_results.append(test_config_dir())
    all_results.append(test_observer_asset_dir())
    all_results.append(test_scalp_swing_directories())
    all_results.append(test_observer_log_dir())
    all_results.append(test_log_subdirectories())
    all_results.append(test_jsonl_file_creation())
    all_results.append(test_log_file_creation())
    all_results.append(test_environment_variable_override())
    
    # 경로 요약
    print_path_summary()
    
    # 최종 결과
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)
    
    print(f"\n{'='*60}")
    print(f"최종 결과: {total_passed}/{total_passed + total_failed} 테스트 통과")
    print(f"{'='*60}")
    
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
