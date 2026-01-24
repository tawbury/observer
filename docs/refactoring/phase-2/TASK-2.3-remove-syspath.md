# TASK-2.3: sys.path 패턴 제거

## 태스크 정보
- **Phase**: 2 - 모듈 통합
- **우선순위**: High
- **의존성**: 없음
- **상태**: 대기

---

## 목표
12개 파일에서 반복되는 `sys.path.append(APP_ROOT)` 패턴을 제거하고, 적절한 패키지 구조로 대체합니다.

---

## 현재 문제

### 중복 코드 패턴
다음 파일들에서 동일한 패턴이 반복됩니다:

```python
import sys
from pathlib import Path

APP_ROOT = str(Path(__file__).resolve().parents[2])
if APP_ROOT not in sys.path:
    sys.path.append(APP_ROOT)
```

### 영향 파일 목록 (12개+)

| # | 파일 경로 |
|---|----------|
| 1 | `app/obs_deploy/app/src/collector/track_a_collector.py` |
| 2 | `app/obs_deploy/app/src/collector/track_b_collector.py` |
| 3 | `app/obs_deploy/app/src/auth/token_lifecycle_manager.py` |
| 4 | `app/obs_deploy/app/src/gap/gap_detector.py` |
| 5 | `app/obs_deploy/app/src/monitoring/prometheus_metrics.py` |
| 6 | `app/obs_deploy/app/src/monitoring/grafana_dashboard.py` |
| 7 | `app/obs_deploy/app/src/optimize/performance_profiler.py` |
| 8 | `app/obs_deploy/app/src/backup/backup_manager.py` |
| 9 | `app/obs_deploy/app/test_track_a_local.py` |
| 10 | `app/obs_deploy/app/test_track_b_local.py` |
| 11 | `app/obs_deploy/app/src/retention/cleaner.py` |
| 12 | `app/obs_deploy/app/src/maintenance/coordinator.py` |

### 문제점

1. **코드 중복**: 동일한 경로 설정 코드가 12개 이상 파일에 반복
2. **취약한 경로 계산**: `parents[2]` 같은 하드코딩된 인덱스 사용
3. **유지보수 어려움**: 폴더 구조 변경 시 모든 파일 수정 필요
4. **IDE 지원 부족**: 동적 경로 추가로 인해 IDE 자동완성 제한

---

## 구현 계획

### 1. 패키지 설정 파일 생성

**파일**: `app/obs_deploy/pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "observer"
version = "1.0.0"
description = "Market Observer System"
requires-python = ">=3.10"

[tool.setuptools.packages.find]
where = ["app"]
include = ["*"]

[tool.setuptools.package-data]
"*" = ["*.json", "*.yaml", "*.yml", "*.txt"]
```

또는 최소한의 **setup.py**:

```python
# app/obs_deploy/setup.py
from setuptools import setup, find_packages

setup(
    name="observer",
    version="1.0.0",
    packages=find_packages(where="app"),
    package_dir={"": "app"},
)
```

### 2. src 디렉토리 패키지화

**파일**: `app/obs_deploy/app/src/__init__.py`

```python
"""
Observer source package.

This package contains all source modules for the Observer system.
"""
__version__ = "1.0.0"

# Ensure proper package structure
from pathlib import Path

PACKAGE_ROOT = Path(__file__).parent.parent
SRC_ROOT = Path(__file__).parent
```

### 3. 상대 import로 전환

각 파일에서 다음과 같이 변경합니다:

#### Before (track_a_collector.py)
```python
import sys
from pathlib import Path

APP_ROOT = str(Path(__file__).resolve().parents[2])
if APP_ROOT not in sys.path:
    sys.path.append(APP_ROOT)

from paths import observer_asset_dir, observer_asset_file
from provider import ProviderEngine, KISAuth
```

#### After (track_a_collector.py)
```python
from pathlib import Path

from paths import observer_asset_dir, observer_asset_file
from provider import ProviderEngine, KISAuth
```

또는 상대 import 사용:
```python
from ..paths import observer_asset_dir, observer_asset_file
from ..provider import ProviderEngine, KISAuth
```

### 4. 파일별 수정 사항

#### 모든 영향 파일에서 제거할 코드:
```python
# 이 블록 전체 제거
import sys
from pathlib import Path

APP_ROOT = str(Path(__file__).resolve().parents[2])
if APP_ROOT not in sys.path:
    sys.path.append(APP_ROOT)
```

#### `src/collector/track_a_collector.py`
```python
# Before
import sys
from pathlib import Path
APP_ROOT = str(Path(__file__).resolve().parents[2])
if APP_ROOT not in sys.path:
    sys.path.append(APP_ROOT)

from paths import observer_asset_dir

# After
from paths import observer_asset_dir
```

#### `src/collector/track_b_collector.py`
```python
# Before
import sys
from pathlib import Path
APP_ROOT = str(Path(__file__).resolve().parents[2])
if APP_ROOT not in sys.path:
    sys.path.append(APP_ROOT)

from provider import ProviderEngine

# After
from provider import ProviderEngine
```

### 5. 테스트 파일 처리

테스트 파일은 패키지 외부에 있을 수 있으므로, conftest.py 사용:

**파일**: `app/obs_deploy/app/conftest.py`

```python
"""
Pytest configuration for Observer tests.

Ensures proper package paths are set up before tests run.
"""
import sys
from pathlib import Path

# Add app directory to path for testing
APP_DIR = Path(__file__).parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# Add src directory
SRC_DIR = APP_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
```

이후 테스트 파일에서는 sys.path 조작 불필요:

```python
# test_track_a_local.py
# Before
import sys
from pathlib import Path
APP_ROOT = str(Path(__file__).resolve().parent)
if APP_ROOT not in sys.path:
    sys.path.append(APP_ROOT)

# After
# conftest.py에서 처리되므로 제거
from collector.track_a_collector import TrackACollector
```

### 6. __main__.py 업데이트

**파일**: `app/obs_deploy/app/__main__.py`

```python
"""
Entry point for running observer as a module.

Usage:
    python -m app
    python -m observer (after package install)
"""
import sys
from pathlib import Path

# Ensure src is in path when running as module
_app_dir = Path(__file__).parent
_src_dir = _app_dir / "src"

if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from observer import main

if __name__ == "__main__":
    main()
```

---

## 마이그레이션 단계

### 단계 1: 패키지 설정 추가
1. `pyproject.toml` 또는 `setup.py` 생성
2. `src/__init__.py` 업데이트
3. 개발 모드로 설치: `pip install -e .`

### 단계 2: conftest.py 추가
1. `app/conftest.py` 생성
2. 테스트 실행 확인

### 단계 3: 파일별 sys.path 제거
1. 각 파일에서 sys.path 블록 제거
2. import 문 확인/수정
3. 파일별 테스트

### 단계 4: 검증
1. 전체 테스트 실행
2. Docker 빌드 확인
3. 실제 실행 테스트

---

## 검증 방법

### 1. sys.path 패턴 검색
```bash
# 변경 후 이 명령어 결과가 최소화되어야 함 (conftest.py, __main__.py만 남음)
grep -rn "sys.path.append" --include="*.py" app/obs_deploy/app/
grep -rn "APP_ROOT = str(Path" --include="*.py" app/obs_deploy/app/
```

### 2. import 테스트
```python
# tests/test_imports.py
def test_all_imports():
    """Verify all modules can be imported without sys.path manipulation."""
    # These should all work without manual path setup
    from collector.track_a_collector import TrackACollector
    from collector.track_b_collector import TrackBCollector
    from auth.token_lifecycle_manager import TokenLifecycleManager
    from gap.gap_detector import GapDetector
    from provider import ProviderEngine
    from paths import observer_asset_dir
```

### 3. 통합 테스트
```bash
# 패키지 설치 후 테스트
cd app/obs_deploy
pip install -e .
pytest app/ -v

# Docker에서 테스트
docker build -t observer-test .
docker run observer-test python -c "from observer import Observer; print('OK')"
```

---

## 완료 조건

- [ ] `pyproject.toml` 또는 `setup.py` 생성됨
- [ ] `conftest.py` 생성됨
- [ ] 모든 12개 파일에서 sys.path 패턴 제거됨
- [ ] import 문이 정상 작동함
- [ ] 모든 테스트 통과
- [ ] Docker 빌드 성공
- [ ] `pip install -e .` 성공

---

## 주의사항

1. **순서 중요**: conftest.py와 패키지 설정을 먼저 추가한 후 sys.path 패턴 제거

2. **Docker 호환성**: Dockerfile에서도 패키지가 올바르게 설치되는지 확인
   ```dockerfile
   COPY app/obs_deploy /app
   WORKDIR /app
   RUN pip install -e .
   ```

3. **상대 import 주의**: 상대 import (`.`, `..`) 사용 시 패키지 구조 주의

4. **테스트 순서**: 파일 하나씩 수정하고 테스트하여 문제 조기 발견

---

## 롤백 계획

문제 발생 시:
1. conftest.py를 통해 기존 sys.path 로직 복원
2. 개별 파일 복원 가능

```python
# 긴급 복원용 conftest.py
import sys
from pathlib import Path

APP_ROOT = str(Path(__file__).resolve().parent)
SRC_ROOT = str(Path(__file__).resolve().parent / "src")

for path in [APP_ROOT, SRC_ROOT]:
    if path not in sys.path:
        sys.path.insert(0, path)
```

---

## 관련 태스크
- [TASK-4.1](../phase-4/TASK-4.1-flatten-structure.md): 폴더 구조 재정립 (이 태스크 이후)
