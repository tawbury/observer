#!/usr/bin/env python3
"""
Phase 3.1: Docker 설정 검증 테스트 (Docker 없이 실행 가능)

목표:
- docker-compose.yml 볼륨 매핑 설정 검증
- Dockerfile 경로 설정 검증
- 환경 변수 설정 검증
- 호스트 경로 구조 검증

실행:
  python tests/integration/test_docker_config_verification.py
"""

import sys
import yaml
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Project paths (App repo: src/, docker/, backups/ for legacy compose)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKUP_ROOT = PROJECT_ROOT / "backups" / "pre-k8s-refactor-20260202"
SRC_ROOT = PROJECT_ROOT / "src"


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

    def skip(self, name: str, reason: str):
        print(f"  [SKIP] {name} - {reason}")


def test_docker_compose_volumes():
    """docker-compose.yml 볼륨 설정 검증"""
    print("\n[1] Docker Compose Volume Configuration")
    result = TestResult()
    
    compose_files = [
        ("docker-compose.yml", BACKUP_ROOT / "docker-compose" / "docker-compose.yml"),
        ("docker-compose.prod.yml", BACKUP_ROOT / "compose" / "docker-compose.prod.yml"),
    ]
    
    expected_volumes = {
        "data": ("/app/data", "data"),
        "logs": ("/app/logs", "logs"),
        "config": ("/app/config", "config"),
        "secrets": ("/app/secrets", "secrets"),
    }
    
    for name, compose_path in compose_files:
        if not compose_path.exists():
            result.skip(f"{name}", "File not found (compose in backups/)")
            continue
        
        print(f"\n  Checking {name}:")
        
        with open(compose_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        try:
            compose_data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            result.fail(f"{name} YAML parse", str(e))
            continue
        
        # Check observer service volumes
        services = compose_data.get("services", {})
        observer_service = services.get("observer", {})
        volumes = observer_service.get("volumes", [])
        
        if not volumes:
            result.fail(f"{name} observer volumes", "No volumes defined")
            continue
        
        for vol_name, (container_path, host_suffix) in expected_volumes.items():
            found = False
            for vol in volumes:
                if container_path in vol:
                    found = True
                    result.success(f"{vol_name} volume: {vol}")
                    break
            
            if not found:
                result.fail(f"{vol_name} volume", f"Container path {container_path} not found")
    
    return result


def test_docker_compose_environment():
    """docker-compose.yml 환경 변수 설정 검증"""
    print("\n[2] Docker Compose Environment Variables")
    result = TestResult()
    
    compose_path = BACKUP_ROOT / "docker-compose" / "docker-compose.yml"
    
    if not compose_path.exists():
        result.skip("docker-compose.yml", "File not found (compose in backups/)")
        return result
    
    with open(compose_path, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)
    
    observer_service = compose_data.get("services", {}).get("observer", {})
    environment = observer_service.get("environment", [])
    
    # Convert list to dict if needed
    env_dict = {}
    for item in environment:
        if isinstance(item, str) and "=" in item:
            key, value = item.split("=", 1)
            env_dict[key.strip("- ")] = value
        elif isinstance(item, str):
            env_dict[item.strip("- ")] = ""
    
    expected_env = {
        "OBSERVER_STANDALONE": "1",
        "OBSERVER_DATA_DIR": "/app/data",
        "OBSERVER_LOG_DIR": "/app/logs",
        "OBSERVER_CONFIG_DIR": "/app/config",
        "TZ": "Asia/Seoul",
    }
    
    for key, expected_value in expected_env.items():
        if key in env_dict:
            actual = env_dict[key]
            if expected_value and actual == expected_value:
                result.success(f"{key}={actual}")
            elif expected_value:
                result.fail(f"{key}", f"Expected {expected_value}, got {actual}")
            else:
                result.success(f"{key} is set")
        else:
            result.fail(f"{key}", "Not found in environment")
    
    return result


def test_dockerfile_configuration():
    """Dockerfile 설정 검증"""
    print("\n[3] Dockerfile Configuration")
    result = TestResult()
    
    dockerfile_path = PROJECT_ROOT / "docker" / "Dockerfile"
    
    if not dockerfile_path.exists():
        result.fail("Dockerfile", "File not found")
        return result
    
    with open(dockerfile_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check required directories
    required_dirs = [
        "/app/data",
        "/app/logs",
        "/app/config",
        "/app/secrets",
    ]
    
    for dir_path in required_dirs:
        if dir_path in content:
            result.success(f"Directory {dir_path} referenced")
        else:
            result.fail(f"Directory {dir_path}", "Not found in Dockerfile")
    
    # Check environment variables
    env_vars = [
        "OBSERVER_STANDALONE=1",
        "OBSERVER_DATA_DIR=/app/data",
        "OBSERVER_LOG_DIR=/app/logs",
        "OBSERVER_CONFIG_DIR=/app/config",
    ]
    
    for env_var in env_vars:
        if env_var in content:
            result.success(f"ENV {env_var}")
        else:
            result.fail(f"ENV {env_var}", "Not found in Dockerfile")
    
    # Check WORKDIR
    if "WORKDIR /app" in content:
        result.success("WORKDIR /app")
    else:
        result.fail("WORKDIR", "/app not set")
    
    return result


def test_host_directory_structure():
    """호스트 디렉토리 구조 검증"""
    print("\n[4] Host Directory Structure")
    result = TestResult()
    
    required_dirs = [
        PROJECT_ROOT / "config",
        PROJECT_ROOT / "config" / "observer",
        PROJECT_ROOT / "config" / "observer" / "scalp",
        PROJECT_ROOT / "config" / "observer" / "swing",
        PROJECT_ROOT / "data",
        PROJECT_ROOT / "secrets",
        PROJECT_ROOT / "logs",
    ]
    
    for dir_path in required_dirs:
        if dir_path.exists():
            result.success(f"Directory exists: {dir_path.relative_to(PROJECT_ROOT)}")
        else:
            # Try to create
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                result.success(f"Directory created: {dir_path.relative_to(PROJECT_ROOT)}")
            except Exception as e:
                result.fail(f"Directory: {dir_path.relative_to(PROJECT_ROOT)}", str(e))
    
    return result


def test_volume_path_mapping():
    """볼륨 경로 매핑 일관성 검증"""
    print("\n[5] Volume Path Mapping Consistency")
    result = TestResult()
    
    # Expected mappings
    mappings = [
        ("Host", "Container", "Purpose"),
        ("config", "/app/config", "Config files"),
        ("logs", "/app/logs", "Log files"),
        ("data", "/app/data", "Data files"),
        ("secrets", "/app/secrets", "Secrets"),
    ]
    
    print("\n  Volume Mapping Table:")
    print(f"  {'Host Path':<30} {'Container Path':<20} {'Purpose':<15}")
    print(f"  {'-'*30} {'-'*20} {'-'*15}")
    
    for host, container, purpose in mappings[1:]:
        print(f"  {host:<30} {container:<20} {purpose:<15}")
        
        # Verify host path exists
        host_path = PROJECT_ROOT / host
        if host_path.exists():
            result.success(f"Host path exists: {host}")
        else:
            result.fail(f"Host path: {host}", "Does not exist")
    
    return result


def test_paths_py_docker_mode():
    """paths.py Docker 모드 설정 검증"""
    print("\n[6] paths.py Docker Mode Configuration")
    result = TestResult()
    
    paths_file = PROJECT_ROOT / "src" / "observer" / "paths.py"
    
    if not paths_file.exists():
        result.fail("paths.py", "File not found")
        return result
    
    with open(paths_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for OBSERVER_STANDALONE handling
    if 'OBSERVER_STANDALONE' in content:
        result.success("OBSERVER_STANDALONE env var handling")
    else:
        result.fail("OBSERVER_STANDALONE", "Not found in paths.py")
    
    # Check for Docker path resolution
    if '/app' in content:
        result.success("Docker /app path reference")
    else:
        result.fail("Docker /app path", "Not found in paths.py")
    
    # Check for environment variable overrides
    env_overrides = [
        "OBSERVER_CONFIG_DIR",
        "OBSERVER_LOG_DIR",
        "OBSERVER_DATA_DIR",
    ]
    
    for env_var in env_overrides:
        if env_var in content:
            result.success(f"ENV override: {env_var}")
        else:
            result.fail(f"ENV override: {env_var}", "Not found in paths.py")
    
    return result


def print_summary(all_results):
    """테스트 결과 요약 출력"""
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)
    
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    print(f"  Passed: {total_passed}")
    print(f"  Failed: {total_failed}")
    print(f"  Total:  {total_passed + total_failed}")
    
    if total_failed > 0:
        print(f"\nFailed tests:")
        for r in all_results:
            for name, reason in r.errors:
                print(f"  - {name}: {reason}")
    
    print(f"\n{'='*60}")
    
    return total_failed == 0


def main():
    print("="*60)
    print("Phase 3.1: Docker Configuration Verification")
    print("(No Docker required)")
    print("="*60)
    
    all_results = []
    
    all_results.append(test_docker_compose_volumes())
    all_results.append(test_docker_compose_environment())
    all_results.append(test_dockerfile_configuration())
    all_results.append(test_host_directory_structure())
    all_results.append(test_volume_path_mapping())
    all_results.append(test_paths_py_docker_mode())
    
    success = print_summary(all_results)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
