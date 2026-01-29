#!/usr/bin/env python3
"""
Track A/B 통합 테스트 러너

모든 Phase의 테스트를 순차적으로 실행합니다.

실행:
  python tests/run_track_ab_tests.py [--skip-docker]
"""

import subprocess
import sys
import argparse
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = PROJECT_ROOT / "tests"


def run_test(name: str, script_path: Path) -> bool:
    """테스트 스크립트 실행"""
    print(f"\n{'='*60}")
    print(f"Running: {name}")
    print(f"Script: {script_path.relative_to(PROJECT_ROOT)}")
    print(f"{'='*60}")
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(PROJECT_ROOT),
        capture_output=False,
    )
    
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Track A/B Integration Test Runner")
    parser.add_argument("--skip-docker", action="store_true", help="Skip Docker-dependent tests")
    parser.add_argument("--phase", type=int, choices=[1, 2, 3], help="Run specific phase only")
    args = parser.parse_args()
    
    print("="*60)
    print("Track A/B Integration Test Runner")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)
    
    results = {}
    
    # Phase 1: Local Unit Tests
    if args.phase is None or args.phase == 1:
        print("\n" + "#"*60)
        print("# PHASE 1: Local Unit Tests")
        print("#"*60)
        
        results["Phase 1.1: Path Functions"] = run_test(
            "Phase 1.1: Path Functions Test",
            TESTS_DIR / "local" / "test_track_ab_config_creation.py"
        )
        
        results["Phase 1.2-1.3: Mock Tests"] = run_test(
            "Phase 1.2-1.3: Mock-based Tests",
            TESTS_DIR / "local" / "test_track_ab_mock.py"
        )
    
    # Phase 2: Local Integration Tests
    if args.phase is None or args.phase == 2:
        print("\n" + "#"*60)
        print("# PHASE 2: Local Integration Tests")
        print("#"*60)
        
        results["Phase 2: File Verification"] = run_test(
            "Phase 2: File Verification Test",
            TESTS_DIR / "local" / "test_track_ab_file_verification.py"
        )
    
    # Phase 3: Docker Tests
    if args.phase is None or args.phase == 3:
        print("\n" + "#"*60)
        print("# PHASE 3: Docker Tests")
        print("#"*60)
        
        # Docker config verification (no Docker required)
        results["Phase 3.1: Docker Config"] = run_test(
            "Phase 3.1: Docker Configuration Verification",
            TESTS_DIR / "integration" / "test_docker_config_verification.py"
        )
        
        if not args.skip_docker:
            # Docker volume mapping (Docker required)
            results["Phase 3.1: Volume Mapping"] = run_test(
                "Phase 3.1: Docker Volume Mapping",
                TESTS_DIR / "integration" / "test_docker_volume_mapping.py"
            )
            
            # Docker integration (Docker required)
            results["Phase 3.2-3.3: Docker Integration"] = run_test(
                "Phase 3.2-3.3: Docker Track A/B Integration",
                TESTS_DIR / "integration" / "test_docker_track_ab_integration.py"
            )
        else:
            print("\n[SKIP] Docker-dependent tests skipped (--skip-docker)")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    
    for name, success in results.items():
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status} {name}")
    
    print(f"\n  Total: {passed}/{len(results)} passed")
    print(f"  Finished at: {datetime.now().isoformat()}")
    print("="*60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
