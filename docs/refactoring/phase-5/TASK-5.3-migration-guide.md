# TASK-5.3: 마이그레이션 가이드 작성

## 태스크 정보
- **Phase**: 5 - 문서화 및 정리
- **우선순위**: Low
- **의존성**: Phase 1-4 완료
- **상태**: 대기

---

## 목표
리팩토링된 코드베이스로의 마이그레이션 가이드를 작성하여 기존 코드 사용자가 새 구조에 쉽게 적응할 수 있도록 합니다.

---

## 생성할 문서

**파일**: `docs/refactoring/MIGRATION_GUIDE.md`

---

## 문서 내용

```markdown
# Observer 리팩토링 마이그레이션 가이드

## 개요

이 문서는 Observer 시스템의 리팩토링된 코드베이스로 마이그레이션하는 방법을 설명합니다.
주요 변경사항과 기존 코드의 업데이트 방법을 안내합니다.

## 목차

1. [주요 변경사항](#주요-변경사항)
2. [폴더 구조 변경](#폴더-구조-변경)
3. [Import 경로 변경](#import-경로-변경)
4. [API 변경사항](#api-변경사항)
5. [설정 변경](#설정-변경)
6. [마이그레이션 단계](#마이그레이션-단계)
7. [FAQ](#faq)

---

## 주요 변경사항

### 1. 폴더 구조
- `app/obs_deploy/app/` → `app/observer/`
- 테스트 파일이 `tests/` 디렉토리로 이동

### 2. 공유 유틸리티
- 새로운 `shared/` 모듈 도입
- 중복 코드가 유틸리티 함수/클래스로 통합

### 3. 모듈 통합
- `maintenance/retention/` → `retention/`
- `maintenance/backup/` → `backup/`

### 4. 베이스 클래스
- `BaseCollector` 추상 클래스 추가
- `BaseExecutor` 추상 클래스 추가

---

## 폴더 구조 변경

### Before
```
app/
└── obs_deploy/
    └── app/
        ├── observer.py
        ├── paths.py
        └── src/
            ├── collector/
            ├── maintenance/
            │   ├── retention/
            │   └── backup/
            └── ...
```

### After
```
app/
└── observer/
    ├── main.py           # observer.py → main.py
    ├── paths.py
    ├── src/
    │   ├── collector/
    │   ├── retention/    # 통합됨
    │   ├── backup/       # 통합됨
    │   └── shared/       # 새로 추가
    └── tests/            # 테스트 분리
```

---

## Import 경로 변경

### 공유 유틸리티

#### Timezone
```python
# Before
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

# After
from shared.timezone import ZoneInfo, get_zoneinfo
```

#### Time Helper
```python
# Before
class MyClass:
    def _now(self):
        if self._tz:
            return datetime.now(self._tz)
        return datetime.now()

# After
from shared.time_helpers import TimeAwareMixin

class MyClass(TimeAwareMixin):
    def __init__(self):
        self._tz_name = "Asia/Seoul"
        self._init_timezone()
    # _now()는 믹스인에서 제공
```

#### Trading Hours
```python
# Before
def _in_trading_hours(self, dt: datetime) -> bool:
    t = dt.time()
    return self.cfg.trading_start <= t <= self.cfg.trading_end

# After
from shared.trading_hours import in_trading_hours

# 함수 직접 사용
if in_trading_hours(dt, self.cfg.trading_start, self.cfg.trading_end):
    ...
```

#### Serialization
```python
# Before
def _safe_to_dict(obj):
    ...

def _fingerprint(order, hint):
    ...

# After
from shared.serialization import safe_to_dict, order_hint_fingerprint

data = safe_to_dict(my_object)
fp = order_hint_fingerprint(order, hint)
```

### Retention 모듈

```python
# Before
from maintenance.retention.policy import RetentionPolicy

# After (경고 발생)
from maintenance.retention import RetentionPolicy  # DeprecationWarning

# After (권장)
from retention.policy import RetentionPolicy
```

### Backup 모듈

```python
# Before
from maintenance.backup.runner import create_backup
from backup.backup_manager import BackupManager

# After
from backup import create_backup, BackupScheduler
```

### Collector

```python
# Before
class TrackACollector:
    def __init__(self, cfg, ...):
        if cfg.tz_name:
            self._tz = ZoneInfo(cfg.tz_name)
        ...

    def _now(self):
        ...

    def _in_trading_hours(self, dt):
        ...

# After
from collector import TrackACollector  # BaseCollector 상속
# _now(), _in_trading_hours() 자동 제공
```

### Executor

```python
# Before
class SimExecutor:
    def _safe_to_dict(self, obj):
        ...

    def _fingerprint(self, order, hint):
        ...

# After
from decision_pipeline.execution_stub import SimExecutor  # BaseExecutor 상속
# 유틸리티 함수는 shared.serialization에서 import
```

---

## API 변경사항

### RetentionPolicy

```python
# Before - 두 가지 다른 API
# maintenance/retention
policy = RetentionPolicy(ttl_days=7)

# retention
policy = RetentionPolicy(raw_snapshot_days=7)

# After - 통합 API
from retention import RetentionPolicy

# TTL 기반 (새 방식)
policy = RetentionPolicy.from_ttl(7)

# 카테고리 기반 (기존 방식)
policy = RetentionPolicy(
    raw_snapshot_days=7,
    pattern_record_days=30,
)

# 모든 옵션
policy = RetentionPolicy(
    ttl_days=7,
    raw_snapshot_days=7,
    pattern_record_days=30,
    include_globs=["*.json"],
)
```

### BackupManifest

```python
# Before
from backup.backup_manager import BackupManifest

# After
from backup import BackupManifest, create_manifest

manifest = create_manifest(
    backup_id="backup_001",
    source_dir=Path("/data"),
)
```

### Executor Result

```python
# Before
result = {"status": "success", "fingerprint": fp}

# After
from decision_pipeline.execution_stub import ExecutionResult, ExecutionStatus

result = ExecutionResult(
    decision_id="D001",
    mode=ExecutionMode.SIMULATION,
    status=ExecutionStatus.SUCCESS,
    fingerprint=fp,
    timestamp=now,
    audit={...},
)
```

---

## 설정 변경

### 환경 변수

변경 없음 - 기존 환경 변수 그대로 사용

### Docker

```yaml
# Before
services:
  observer:
    build:
      context: ./app/obs_deploy

# After
services:
  observer:
    build:
      context: ./app/observer
```

### pyproject.toml

```toml
# Before
[tool.setuptools.packages.find]
where = ["app"]

# After
[tool.setuptools.packages.find]
where = ["."]
include = ["src*"]
```

---

## 마이그레이션 단계

### 1단계: 코드 업데이트

```bash
# 저장소 업데이트
git pull origin main

# 의존성 업데이트
pip install -e app/observer
```

### 2단계: Import 수정

IDE의 찾기/바꾸기 또는 스크립트 사용:

```bash
# 예시: sed 사용
find . -name "*.py" -exec sed -i \
    's/from obs_deploy.app./from /g' {} +

find . -name "*.py" -exec sed -i \
    's/from maintenance.retention import/from retention import/g' {} +
```

### 3단계: 클래스 상속 업데이트

Collector나 Executor를 커스텀했다면:

```python
# Collector
from collector.base import BaseCollector

class MyCollector(BaseCollector):
    ...

# Executor
from decision_pipeline.execution_stub import BaseExecutor

class MyExecutor(BaseExecutor):
    ...
```

### 4단계: 테스트 실행

```bash
cd app/observer
pytest tests/ -v
```

### 5단계: Docker 빌드 확인

```bash
cd app/observer
docker build -t observer:latest .
docker run observer:latest python -c "from src.observer import Observer; print('OK')"
```

---

## FAQ

### Q: 기존 import가 작동하지 않습니다
A: `maintenance.retention` 등 일부 import는 deprecation 경고와 함께 작동합니다.
   새로운 경로로 업데이트하는 것을 권장합니다.

### Q: _now() 메서드가 없다는 에러가 발생합니다
A: TimeAwareMixin을 상속하고 `_init_timezone()`을 호출하세요:
```python
from shared.time_helpers import TimeAwareMixin

class MyClass(TimeAwareMixin):
    def __init__(self):
        self._tz_name = "Asia/Seoul"
        self._init_timezone()
```

### Q: 테스트 파일을 찾을 수 없습니다
A: 테스트가 `tests/` 디렉토리로 이동했습니다.
   `pytest tests/` 명령어를 사용하세요.

### Q: Docker 빌드가 실패합니다
A: Dockerfile의 경로가 업데이트되었는지 확인하세요.
   `WORKDIR /app/observer`를 사용해야 합니다.

### Q: 이전 버전과 호환되나요?
A: Deprecation 경고가 있는 import는 당분간 작동합니다.
   다음 메이저 버전에서 제거될 예정이니 업데이트를 권장합니다.

---

## 지원

문제가 발생하면:
1. 이 가이드의 FAQ 확인
2. `docs/refactoring/` 내 관련 TASK 문서 참조
3. 이슈 생성
```

---

## 검증 방법

### 1. 문서 완성도 확인

```bash
# 마크다운 문법 검사
markdownlint docs/refactoring/MIGRATION_GUIDE.md

# 링크 유효성 확인
markdown-link-check docs/refactoring/MIGRATION_GUIDE.md
```

### 2. 코드 예시 검증

```bash
# 문서 내 코드 예시가 실제로 동작하는지 확인
cd app/observer
python << 'EOF'
from shared.timezone import get_zoneinfo
from shared.time_helpers import TimeAwareMixin
from shared.trading_hours import in_trading_hours
from shared.serialization import safe_to_dict

print("All imports work!")
EOF
```

---

## 완료 조건

- [ ] `MIGRATION_GUIDE.md` 작성됨
- [ ] 주요 변경사항 섹션 완성
- [ ] Import 경로 변경 표 완성
- [ ] API 변경사항 문서화
- [ ] 마이그레이션 단계 작성
- [ ] FAQ 작성
- [ ] 코드 예시 검증됨
- [ ] 마크다운 문법 오류 없음

---

## 관련 태스크
- [TASK-5.1](TASK-5.1-documentation.md): 모듈 문서화
- [TASK-5.2](TASK-5.2-remove-deprecated.md): 폐기 파일 제거
