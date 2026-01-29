#!/usr/bin/env python3
"""
Phase 3.2-3.3: Docker 컨테이너 내 Track A/B 실행 및 파일 동기화 검증

목표:
- 컨테이너 내 /app/config/observer/scalp/YYYYMMDD.jsonl 생성 확인
- 호스트 app/observer/config/observer/scalp/YYYYMMDD.jsonl 동기화 확인
- 양방향 파일 접근 가능 여부 확인

실행:
  python tests/integration/test_docker_track_ab_integration.py
  
사전 요구사항:
  1. Docker Desktop 실행
  2. docker-compose up -d (infra/docker/compose/)
"""

import subprocess
import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class TestResult:
    """테스트 결과 추적"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []
    
    def success(self, name: str):
        self.passed += 1
        print(f"  [PASS] {name}")
    
    def fail(self, name: str, reason: str):
        self.failed += 1
        self.errors.append((name, reason))
        print(f"  [FAIL] {name} - {reason}")
    
    def skip(self, name: str, reason: str):
        self.skipped += 1
        print(f"  [SKIP] {name} - {reason}")


def run_command(cmd: str, timeout: int = 30) -> Tuple[int, str, str]:
    """Run shell command and return (exit_code, stdout, stderr)"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def check_docker_available() -> Tuple[bool, str]:
    """Docker 가용성 확인"""
    code, _, stderr = run_command("docker info")
    if code != 0:
        return False, "Docker is not running"
    
    code, stdout, _ = run_command("docker ps --filter name=observer --format '{{.Names}}'")
    if code != 0 or "observer" not in stdout:
        return False, "Observer container is not running"
    
    return True, "Docker and container are ready"


def test_docker_prerequisites():
    """Docker 사전 요구사항 확인"""
    print("\n[1] Docker Prerequisites Check")
    result = TestResult()
    
    available, message = check_docker_available()
    
    if available:
        result.success(message)
        return result, True
    else:
        result.fail("Docker prerequisites", message)
        print("\n  To start Docker containers:")
        print("    cd infra/docker/compose")
        print("    docker-compose up -d")
        return result, False


def test_container_paths_verification():
    """컨테이너 내 경로 검증"""
    print("\n[2] Container Paths Verification")
    result = TestResult()
    
    # Run paths.py verification in container
    python_cmd = '''
import sys
sys.path.insert(0, "/app/src")
sys.path.insert(0, "/app")
from paths import project_root, config_dir, observer_asset_dir, observer_log_dir
import json
paths_info = {
    "project_root": str(project_root()),
    "config_dir": str(config_dir()),
    "observer_asset_dir": str(observer_asset_dir()),
    "observer_log_dir": str(observer_log_dir()),
    "scalp_dir": str(observer_asset_dir() / "scalp"),
    "swing_dir": str(observer_asset_dir() / "swing"),
}
print(json.dumps(paths_info))
'''
    
    code, stdout, stderr = run_command(f'docker exec observer python -c "{python_cmd}"')
    
    if code != 0:
        result.fail("Container paths execution", stderr or "Failed to execute")
        return result
    
    try:
        paths_info = json.loads(stdout)
        
        expected_paths = {
            "project_root": "/app",
            "config_dir": "/app/config",
            "observer_asset_dir": "/app/config/observer",
            "observer_log_dir": "/app/logs",
            "scalp_dir": "/app/config/observer/scalp",
            "swing_dir": "/app/config/observer/swing",
        }
        
        for key, expected in expected_paths.items():
            actual = paths_info.get(key, "")
            if actual == expected:
                result.success(f"{key}: {actual}")
            else:
                result.fail(f"{key}", f"Expected {expected}, got {actual}")
    
    except json.JSONDecodeError as e:
        result.fail("Container paths JSON", str(e))
    
    return result


def test_track_a_config_in_container():
    """컨테이너 내 Track A config 생성 테스트"""
    print("\n[3] Track A Config Generation in Container")
    result = TestResult()
    
    today = datetime.now().strftime("%Y%m%d")
    container_swing_path = f"/app/config/observer/swing/{today}.jsonl"
    host_swing_path = PROJECT_ROOT / "app" / "observer" / "config" / "observer" / "swing" / f"{today}.jsonl"
    
    # Create test record in container
    test_record = {
        "ts": datetime.now().isoformat(),
        "session": "docker_test_session",
        "dataset": "track_a_swing",
        "market": "kr_stocks",
        "symbol": "TEST001",
        "price": {"open": 10000, "high": 10500, "low": 9500, "close": 10200},
        "volume": 100000,
        "source": "docker_test",
    }
    
    # Write from container
    python_cmd = f'''
import json
record = {json.dumps(test_record)}
with open("{container_swing_path}", "a", encoding="utf-8") as f:
    f.write(json.dumps(record, ensure_ascii=False) + "\\n")
print("OK")
'''
    
    code, stdout, stderr = run_command(f'docker exec observer python -c "{python_cmd}"')
    
    if code == 0 and "OK" in stdout:
        result.success("Container write: swing JSONL")
    else:
        result.fail("Container write: swing JSONL", stderr or "Write failed")
        return result
    
    # Verify on host
    time.sleep(0.5)  # Brief delay for sync
    
    if host_swing_path.exists():
        with open(host_swing_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if any("docker_test" in line for line in lines):
                result.success("Host sync: swing JSONL contains docker_test record")
            else:
                result.fail("Host sync: swing JSONL", "docker_test record not found")
    else:
        result.fail("Host sync: swing JSONL", f"File not found: {host_swing_path}")
    
    return result


def test_track_b_config_in_container():
    """컨테이너 내 Track B config 생성 테스트"""
    print("\n[4] Track B Config Generation in Container")
    result = TestResult()
    
    today = datetime.now().strftime("%Y%m%d")
    container_scalp_path = f"/app/config/observer/scalp/{today}.jsonl"
    host_scalp_path = PROJECT_ROOT / "app" / "observer" / "config" / "observer" / "scalp" / f"{today}.jsonl"
    
    # Create test record in container
    test_record = {
        "timestamp": datetime.now().isoformat(),
        "symbol": "TEST002",
        "execution_time": "103015",
        "price": {"current": 20200, "open": 20000, "high": 20500, "low": 19500, "change_rate": 1.0},
        "volume": {"accumulated": 200000, "trade_value": 4040000000},
        "source": "websocket",
        "session_id": "docker_test_session",
        "test_marker": "docker_scalp_test",
    }
    
    # Write from container
    python_cmd = f'''
import json
record = {json.dumps(test_record)}
with open("{container_scalp_path}", "a", encoding="utf-8") as f:
    f.write(json.dumps(record, ensure_ascii=False) + "\\n")
print("OK")
'''
    
    code, stdout, stderr = run_command(f'docker exec observer python -c "{python_cmd}"')
    
    if code == 0 and "OK" in stdout:
        result.success("Container write: scalp JSONL")
    else:
        result.fail("Container write: scalp JSONL", stderr or "Write failed")
        return result
    
    # Verify on host
    time.sleep(0.5)
    
    if host_scalp_path.exists():
        with open(host_scalp_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if any("docker_scalp_test" in line for line in lines):
                result.success("Host sync: scalp JSONL contains docker_scalp_test record")
            else:
                result.fail("Host sync: scalp JSONL", "docker_scalp_test record not found")
    else:
        result.fail("Host sync: scalp JSONL", f"File not found: {host_scalp_path}")
    
    return result


def test_host_to_container_sync():
    """호스트에서 컨테이너로 파일 동기화 테스트"""
    print("\n[5] Host to Container File Sync")
    result = TestResult()
    
    today = datetime.now().strftime("%Y%m%d")
    timestamp = datetime.now().strftime("%H%M%S")
    
    # Write from host
    host_test_file = PROJECT_ROOT / "app" / "observer" / "config" / "observer" / "scalp" / f"host_test_{timestamp}.txt"
    test_content = f"Test from host at {timestamp}"
    
    try:
        host_test_file.parent.mkdir(parents=True, exist_ok=True)
        with open(host_test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        result.success("Host write: test file created")
        
        # Verify in container
        time.sleep(0.5)
        container_path = f"/app/config/observer/scalp/host_test_{timestamp}.txt"
        code, stdout, stderr = run_command(f'docker exec observer cat {container_path}')
        
        if code == 0 and test_content in stdout:
            result.success("Container read: test file synced")
        else:
            result.fail("Container read: test file", stderr or "Content mismatch")
    
    except Exception as e:
        result.fail("Host to container sync", str(e))
    
    finally:
        # Cleanup
        if host_test_file.exists():
            host_test_file.unlink()
    
    return result


def test_log_directory_sync():
    """로그 디렉토리 동기화 테스트"""
    print("\n[6] Log Directory Sync")
    result = TestResult()
    
    today = datetime.now().strftime("%Y%m%d")
    timestamp = datetime.now().strftime("%H%M%S")
    
    # Write log from container
    container_log_path = f"/app/logs/scalp/{today}_docker_test.log"
    log_content = f"{datetime.now().isoformat()} | INFO | DockerTest | Test log entry {timestamp}"
    
    python_cmd = f'''
from pathlib import Path
log_dir = Path("/app/logs/scalp")
log_dir.mkdir(parents=True, exist_ok=True)
with open("{container_log_path}", "a", encoding="utf-8") as f:
    f.write("{log_content}\\n")
print("OK")
'''
    
    code, stdout, stderr = run_command(f'docker exec observer python -c "{python_cmd}"')
    
    if code == 0 and "OK" in stdout:
        result.success("Container write: log file")
    else:
        result.fail("Container write: log file", stderr or "Write failed")
        return result
    
    # Verify on host
    # Note: logs are mounted from app/observer/logs
    host_log_path = PROJECT_ROOT / "app" / "observer" / "logs" / "scalp" / f"{today}_docker_test.log"
    
    # Also check project root logs (depends on docker-compose configuration)
    alt_host_log_path = PROJECT_ROOT / "logs" / "scalp" / f"{today}_docker_test.log"
    
    time.sleep(0.5)
    
    found = False
    for log_path in [host_log_path, alt_host_log_path]:
        if log_path.exists():
            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read()
                if timestamp in content:
                    result.success(f"Host sync: log file at {log_path.relative_to(PROJECT_ROOT)}")
                    found = True
                    break
    
    if not found:
        result.fail("Host sync: log file", "Log file not found on host")
    
    return result


def test_collector_import_in_container():
    """컨테이너 내 Collector 모듈 임포트 테스트"""
    print("\n[7] Collector Module Import in Container")
    result = TestResult()
    
    # Test Track A Collector import
    python_cmd = '''
import sys
sys.path.insert(0, "/app/src")
sys.path.insert(0, "/app")
from collector.track_a_collector import TrackACollector, TrackAConfig
print("TrackA OK")
'''
    
    code, stdout, stderr = run_command(f'docker exec observer python -c "{python_cmd}"')
    
    if code == 0 and "TrackA OK" in stdout:
        result.success("Track A Collector import")
    else:
        result.fail("Track A Collector import", stderr or "Import failed")
    
    # Test Track B Collector import
    python_cmd = '''
import sys
sys.path.insert(0, "/app/src")
sys.path.insert(0, "/app")
from collector.track_b_collector import TrackBCollector, TrackBConfig
print("TrackB OK")
'''
    
    code, stdout, stderr = run_command(f'docker exec observer python -c "{python_cmd}"')
    
    if code == 0 and "TrackB OK" in stdout:
        result.success("Track B Collector import")
    else:
        result.fail("Track B Collector import", stderr or "Import failed")
    
    return result


def test_environment_variables_in_container():
    """컨테이너 내 환경 변수 확인"""
    print("\n[8] Environment Variables in Container")
    result = TestResult()
    
    env_vars = [
        "OBSERVER_STANDALONE",
        "OBSERVER_CONFIG_DIR",
        "OBSERVER_LOG_DIR",
        "OBSERVER_DATA_DIR",
        "TZ",
    ]
    
    for var in env_vars:
        code, stdout, _ = run_command(f'docker exec observer printenv {var}')
        if code == 0 and stdout:
            result.success(f"{var}={stdout}")
        else:
            result.fail(f"{var}", "Not set or empty")
    
    return result


def print_summary(all_results):
    """테스트 결과 요약 출력"""
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)
    total_skipped = sum(r.skipped for r in all_results)
    
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    print(f"  Passed:  {total_passed}")
    print(f"  Failed:  {total_failed}")
    print(f"  Skipped: {total_skipped}")
    print(f"  Total:   {total_passed + total_failed + total_skipped}")
    
    if total_failed > 0:
        print(f"\nFailed tests:")
        for r in all_results:
            for name, reason in r.errors:
                print(f"  - {name}: {reason}")
    
    print(f"\n{'='*60}")
    
    return total_failed == 0


def main():
    print("="*60)
    print("Phase 3.2-3.3: Docker Track A/B Integration Test")
    print("="*60)
    
    all_results = []
    
    # Check Docker prerequisites
    prereq_result, docker_ok = test_docker_prerequisites()
    all_results.append(prereq_result)
    
    if not docker_ok:
        print("\n[!] Docker prerequisites not met. Skipping remaining tests.")
        print_summary(all_results)
        return 1
    
    # Run integration tests
    all_results.append(test_container_paths_verification())
    all_results.append(test_track_a_config_in_container())
    all_results.append(test_track_b_config_in_container())
    all_results.append(test_host_to_container_sync())
    all_results.append(test_log_directory_sync())
    all_results.append(test_collector_import_in_container())
    all_results.append(test_environment_variables_in_container())
    
    success = print_summary(all_results)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
