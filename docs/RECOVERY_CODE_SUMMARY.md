# 백업 코드 상세 복구 가이드

**작성일**: 2026-01-20
**상태**: UTF-16 → UTF-8 변환 완료, 코드 분석 완료

---

## 🎯 핵심 복구 파일 4개

### 1️⃣ api_server.py (450 줄) - ⭐⭐⭐⭐⭐ 최고 우선순위

**위치**: `backup/e531842/api_server.py.utf8.py`

**문제**: 현재 프로젝트의 `app/obs_deploy/app/observer.py`는 단순히 대기만 하는 32줄 코드

**해결책**: FastAPI 기반 REST API 서버 복원

#### A. Pydantic 모델 (데이터 검증)
```python
# 모두 현재 프로젝트에서 필요함
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    uptime_seconds: float
    details: Dict[str, Any]

class ReadinessResponse(BaseModel):
    ready: bool
    timestamp: str
    checks: Dict[str, bool]
    details: Dict[str, Any]

class StatusResponse(BaseModel):
    status: str
    timestamp: str
    observer: Dict[str, Any]
    system: Dict[str, Any]
    metrics: Dict[str, Any]

class MetricsResponse(BaseModel):
    timestamp: str
    observer_metrics: Dict[str, Any]
    system_metrics: Dict[str, Any]
```

#### B. ObserverStatusTracker 클래스
```python
class ObserverStatusTracker:
    """Observer 시스템 상태 추적"""

    def __init__(self):
        self._start_time: datetime
        self._observer_running: bool
        self._eventbus_connected: bool
        self._kis_connected: bool
        self._db_connected: bool
        self._last_snapshot_time: Optional[datetime]
        self._total_snapshots: int
        self._total_errors: int

    # 상태 마킹 메서드
    def mark_observer_started() -> None
    def mark_observer_stopped() -> None
    def mark_eventbus_connected(connected: bool) -> None
    def mark_kis_connected(connected: bool) -> None
    def mark_db_connected(connected: bool) -> None
    def record_snapshot() -> None
    def record_error() -> None

    # 상태 조회 메서드
    def get_uptime() -> float
    def get_status() -> Dict[str, Any]
    def is_healthy() -> bool  # Observer 실행 && EventBus 연결
    def is_ready() -> bool    # 모든 필수 컴포넌트 준비
    def _has_sufficient_disk_space() -> bool  # 80% 임계값
```

#### C. FastAPI 엔드포인트 (6개)
```python
@app.get("/")
async def root():
    """서비스 정보 및 사용 가능한 엔드포인트 반환"""

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Kubernetes Liveness Probe
    - 200: Healthy (Observer 실행 중 && EventBus 연결)
    - 503: Unhealthy
    """

@app.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    """
    Kubernetes Readiness Probe
    - 200: Ready (모든 필수 컴포넌트 준비)
    - 503: Not Ready
    """

@app.get("/status", response_model=StatusResponse)
async def get_status():
    """
    전체 시스템 상태
    - Observer 상태
    - 시스템 메트릭 (CPU, 메모리, 디스크)
    - Observer 메트릭
    """

@app.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    """
    Prometheus 노출 형식
    - Observer 메트릭
    - 시스템 메트릭
    - 카운터, 게이지 등
    """

@app.get("/metrics/observer", response_model=MetricsResponse)
async def observer_metrics():
    """
    Observer 상세 메트릭 (JSON)
    - 모든 성능 메트릭
    - 시스템 리소스 사용량
    """
```

#### D. 라이프사이클 관리
```python
@app.on_event("startup")
async def startup_event():
    """API 서버 시작"""

@app.on_event("shutdown")
async def shutdown_event():
    """API 서버 종료 (Observer 상태 업데이트)"""
```

#### E. 유틸리티 함수
```python
async def run_api_server(host: str = "0.0.0.0", port: int = 8000):
    """Uvicorn 서버 실행"""

def start_api_server_background(host: str = "0.0.0.0", port: int = 8000):
    """백그라운드 비동기 태스크로 서버 실행"""
```

#### 복구 액션
```bash
# 1. 파일 복사
cp backup/e531842/api_server.py.utf8.py app/obs_deploy/app/src/observer/api_server_restored.py

# 2. 현재 프로젝트의 api_server.py와 비교
diff -u app/obs_deploy/app/src/observer/api_server.py app/obs_deploy/app/src/observer/api_server_restored.py

# 3. 변경사항 검토 후 병합
# - 현재 코드가 있으면: 버전 비교 및 최신 기능 병합
# - 없으면: 직접 사용
```

---

### 2️⃣ main.py (109 줄) - Docker 엔트리 포인트

**위치**: `backup/e531842/main.py.utf8.py`

**문제**: 현재의 단순화된 대기 루프

**해결책**: Docker + FastAPI 완전 통합

```python
def configure_environment():
    """Docker 환경 변수 설정"""
    os.environ.setdefault("OBSERVER_STANDALONE", "1")
    os.environ.setdefault("PYTHONPATH", "/app/src:/app")
    os.environ.setdefault("OBSERVER_DATA_DIR", "/app/data/observer")
    os.environ.setdefault("OBSERVER_LOG_DIR", "/app/logs")

async def run_observer_with_api():
    """Observer 시스템을 FastAPI 서버와 함께 실행"""
    configure_environment()

    # 1. 로깅 설정
    setup_observer_logging(
        log_level="INFO",
        enable_file_logging=True,
        enable_console_logging=True,
        base_log_filename="observer"
    )

    # 2. 이벤트 버스 및 싱크 초기화
    event_bus = EventBus([
        JsonlFileSink("observer.jsonl", enable_rotation=True)
    ])

    # 3. Observer 생성
    observer = Observer(
        session_id=f"observer-{uuid4()}",
        mode="DOCKER",
        event_bus=event_bus
    )

    # 4. StatusTracker 가져오기
    status_tracker = get_status_tracker()

    # 5. Observer 시작
    await observer.start()
    status_tracker.mark_observer_started()
    status_tracker.mark_eventbus_connected(True)

    # 6. FastAPI 서버를 백그라운드 태스크로 시작
    api_task = asyncio.create_task(run_api_server(host="0.0.0.0", port=8000))

    # 7. API 서버 유지
    await api_task
```

#### 복구 액션
```bash
# 1. main.py와 비교
diff app/obs_deploy/app/observer.py backup/e531842/main.py.utf8.py

# 2. Observer 실행 로직 업그레이드
cp backup/e531842/main.py.utf8.py app/obs_deploy/app/observer_new.py
```

---

### 3️⃣ Event Bus & Logging System

#### 3-1. event_bus.py (194 줄)

**위치**: `backup/e531842/event_bus.py.utf8.py`

**현재 위치**: `app/obs_deploy/app/src/observer/event_bus.py` (존재하는지 확인 필요)

**복구 액션**:
```bash
# 1. 현재 버전과 비교
diff app/obs_deploy/app/src/observer/event_bus.py backup/e531842/event_bus.py.utf8.py

# 2. 차이가 있으면 최신 버전 사용
# - SnapshotSink (추상 기본 클래스)
# - JsonlFileSink (파일 저장)
# - EventBus (라우팅)
# - RotationConfig, RotationManager 통합
```

**핵심 기능**:
```python
class SnapshotSink(ABC):
    """PatternRecord를 저장하는 추상 싱크"""
    @abstractmethod
    def publish(self, record: PatternRecord) -> None:
        pass

class JsonlFileSink(SnapshotSink):
    """JSONL 파일에 append-only로 저장"""
    def __init__(self, filename: str, rotation_config: Optional[RotationConfig] = None):
        self.base_dir = observer_asset_dir()
        self.file_path = observer_asset_file(filename)
        # 로테이션 설정 (시간 기반)

    def publish(self, record: PatternRecord) -> None:
        # 로테이션 체크
        # 파일에 JSON 한 줄 추가
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    def get_rotation_stats(self) -> dict:
        """로테이션 통계 반환"""

class EventBus:
    """모든 Sink에 레코드를 발송"""
    def __init__(self, sinks: Iterable[SnapshotSink]):
        self._sinks = list(sinks)

    def dispatch(self, record: PatternRecord) -> None:
        """모든 싱크에 레코드 전달"""
        for sink in self._sinks:
            try:
                sink.publish(record)
            except Exception:
                logger.exception("Unexpected exception from SnapshotSink")
```

#### 3-2. logging_config.py (~250 줄)

**위치**: `backup/e531842/logging_config.py.utf8.py`

**기능**:
```python
def setup_observer_logging(
    log_level: str = "INFO",
    enable_file_logging: bool = True,
    enable_console_logging: bool = True,
    base_log_filename: str = "observer"
) -> None:
    """Observer 로깅 설정"""
    # 포매터, 핸들러 설정
    # 파일 및 콘솔 로깅 활성화
    # 로그 레벨 설정
```

#### 3-3. log_rotation.py (~250 줄)

**위치**: `backup/e531842/log_rotation.py.utf8.py`

**기능**:
```python
@dataclass
class RotationConfig:
    """로테이션 설정"""
    enable_rotation: bool = True
    window_ms: int = 3600000  # 1시간
    max_file_size_bytes: Optional[int] = None

class RotationManager:
    """시간 기반 로그 로테이션 관리"""
    def __init__(self, config: RotationConfig):
        self.config = config

    def get_current_file_path(self) -> Path:
        """현재 로테이션 윈도우의 파일 경로 반환"""
        # Format: {base}_{YYYYMMDD_HHMM}.jsonl

    def get_rotation_stats(self) -> dict:
        """로테이션 통계"""
```

---

### 4️⃣ 테스트 파일들

#### 4-1. test_events_docker.py (92 줄)

**위치**: `backup/e531842/test_events_docker.py.utf8.py`

**목적**: Docker 환경에서 테스트 이벤트 생성

```python
async def generate_test_events():
    """테스트 PatternRecord 이벤트 생성"""
    setup_observer_logging(...)

    event_bus = EventBus([
        JsonlFileSink("test_events.jsonl", enable_rotation=False)
    ])

    observer = Observer(
        session_id=f"test-{uuid4()}",
        mode="TEST",
        event_bus=event_bus
    )

    await observer.start()

    # 3개의 테스트 스냅샷 생성
    for i in range(3):
        snapshot = ObservationSnapshot(
            meta=Meta(
                timestamp=datetime.now(timezone.utc).isoformat(),
                session_id=session_id,
                run_id=f"test_run_{i+1}",
                mode="TEST"
            ),
            context=Context(
                source='market',
                stage='raw',
                symbol='005930',  # Samsung Electronics
                market='KOSPI'
            ),
            observation=Observation(
                inputs={'price': 75000 + i * 100, 'volume': 1000 + i * 100},
                computed={'change': i * 0.1},
                state={'status': 'active'}
            )
        )
        observer.on_snapshot(snapshot)
```

**복구 액션**:
```bash
# 테스트 스크립트 복사
cp backup/e531842/test_events_docker.py.utf8.py test/test_events_docker_restored.py

# 실행 테스트
python test/test_events_docker_restored.py
```

#### 4-2. test_integration.py (479 줄) - c0a7118

**위치**: `backup/c0a7118/test_integration.py`

**테스트 범위**:
- Observer 통합 테스트
- EventBus 기능
- .env 파일 로드
- 전체 시스템 흐름

#### 4-3. test_api_server.py (206 줄) - c0a7118

**위치**: `backup/c0a7118/test_api_server.py`

**테스트 범위**:
- API 엔드포인트 검증
- StatusTracker 기능
- Health/Ready 체크
- 상태 조회

---

## 📊 Track A/B 테스트 데이터

### 데이터 통계
```
Track A Test: 31 줄
Track B Test: 579 줄
```

### 데이터 위치
```bash
# 변환된 파일
backup/e531842/track_a_test.utf8.jsonl  (31 줄)
backup/e531842/track_b_test.utf8.jsonl  (579 줄)

# 원본 파일 (UTF-16)
backup/e531842/track_a_only_test_20260120_0400.jsonl
backup/e531842/track_b_test_20260120_0300.jsonl
```

### 데이터 포맷
```
각 줄: 로그 메시지 (로그 레벨, 시간, 모듈 정보 포함)
예: 2026-01-20 13:18:51 | INFO | observer.log_rotation | Log rotation triggered
```

### 복구 액션
```bash
# 1. 테스트 데이터 디렉토리 생성
mkdir -p test_data

# 2. 데이터 복사
cp backup/e531842/track_a_test.utf8.jsonl test_data/track_a_test.jsonl
cp backup/e531842/track_b_test.utf8.jsonl test_data/track_b_test.jsonl

# 3. 데이터 검증
wc -l test_data/track_*.jsonl
head -5 test_data/track_a_test.jsonl
```

---

## 🔧 복구 체크리스트

### Step 1: 파일 검증
- [ ] `api_server.py.utf8.py` (450줄, FastAPI 엔드포인트)
- [ ] `main.py.utf8.py` (109줄, Docker 엔트리)
- [ ] `event_bus.py.utf8.py` (194줄, 이벤트 라우팅)
- [ ] `logging_config.py.utf8.py` (로깅 설정)
- [ ] `log_rotation.py.utf8.py` (로그 로테이션)
- [ ] `test_events_docker.py.utf8.py` (테스트 이벤트)
- [ ] Track A/B 테스트 데이터 (31줄, 579줄)

### Step 2: 호환성 검증
```bash
# 현재 프로젝트의 파일과 비교
diff app/obs_deploy/app/src/observer/event_bus.py backup/e531842/event_bus.py.utf8.py

# import 경로 확인
grep -n "from observer" backup/e531842/api_server.py.utf8.py
grep -n "import" backup/e531842/api_server.py.utf8.py
```

### Step 3: 의존성 확인
```python
# 필요한 모듈들
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import psutil
from datetime import datetime, timezone
import asyncio
import uvicorn
```

### Step 4: 통합 및 테스트
```bash
# 1. 개별 파일 테스트
python -m py_compile backup/e531842/api_server.py.utf8.py

# 2. 통합 테스트
python test/test_integration.py

# 3. API 서버 테스트
python test/test_api_server.py
```

### Step 5: 커밋
```bash
git add app/obs_deploy/app/src/observer/api_server_restored.py
git add test_data/track_*.jsonl
git commit -m "feat: Restore FastAPI server and test data from backup

- Restore api_server.py with FastAPI endpoints (/health, /ready, /status, /metrics)
- Restore main.py with Docker integration
- Restore event_bus.py and logging configuration
- Recover Track A/B test data (31 + 579 lines)
- All files converted from UTF-16LE to UTF-8

Restored commit: e531842"
```

---

## ⚠️ 주의사항

1. **import 경로 확인**: 파일들이 `observer.*` 모듈을 가정하므로 경로 확인 필요
2. **의존성**: FastAPI, uvicorn, psutil, pydantic 필요
3. **환경 변수**: OBSERVER_DATA_DIR, OBSERVER_LOG_DIR 등 설정 필요
4. **인코딩**: 모든 파일이 UTF-16LE로 저장되어 있으므로 UTF-8로 변환 필요

---

## 📝 다음 단계

1. ✅ 파일 변환 (UTF-16 → UTF-8)
2. ⏳ 파일 검토 및 호환성 확인
3. ⏳ 현재 프로젝트와 병합
4. ⏳ 테스트 실행
5. ⏳ 커밋 및 푸시

---

*작성: 2026-01-20*
*상태: 복구 준비 완료*
