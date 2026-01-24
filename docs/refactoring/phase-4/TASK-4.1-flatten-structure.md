# TASK-4.1: 폴더 구조 재정립

## 태스크 정보
- **Phase**: 4 - 폴더 구조 재정립
- **우선순위**: Medium
- **의존성**: Phase 1, 2, 3 완료
- **위험도**: High (전체 import 경로 변경)
- **상태**: 대기

---

## 목표
중첩된 `app/obs_deploy/app/` 구조를 `app/observer/`로 재정립하여 명확한 패키지 구조를 확립합니다.

---

## 현재 문제

### 현재 구조
```
app/
├── logs/
│   └── system/
└── obs_deploy/
    ├── app/                  ← 중첩된 "app" (문제점)
    │   ├── __init__.py
    │   ├── __main__.py
    │   ├── observer.py
    │   ├── paths.py
    │   ├── config/
    │   ├── data/
    │   ├── logs/
    │   └── src/
    │       └── (21개 모듈)
    ├── data/
    ├── migrations/
    ├── monitoring/
    ├── scripts/
    ├── secrets/
    ├── docker-compose.yml
    ├── Dockerfile
    └── requirements.txt
```

### 문제점
1. **이름 중복**: `app/obs_deploy/app/` 경로에서 "app" 두 번 등장
2. **명확성 부족**: 패키지 이름이 역할을 반영하지 않음
3. **깊은 중첩**: 실제 코드까지 경로가 너무 깊음
4. **import 복잡성**: `from obs_deploy.app.src.xxx` 형태의 긴 import

---

## 목표 구조

### Option B: 이름 명확화 (선택됨)
```
app/
├── logs/
│   └── system/
└── observer/                 ← 명확한 이름
    ├── __init__.py
    ├── __main__.py
    ├── main.py               ← observer.py 이름 변경
    ├── paths.py
    ├── config/
    ├── data/
    ├── logs/
    ├── src/
    │   └── (21개 모듈)
    ├── docker-compose.yml
    ├── Dockerfile
    ├── requirements.txt
    └── ...
```

---

## 구현 계획

### 단계 1: 새 디렉토리 구조 생성

```bash
# 새 observer 디렉토리 생성
mkdir -p app/observer

# obs_deploy 내용 복사 (app 제외)
cp -r app/obs_deploy/data app/observer/
cp -r app/obs_deploy/migrations app/observer/
cp -r app/obs_deploy/monitoring app/observer/
cp -r app/obs_deploy/scripts app/observer/
cp -r app/obs_deploy/secrets app/observer/
cp app/obs_deploy/*.yml app/observer/
cp app/obs_deploy/*.txt app/observer/
cp app/obs_deploy/Dockerfile app/observer/
cp app/obs_deploy/.env* app/observer/

# obs_deploy/app 내용을 observer로 이동
cp -r app/obs_deploy/app/* app/observer/
```

### 단계 2: 파일 이름 변경

```bash
# observer.py → main.py (명확성)
mv app/observer/observer.py app/observer/main.py
```

### 단계 3: Import 경로 업데이트

#### 영향받는 파일 패턴

| 파일 유형 | 수정 내용 |
|----------|----------|
| Python 파일 | `from obs_deploy.app.xxx` → `from xxx` |
| Dockerfile | 경로 업데이트 |
| docker-compose.yml | 볼륨 마운트 경로 |
| 배포 스크립트 | 경로 참조 |

#### Python Import 변경 예시

**Before:**
```python
# 외부에서 접근 시
from obs_deploy.app.src.observer import Observer
from obs_deploy.app.paths import observer_asset_dir
```

**After:**
```python
# 패키지 설치 후
from observer.src.observer import Observer
from observer.paths import observer_asset_dir
```

### 단계 4: Docker 설정 업데이트

**파일**: `app/observer/Dockerfile`

```dockerfile
# Before
WORKDIR /app/obs_deploy/app
COPY app/ /app/obs_deploy/app/

# After
WORKDIR /app/observer
COPY . /app/observer/

# Entry point 업데이트
CMD ["python", "-m", "main"]
```

**파일**: `app/observer/docker-compose.yml`

```yaml
# Before
services:
  observer:
    build:
      context: .
    volumes:
      - ./app:/app/obs_deploy/app

# After
services:
  observer:
    build:
      context: .
    volumes:
      - ./:/app/observer
```

### 단계 5: paths.py 업데이트

**파일**: `app/observer/paths.py`

```python
"""
Path configuration for Observer system.

Updated for new directory structure.
"""
from pathlib import Path
import os

# Project root detection
def _find_project_root() -> Path:
    """Find project root by looking for key markers."""
    current = Path(__file__).parent

    # In new structure, this file is at app/observer/paths.py
    # So parent is app/observer, parent.parent is app
    if current.name == "observer":
        return current.parent

    # Fallback for other scenarios
    for parent in current.parents:
        if (parent / "observer").is_dir():
            return parent
        if (parent / "requirements.txt").is_file():
            return parent

    return current


PROJECT_ROOT = _find_project_root()
OBSERVER_ROOT = PROJECT_ROOT / "observer"


def project_root() -> Path:
    """Get project root directory."""
    return PROJECT_ROOT


def observer_root() -> Path:
    """Get observer package root directory."""
    return OBSERVER_ROOT


def config_dir() -> Path:
    """Get configuration directory."""
    return OBSERVER_ROOT / "config"


def observer_asset_dir() -> Path:
    """Get observer asset directory for runtime data."""
    env_dir = os.environ.get("OBSERVER_DATA_DIR")
    if env_dir:
        return Path(env_dir)
    return OBSERVER_ROOT / "data" / "observer"


# ... 나머지 함수들도 유사하게 업데이트
```

### 단계 6: pyproject.toml 업데이트

**파일**: `app/observer/pyproject.toml`

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
where = ["."]
include = ["src*", "config*"]

[tool.setuptools.package-data]
"*" = ["*.json", "*.yaml", "*.yml", "*.txt"]
```

### 단계 7: 기존 구조 제거

```bash
# 확인 후 제거
rm -rf app/obs_deploy
```

---

## 마이그레이션 체크리스트

### 파일 이동
- [ ] `obs_deploy/data/` → `observer/data/`
- [ ] `obs_deploy/migrations/` → `observer/migrations/`
- [ ] `obs_deploy/monitoring/` → `observer/monitoring/`
- [ ] `obs_deploy/scripts/` → `observer/scripts/`
- [ ] `obs_deploy/secrets/` → `observer/secrets/`
- [ ] `obs_deploy/app/*` → `observer/`
- [ ] Docker 관련 파일들

### Import 업데이트
- [ ] `observer.py` → `main.py`
- [ ] 모든 Python 파일의 import 경로
- [ ] `paths.py` 경로 계산 로직

### 설정 업데이트
- [ ] Dockerfile
- [ ] docker-compose.yml
- [ ] docker-compose.server.yml
- [ ] pyproject.toml
- [ ] CI/CD 파이프라인

### 삭제
- [ ] `obs_deploy/` 디렉토리
- [ ] `observer_backup_*.py` 파일들

---

## 검증 방법

### 1. 구조 확인
```bash
# 새 구조 확인
tree app/observer -L 2

# 예상 출력
app/observer/
├── __init__.py
├── __main__.py
├── main.py
├── paths.py
├── config/
├── data/
├── src/
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

### 2. Import 테스트
```bash
cd app/observer
pip install -e .
python -c "from src.observer import Observer; print('OK')"
python -c "from paths import observer_asset_dir; print(observer_asset_dir())"
```

### 3. Docker 빌드
```bash
cd app/observer
docker build -t observer:test .
docker run observer:test python -c "from src.observer import Observer; print('OK')"
```

### 4. 테스트 실행
```bash
cd app/observer
pytest . -v
```

---

## 완료 조건

- [ ] `app/observer/` 디렉토리 생성됨
- [ ] 모든 파일이 새 위치로 이동됨
- [ ] `observer.py` → `main.py` 이름 변경됨
- [ ] `paths.py` 업데이트됨
- [ ] Dockerfile 업데이트됨
- [ ] docker-compose.yml 업데이트됨
- [ ] pyproject.toml 업데이트됨
- [ ] 모든 테스트 통과
- [ ] Docker 빌드 성공
- [ ] `obs_deploy/` 삭제됨

---

## 롤백 계획

문제 발생 시:
1. Git에서 변경 전 상태로 복원
2. `obs_deploy/` 구조 유지

```bash
# 긴급 롤백
git checkout HEAD~1 -- app/obs_deploy
rm -rf app/observer
```

---

## 주의사항

1. **순서 중요**: Phase 1-3 완료 후 진행
2. **충분한 테스트**: 각 단계마다 테스트 실행
3. **배포 파이프라인**: CI/CD 설정도 함께 업데이트
4. **환경 변수**: OBSERVER_* 환경 변수 경로 확인
5. **볼륨 마운트**: 프로덕션 Docker 볼륨 경로 업데이트

---

## 관련 태스크
- [TASK-2.3](../phase-2/TASK-2.3-remove-syspath.md): sys.path 패턴 제거 (선행)
- [TASK-4.2](TASK-4.2-reorganize-tests.md): 테스트 재구성 (이 태스크 이후)
