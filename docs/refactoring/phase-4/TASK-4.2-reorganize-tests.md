# TASK-4.2: 테스트 파일 재구성

## 태스크 정보
- **Phase**: 4 - 폴더 구조 재정립
- **우선순위**: Medium
- **의존성**: TASK-4.1 (폴더 구조 재정립)
- **상태**: 대기

---

## 목표
소스 코드와 혼재된 테스트 파일들을 `tests/` 디렉토리로 분리하여 명확한 구조를 확립합니다.

---

## 현재 문제

### 현재 테스트 파일 위치
테스트 파일이 소스 코드와 혼재되어 있습니다:

```
app/observer/                         # (구조 변경 후)
├── test_track_a_local.py            ← 루트에 테스트
├── test_track_b_local.py            ← 루트에 테스트
└── src/
    ├── backup/
    │   └── test_backup_manager.py   ← src 내부에 테스트
    ├── monitoring/
    │   └── test_monitoring_dashboard.py
    ├── optimize/
    │   └── test_performance_optimization.py
    └── test/
        └── test_e2e_integration.py  ← test 모듈 안에 테스트
```

### 문제점
1. **구조 불명확**: 소스와 테스트 혼재
2. **발견 어려움**: pytest가 전체 src를 스캔
3. **CI/CD 복잡**: 테스트 경로 지정 어려움
4. **코드 리뷰**: 변경된 코드와 테스트 찾기 어려움

---

## 목표 구조

```
app/observer/
├── src/                    # 소스 코드만
│   ├── backup/
│   ├── collector/
│   ├── monitoring/
│   ├── observer/
│   └── ...
└── tests/                  # 모든 테스트
    ├── conftest.py         # 공통 fixture
    ├── unit/               # 단위 테스트
    │   ├── backup/
    │   │   └── test_backup_manager.py
    │   ├── collector/
    │   │   └── test_collectors.py
    │   ├── monitoring/
    │   │   └── test_monitoring_dashboard.py
    │   ├── optimize/
    │   │   └── test_performance_optimization.py
    │   └── shared/
    │       ├── test_timezone.py
    │       ├── test_time_helpers.py
    │       └── test_serialization.py
    ├── integration/        # 통합 테스트
    │   └── test_e2e_integration.py
    └── local/              # 로컬 테스트 (수동 실행)
        ├── test_track_a_local.py
        └── test_track_b_local.py
```

---

## 구현 계획

### 단계 1: tests 디렉토리 구조 생성

```bash
mkdir -p app/observer/tests/{unit,integration,local}
mkdir -p app/observer/tests/unit/{backup,collector,monitoring,optimize,shared,decision_pipeline}
```

### 단계 2: conftest.py 생성

**파일**: `app/observer/tests/conftest.py`

```python
"""
Pytest configuration and shared fixtures for Observer tests.

This file is automatically loaded by pytest and provides:
- Path setup for imports
- Common fixtures
- Test utilities
"""
import sys
from pathlib import Path
from typing import Generator

import pytest

# Add source paths
TESTS_DIR = Path(__file__).parent
OBSERVER_DIR = TESTS_DIR.parent
SRC_DIR = OBSERVER_DIR / "src"

for path in [str(OBSERVER_DIR), str(SRC_DIR)]:
    if path not in sys.path:
        sys.path.insert(0, path)


# ============== Fixtures ==============

@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary data directory for tests."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    yield data_dir


@pytest.fixture
def mock_config():
    """Provide a mock configuration for tests."""
    from dataclasses import dataclass
    from datetime import time

    @dataclass
    class MockConfig:
        tz_name: str = "Asia/Seoul"
        trading_start: time = time(9, 0)
        trading_end: time = time(15, 30)
        interval_minutes: int = 10

    return MockConfig()


@pytest.fixture
def sample_order():
    """Provide a sample order for execution tests."""
    from dataclasses import dataclass

    @dataclass
    class SampleOrder:
        decision_id: str = "TEST_001"
        action: str = "buy"
        qty: int = 100
        symbol: str = "005930"
        price: float = 70000.0

    return SampleOrder()


@pytest.fixture
def sample_hint():
    """Provide a sample hint for execution tests."""
    from dataclasses import dataclass

    @dataclass
    class SampleHint:
        reason: str = "test_signal"
        confidence: float = 0.85
        price: float = 70000.0

    return SampleHint()


# ============== Markers ==============

def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "local: marks tests for local-only execution"
    )


# ============== Test Collection ==============

def pytest_collection_modifyitems(config, items):
    """Modify test collection based on markers."""
    # Skip local tests in CI
    if config.getoption("-m") != "local":
        skip_local = pytest.mark.skip(reason="local tests skipped in CI")
        for item in items:
            if "local" in item.keywords:
                item.add_marker(skip_local)
```

### 단계 3: 테스트 파일 이동

#### unit 테스트 이동

```bash
# backup
mv app/observer/src/backup/test_backup_manager.py \
   app/observer/tests/unit/backup/

# monitoring
mv app/observer/src/monitoring/test_monitoring_dashboard.py \
   app/observer/tests/unit/monitoring/

# optimize
mv app/observer/src/optimize/test_performance_optimization.py \
   app/observer/tests/unit/optimize/
```

#### integration 테스트 이동

```bash
# e2e test
mv app/observer/src/test/test_e2e_integration.py \
   app/observer/tests/integration/
```

#### local 테스트 이동

```bash
# local tests (루트에서)
mv app/observer/test_track_a_local.py \
   app/observer/tests/local/

mv app/observer/test_track_b_local.py \
   app/observer/tests/local/
```

### 단계 4: 이동된 테스트 파일 업데이트

**파일**: `app/observer/tests/unit/backup/test_backup_manager.py`

```python
"""
Unit tests for BackupManager.

Moved from src/backup/test_backup_manager.py
"""
import pytest
from pathlib import Path

# conftest.py에서 경로 설정됨
from backup import BackupConfig, create_backup, BackupManifest


class TestBackupManager:
    """Tests for backup manager functionality."""

    def test_create_backup(self, tmp_path: Path):
        """Test basic backup creation."""
        # Setup
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("test content")

        backup_dir = tmp_path / "backups"

        config = BackupConfig(
            source_dir=source,
            backup_dir=backup_dir,
        )

        # Execute
        result = create_backup(config)

        # Verify
        assert result.success
        assert result.backup_path.exists()
        assert result.manifest is not None

    def test_backup_with_manifest(self, tmp_path: Path):
        """Test backup includes manifest."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "data.json").write_text('{"key": "value"}')

        config = BackupConfig(
            source_dir=source,
            backup_dir=tmp_path / "backups",
            include_manifest=True,
        )

        result = create_backup(config)

        assert result.manifest_path is not None
        assert result.manifest_path.exists()
```

**파일**: `app/observer/tests/local/test_track_a_local.py`

```python
"""
Local tests for Track A collector.

These tests require external services and are meant for local development.
Run with: pytest tests/local/ -m local
"""
import pytest

# Mark all tests in this file as local
pytestmark = pytest.mark.local


@pytest.fixture
def track_a_setup():
    """Setup for Track A local tests."""
    # Local-specific setup
    pass


class TestTrackALocal:
    """Local tests for Track A collector."""

    @pytest.mark.slow
    def test_real_data_collection(self, track_a_setup):
        """Test with real market data (requires API)."""
        # This test connects to real services
        pass

    def test_local_file_output(self, track_a_setup, tmp_path):
        """Test output file generation locally."""
        pass
```

### 단계 5: pytest.ini 설정

**파일**: `app/observer/pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Default markers to exclude
addopts = -m "not local" --strict-markers

# Marker definitions
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    local: marks tests for local-only execution (skipped by default)

# Coverage settings
[coverage:run]
source = src
omit = tests/*

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
```

### 단계 6: src/test 디렉토리 정리

```bash
# src/test 디렉토리가 비어있으면 제거
# 또는 필요한 테스트 유틸리티만 남기고 테스트 파일 제거
rm -rf app/observer/src/test/test_*.py

# __init__.py만 남기거나 완전 제거
```

---

## 테스트 실행 가이드

### 일반 테스트 실행
```bash
cd app/observer

# 모든 테스트 (local 제외)
pytest

# 특정 모듈 테스트
pytest tests/unit/backup/

# 통합 테스트만
pytest tests/integration/ -m integration
```

### 로컬 테스트 실행
```bash
# 로컬 테스트 포함
pytest -m local

# 모든 테스트 (로컬 포함)
pytest -m ""
```

### 커버리지 확인
```bash
pytest --cov=src --cov-report=html
```

---

## 검증 방법

### 1. 구조 확인
```bash
tree app/observer/tests

# 예상 출력
tests/
├── conftest.py
├── unit/
│   ├── backup/
│   ├── collector/
│   ├── monitoring/
│   └── ...
├── integration/
└── local/
```

### 2. pytest 수집 확인
```bash
cd app/observer
pytest --collect-only

# 테스트가 올바르게 수집되는지 확인
```

### 3. import 확인
```bash
cd app/observer
pytest tests/unit/backup/test_backup_manager.py -v
```

### 4. 마커 확인
```bash
pytest --markers | grep -E "slow|integration|local"
```

---

## 완료 조건

- [ ] `tests/` 디렉토리 구조 생성됨
- [ ] `tests/conftest.py` 생성됨
- [ ] `tests/unit/` 하위 디렉토리 생성됨
- [ ] `tests/integration/` 생성됨
- [ ] `tests/local/` 생성됨
- [ ] 모든 테스트 파일 이동됨
- [ ] 이동된 테스트 파일 import 업데이트됨
- [ ] `pytest.ini` 설정됨
- [ ] `src/` 내 테스트 파일 제거됨
- [ ] 모든 테스트 통과

---

## 파일 이동 체크리스트

| 원본 위치 | 대상 위치 | 상태 |
|----------|----------|------|
| `src/backup/test_backup_manager.py` | `tests/unit/backup/` | [ ] |
| `src/monitoring/test_monitoring_dashboard.py` | `tests/unit/monitoring/` | [ ] |
| `src/optimize/test_performance_optimization.py` | `tests/unit/optimize/` | [ ] |
| `src/test/test_e2e_integration.py` | `tests/integration/` | [ ] |
| `test_track_a_local.py` | `tests/local/` | [ ] |
| `test_track_b_local.py` | `tests/local/` | [ ] |

---

## 관련 태스크
- [TASK-4.1](TASK-4.1-flatten-structure.md): 폴더 구조 재정립 (선행)
- [TASK-5.1](../phase-5/TASK-5.1-documentation.md): 문서화 (테스트 가이드 포함)
