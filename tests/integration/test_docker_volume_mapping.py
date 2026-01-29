#!/usr/bin/env python3
"""
Phase 3.1: Docker 볼륨 매핑 검증 테스트

목표:
- 호스트 app/observer/config/observer/scalp/ <-> 컨테이너 /app/config/observer/scalp/
- 호스트 app/observer/config/observer/swing/ <-> 컨테이너 /app/config/observer/swing/
- 호스트 app/observer/logs/ <-> 컨테이너 /app/logs/

실행:
  python tests/integration/test_docker_volume_mapping.py
  
참고:
  - Docker 컨테이너가 실행 중이어야 합니다
  - docker-compose up -d 로 먼저 컨테이너를 시작하세요
"""

import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

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


def check_docker_running() -> bool:
    """Docker가 실행 중인지 확인"""
    code, _, _ = run_command("docker info")
    return code == 0


def check_container_running(container_name: str = "observer") -> bool:
    """특정 컨테이너가 실행 중인지 확인"""
    code, stdout, _ = run_command(f"docker ps --filter name={container_name} --format '{{{{.Names}}}}'")
    return code == 0 and container_name in stdout


def test_docker_availability():
    """Docker 및 컨테이너 가용성 테스트"""
    print("\n[1] Docker Availability Check")
    result = TestResult()
    
    if check_docker_running():
        result.success("Docker daemon is running")
    else:
        result.fail("Docker daemon", "Docker is not running")
        return result, False
    
    if check_container_running("observer"):
        result.success("Observer container is running")
    else:
        result.fail("Observer container", "Container is not running. Run 'docker-compose up -d' first")
        return result, False
    
    return result, True


def test_volume_mount_configuration():
    """docker-compose.yml 볼륨 설정 검증"""
    print("\n[2] Volume Mount Configuration Check")
    result = TestResult()
    
    compose_files = [
        PROJECT_ROOT / "infra" / "docker" / "compose" / "docker-compose.yml",
        PROJECT_ROOT / "infra" / "_shared" / "compose" / "docker-compose.prod.yml",
    ]
    
    expected_mounts = [
        ("config", "../../../app/observer/config:/app/config"),
        ("logs", "../../../app/observer/logs:/app/logs"),
        ("data", "../../../app/observer/data:/app/data"),
        ("secrets", "../../../app/observer/secrets:/app/secrets"),
    ]
    
    for compose_file in compose_files:
        if compose_file.exists():
            with open(compose_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            print(f"\n  Checking {compose_file.name}:")
            for name, mount in expected_mounts:
                if mount in content or mount.replace("../../../", "./") in content:
                    result.success(f"{name} volume mount configured")
                else:
                    result.fail(f"{name} volume mount", f"Not found in {compose_file.name}")
        else:
            result.skip(f"{compose_file.name}", "File not found")
    
    return result


def test_container_path_access():
    """컨테이너 내부 경로 접근 테스트"""
    print("\n[3] Container Path Access Test")
    result = TestResult()
    
    paths_to_check = [
        "/app/config",
        "/app/config/observer",
        "/app/config/observer/scalp",
        "/app/config/observer/swing",
        "/app/logs",
        "/app/data",
    ]
    
    for path in paths_to_check:
        code, stdout, stderr = run_command(f'docker exec observer ls -d {path}')
        if code == 0:
            result.success(f"Container path exists: {path}")
        else:
            result.fail(f"Container path: {path}", stderr or "Path not found")
    
    return result


def test_host_path_access():
    """호스트 경로 접근 테스트"""
    print("\n[4] Host Path Access Test")
    result = TestResult()
    
    paths_to_check = [
        PROJECT_ROOT / "app" / "observer" / "config",
        PROJECT_ROOT / "app" / "observer" / "config" / "observer",
        PROJECT_ROOT / "app" / "observer" / "config" / "observer" / "scalp",
        PROJECT_ROOT / "app" / "observer" / "config" / "observer" / "swing",
        PROJECT_ROOT / "logs",
        PROJECT_ROOT / "app" / "observer" / "data",
    ]
    
    for path in paths_to_check:
        if path.exists():
            result.success(f"Host path exists: {path}")
        else:
            # Try to create if missing
            try:
                path.mkdir(parents=True, exist_ok=True)
                result.success(f"Host path created: {path}")
            except Exception as e:
                result.fail(f"Host path: {path}", str(e))
    
    return result


def test_bidirectional_sync():
    """양방향 파일 동기화 테스트"""
    print("\n[5] Bidirectional File Sync Test")
    result = TestResult()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_filename = f"volume_test_{timestamp}.txt"
    
    # Test paths
    host_config_dir = PROJECT_ROOT / "app" / "observer" / "config" / "observer" / "scalp"
    container_config_path = "/app/config/observer/scalp"
    
    # Ensure host directory exists
    host_config_dir.mkdir(parents=True, exist_ok=True)
    
    # Test 1: Write from host, read from container
    print("\n  [5.1] Host -> Container sync")
    host_test_file = host_config_dir / test_filename
    test_content = f"Test from host at {timestamp}"
    
    try:
        with open(host_test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        # Read from container
        code, stdout, stderr = run_command(f'docker exec observer cat {container_config_path}/{test_filename}')
        if code == 0 and test_content in stdout:
            result.success("Host -> Container sync works")
        else:
            result.fail("Host -> Container sync", stderr or "Content mismatch")
    except Exception as e:
        result.fail("Host -> Container sync", str(e))
    finally:
        if host_test_file.exists():
            host_test_file.unlink()
    
    # Test 2: Write from container, read from host
    print("\n  [5.2] Container -> Host sync")
    test_filename2 = f"volume_test_container_{timestamp}.txt"
    test_content2 = f"Test from container at {timestamp}"
    
    try:
        # Write from container
        write_cmd = f'docker exec observer sh -c "echo \'{test_content2}\' > {container_config_path}/{test_filename2}"'
        code, _, stderr = run_command(write_cmd)
        
        if code == 0:
            # Read from host
            host_test_file2 = host_config_dir / test_filename2
            if host_test_file2.exists():
                with open(host_test_file2, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if test_content2 in content:
                    result.success("Container -> Host sync works")
                else:
                    result.fail("Container -> Host sync", "Content mismatch")
            else:
                result.fail("Container -> Host sync", "File not found on host")
        else:
            result.fail("Container -> Host sync", stderr or "Write failed")
    except Exception as e:
        result.fail("Container -> Host sync", str(e))
    finally:
        host_test_file2 = host_config_dir / test_filename2
        if host_test_file2.exists():
            host_test_file2.unlink()
    
    return result


def test_jsonl_file_sync():
    """JSONL 파일 동기화 테스트"""
    print("\n[6] JSONL File Sync Test")
    result = TestResult()
    
    today = datetime.now().strftime("%Y%m%d")
    
    # Check scalp JSONL
    host_scalp_jsonl = PROJECT_ROOT / "app" / "observer" / "config" / "observer" / "scalp" / f"{today}.jsonl"
    container_scalp_path = f"/app/config/observer/scalp/{today}.jsonl"
    
    if host_scalp_jsonl.exists():
        # Compare file sizes
        host_size = host_scalp_jsonl.stat().st_size
        code, stdout, _ = run_command(f'docker exec observer stat -c %s {container_scalp_path}')
        
        if code == 0:
            container_size = int(stdout.strip()) if stdout.strip().isdigit() else 0
            if host_size == container_size:
                result.success(f"scalp JSONL size match: {host_size} bytes")
            else:
                result.fail("scalp JSONL size", f"Host: {host_size}, Container: {container_size}")
        else:
            result.fail("scalp JSONL container", "File not found in container")
    else:
        result.skip("scalp JSONL sync", "No scalp JSONL file on host today")
    
    # Check swing JSONL
    host_swing_jsonl = PROJECT_ROOT / "app" / "observer" / "config" / "observer" / "swing" / f"{today}.jsonl"
    container_swing_path = f"/app/config/observer/swing/{today}.jsonl"
    
    if host_swing_jsonl.exists():
        host_size = host_swing_jsonl.stat().st_size
        code, stdout, _ = run_command(f'docker exec observer stat -c %s {container_swing_path}')
        
        if code == 0:
            container_size = int(stdout.strip()) if stdout.strip().isdigit() else 0
            if host_size == container_size:
                result.success(f"swing JSONL size match: {host_size} bytes")
            else:
                result.fail("swing JSONL size", f"Host: {host_size}, Container: {container_size}")
        else:
            result.fail("swing JSONL container", "File not found in container")
    else:
        result.skip("swing JSONL sync", "No swing JSONL file on host today")
    
    return result


def test_log_directory_sync():
    """로그 디렉토리 동기화 테스트"""
    print("\n[7] Log Directory Sync Test")
    result = TestResult()
    
    # Check if logs directory is mounted
    code, stdout, _ = run_command('docker exec observer ls -la /app/logs/')
    
    if code == 0:
        result.success("Container /app/logs/ accessible")
        print(f"\n  Container /app/logs/ contents:")
        for line in stdout.split('\n')[:10]:  # Show first 10 lines
            print(f"    {line}")
    else:
        result.fail("Container /app/logs/", "Directory not accessible")
    
    # Check host logs directory
    host_logs = PROJECT_ROOT / "logs"
    if host_logs.exists():
        result.success(f"Host logs directory exists: {host_logs}")
        
        # List subdirectories
        subdirs = [d for d in host_logs.iterdir() if d.is_dir()]
        print(f"\n  Host logs subdirectories:")
        for subdir in subdirs:
            files = list(subdir.glob("*"))
            print(f"    - {subdir.name}/ ({len(files)} files)")
    else:
        result.fail("Host logs directory", f"Not found: {host_logs}")
    
    return result


def test_paths_py_in_container():
    """컨테이너 내 paths.py 경로 확인"""
    print("\n[8] Container paths.py Verification")
    result = TestResult()
    
    # Run paths verification in container
    python_cmd = '''
import sys
sys.path.insert(0, "/app/src")
sys.path.insert(0, "/app")
from paths import project_root, config_dir, observer_asset_dir, observer_log_dir
print(f"project_root: {project_root()}")
print(f"config_dir: {config_dir()}")
print(f"observer_asset_dir: {observer_asset_dir()}")
print(f"observer_log_dir: {observer_log_dir()}")
'''
    
    code, stdout, stderr = run_command(f'docker exec observer python -c "{python_cmd}"')
    
    if code == 0:
        result.success("paths.py executed in container")
        print(f"\n  Container paths:")
        for line in stdout.split('\n'):
            print(f"    {line}")
        
        # Verify expected paths
        if "/app/config/observer" in stdout:
            result.success("observer_asset_dir points to /app/config/observer")
        else:
            result.fail("observer_asset_dir", "Unexpected path")
        
        if "/app/logs" in stdout:
            result.success("observer_log_dir points to /app/logs")
        else:
            result.fail("observer_log_dir", "Unexpected path")
    else:
        result.fail("paths.py execution", stderr or "Failed to execute")
    
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
    print("Phase 3.1: Docker Volume Mapping Verification")
    print("="*60)
    
    all_results = []
    
    # Check Docker availability first
    docker_result, docker_ok = test_docker_availability()
    all_results.append(docker_result)
    
    if not docker_ok:
        print("\n[!] Docker or container not available. Skipping remaining tests.")
        print("    Run 'docker-compose up -d' from infra/docker/compose/ first.")
        print_summary(all_results)
        return 1
    
    # Run remaining tests
    all_results.append(test_volume_mount_configuration())
    all_results.append(test_container_path_access())
    all_results.append(test_host_path_access())
    all_results.append(test_bidirectional_sync())
    all_results.append(test_jsonl_file_sync())
    all_results.append(test_log_directory_sync())
    all_results.append(test_paths_py_in_container())
    
    success = print_summary(all_results)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
