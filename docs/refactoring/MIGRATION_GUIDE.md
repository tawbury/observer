# 리팩토링 마이그레이션 가이드

이 문서는 2026년 1월 리팩토링 이후 코드 변경사항과 마이그레이션 방법을 설명합니다.

## 개요

- **리팩토링 기간**: 2026-01-24
- **커밋 범위**: 30fae72 ~ 현재
- **영향 범위**: 160+ 파일, 5개 Phase

## 주요 변경사항 요약

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| 폴더 구조 | `app/obs_deploy/app/` | `app/observer/` |
| 테스트 위치 | 소스 코드 혼재 | `tests/unit/`, `tests/integration/`, `tests/local/` |
| Timezone 처리 | 각 파일마다 중복 | `shared.timezone` 모듈 |
| Time 헬퍼 | `_now()` 메서드 중복 | `TimeAwareMixin` |
| Collector | 중복 코드 | `BaseCollector` 추상 클래스 |
| Executor | 중복 코드 | `BaseExecutor` 추상 클래스 |

---

## Phase별 마이그레이션 가이드

### Phase 1: 공유 유틸리티 사용

#### 1.1 Timezone 관련 Import 변경

**변경 전**:
```python
try:
    from zoneinfo import ZoneInfo
    ZONEINFO_AVAILABLE = True
except ImportError:
    ZoneInfo = None
    ZONEINFO_AVAILABLE = False

# 매 파일마다 반복
```

**변경 후**:
```python
from shared.timezone import get_zoneinfo, now_with_tz

# 간단하게 사용
kst = get_zoneinfo("Asia/Seoul")
now = now_with_tz("Asia/Seoul")
```

#### 1.2 `_now()` 메서드 제거

**변경 전**:
```python
class MyCollector:
    def __init__(self):
        self._tz = ZoneInfo("Asia/Seoul")
    
    def _now(self) -> datetime:
        if self._tz:
            return datetime.now(self._tz)
        return datetime.now(timezone.utc)
```

**변경 후**:
```python
from shared.time_helpers import TimeAwareMixin

class MyCollector(TimeAwareMixin):
    def __init__(self):
        self._tz_name = "Asia/Seoul"
        self._init_timezone()
    
    # _now()는 자동으로 사용 가능
    def process(self):
        current_time = self._now()
```

#### 1.3 Trading Hours 판별

**변경 전**:
```python
def _in_trading_hours(self, dt: datetime) -> bool:
    t = dt.time()
    return time(9, 0) <= t <= time(15, 30)
```

**변경 후**:
```python
from shared.trading_hours import in_trading_hours, KRX_REGULAR_SESSION

is_trading = in_trading_hours(dt, KRX_REGULAR_SESSION.start, KRX_REGULAR_SESSION.end)
```

#### 1.4 직렬화 및 핑거프린트

**변경 전**:
```python
def _safe_to_dict(obj):
    if is_dataclass(obj):
        return asdict(obj)
    # ... 중복 코드

def _fingerprint(order, hint):
    data = json.dumps(...)
    return hashlib.sha256(data.encode()).hexdigest()[:16]
```

**변경 후**:
```python
from shared.serialization import safe_to_dict, order_hint_fingerprint

data_dict = safe_to_dict(my_object)
fp = order_hint_fingerprint(order, hint)
```

---

### Phase 2: 모듈 통합

#### 2.1 Retention 정책 사용

**변경 전**:
```python
from maintenance.retention.policy import RetentionPolicy  # 구 위치
```

**변경 후**:
```python
from retention.policy import RetentionPolicy

# TTL 모드
policy = RetentionPolicy.from_ttl(days=7)

# 카테고리 모드
policy = RetentionPolicy.from_categories(
    raw_snapshot_days=7,
    pattern_record_days=30
)
```

#### 2.2 Backup 관리

**변경 전**:
```python
from backup.backup_manager import BackupManager  # 중복 파일 존재
from maintenance.backup.manifest import BackupManifest
```

**변경 후**:
```python
from backup.manager import BackupManager
from backup.manifest import BackupManifest
```

#### 2.3 sys.path 제거

**변경 전**:
```python
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(APP_ROOT))

from src.collector import ...  # 절대 import
```

**변경 후**:
```python
# sys.path 조작 불필요
from collector import ...  # 상대 import 사용
```

---

### Phase 3: 베이스 클래스 사용

#### 3.1 Collector 구현

**변경 전**:
```python
class MyCollector:
    def __init__(self, config):
        self.cfg = config
        self._tz = ZoneInfo(config.tz_name)
        # 중복 초기화 코드
    
    def _now(self):
        # 중복 메서드
    
    def _in_trading_hours(self):
        # 중복 메서드
```

**변경 후**:
```python
from collector.base import BaseCollector, CollectorConfig
from typing import Dict, Any

class MyCollector(BaseCollector):
    async def collect_once(self) -> Dict[str, Any]:
        """필수 구현 메서드"""
        if not self.is_in_trading_hours():
            return {"status": "skip"}
        
        # 수집 로직
        return {"status": "success", "data": data}
```

#### 3.2 Executor 구현

**변경 전**:
```python
class MyExecutor(IExecution):
    def execute(self, order, hint, context):
        # 직렬화, 핑거프린트, 에러 처리 모두 중복
```

**변경 후**:
```python
from decision_pipeline.execution_stub.base_executor import BaseExecutor, ExecutionMode

class MyExecutor(BaseExecutor):
    def __init__(self):
        super().__init__(mode=ExecutionMode.REAL)
    
    def _do_execute(self, *, order, hint, context, decision_id, fingerprint):
        """핵심 로직만 구현"""
        # 실행 로직
        return ExecutionResult(...)
```

---

### Phase 4: 폴더 구조 변경

#### 4.1 Import 경로 업데이트 (자동 완료)

**변경 전**:
```dockerfile
# Dockerfile
COPY app/obs_deploy/app/observer.py /app/
COPY app/obs_deploy/app/src/ /app/src/
```

**변경 후**:
```dockerfile
# Dockerfile
COPY app/observer/observer.py /app/
COPY app/observer/src/ /app/src/
```

#### 4.2 테스트 파일 위치

**변경 전**:
```
app/observer/
├── test_track_a_local.py
├── test_track_b_local.py
└── src/
    ├── backup/test_backup_manager.py
    ├── monitoring/test_monitoring_dashboard.py
    └── test/test_e2e_integration.py
```

**변경 후**:
```
tests/
├── local/
│   ├── test_track_a_local.py
│   └── test_track_b_local.py
├── unit/
│   ├── backup/test_backup_manager.py
│   ├── monitoring/test_monitoring_dashboard.py
│   └── optimize/test_performance_optimization.py
└── integration/
    └── test_e2e_integration.py
```

---

## 체크리스트: 새 코드 작성 시

### Collector 작성 시
- [ ] `BaseCollector` 상속
- [ ] `collect_once()` async 메서드 구현
- [ ] `_now()`, `is_in_trading_hours()` 사용 (재정의 금지)
- [ ] `on_error` 콜백으로 에러 전파

### Executor 작성 시
- [ ] `BaseExecutor` 상속
- [ ] `_do_execute()` 메서드 구현
- [ ] `ExecutionResult` 반환
- [ ] 핑거프린트 자동 생성 활용

### 유틸리티 함수 작성 시
- [ ] 3개 이상 파일에서 사용되면 `shared/` 모듈로 이동
- [ ] 타입 힌트 필수
- [ ] Docstring 작성
- [ ] Unit 테스트 추가

---

## 문제 해결

### Import 에러 발생 시

```python
ModuleNotFoundError: No module named 'shared'
```

**해결책**:
```bash
# PYTHONPATH 확인
echo $PYTHONPATH  # /app/src:/app 포함 필요

# Docker 환경변수 확인
ENV PYTHONPATH=/app/src:/app
```

### Timezone 관련 에러

```python
ZoneInfoNotFoundError: 'Asia/Seoul'
```

**해결책**:
```bash
# tzdata 패키지 설치
pip install tzdata
```

### 테스트 실행 오류

**변경 전**:
```bash
pytest app/observer/test_track_a_local.py  # 파일 없음
```

**변경 후**:
```bash
pytest tests/local/test_track_a_local.py
```

---

## 롤백 가이드

만약 문제가 발생하면 각 Phase의 커밋으로 롤백 가능:

```bash
# Phase 1-2 이전으로 롤백
git reset --hard 4dc8398

# Phase 3 이전으로 롤백
git reset --hard 30fae72

# Phase 4 이전으로 롤백
git reset --hard 46b3ff0
```

**경고**: 롤백 시 최신 변경사항이 손실됩니다. 필요한 경우 백업 브랜치 생성:
```bash
git branch backup-before-rollback
git reset --hard <commit>
```

---

## 추가 리소스

- [Phase별 Task 문서](./phase-1/) - 상세 구현 가이드
- [ROADMAP.md](./ROADMAP.md) - 전체 리팩토링 계획
- [PROGRESS.md](./PROGRESS.md) - 진행 상황 및 통계
- [shared 모듈 README](../../app/observer/src/shared/README.md)
- [collector 모듈 README](../../app/observer/src/collector/README.md)
- [execution_stub 모듈 README](../../app/observer/src/decision_pipeline/execution_stub/README.md)

---

## 문의

리팩토링 관련 문의사항은 프로젝트 이슈 트래커에 등록하세요.
