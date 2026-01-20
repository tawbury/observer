# Observer 코드베이스 분석 보고서

**분석 일자:** 2026-01-11  
**분석 대상:** QTS Observer 프로젝트  
**분석 목적:** 아키텍처 생성 및 독립 검토를 위한 사실 기반 코드 분석

---

## 1. 분석 범위 요약

### 1.1 실제 분석한 디렉터리 및 주요 파일 범위

**분석 대상 루트:**
```
app/qts_ops_deploy/
├── app/
│   ├── observer.py              # 실행 진입점
│   ├── paths.py                 # 경로 해석 모듈 (SSoT)
│   ├── deployment_config.json   # 배포 설정
│   └── src/
│       └── observer/            # Observer 코어 모듈
```

**분석한 핵심 파일:**
| 파일명 | 경로 | 분석 목적 |
|--------|------|-----------|
| `observer.py` | `app/` | 실행 진입점 |
| `paths.py` | `app/` | 경로 해석 SSoT |
| `observer.py` | `src/observer/` | Observer 클래스 정의 |
| `event_bus.py` | `src/observer/` | EventBus 및 Sink 구현 |
| `pattern_record.py` | `src/observer/` | PatternRecord 데이터 구조 |
| `snapshot.py` | `src/observer/` | ObservationSnapshot 정의 |
| `validation.py` | `src/observer/` | Validation Layer |
| `guard.py` | `src/observer/` | Guard Layer |
| `phase4_enricher.py` | `src/observer/` | Enrichment Layer |
| `schema_lite.py` | `src/observer/` | 스키마 버전 관리 |
| `log_rotation.py` | `src/observer/` | 로그 로테이션 |
| `performance_metrics.py` | `src/observer/` | 성능 메트릭 (유틸리티) |

**배포 관련 파일:**
| 파일명 | 분석 목적 |
|--------|-----------|
| `Dockerfile` | 컨테이너 빌드 구조 |
| `docker-compose.yml` | 서비스 정의 |
| `start_ops.sh` | 시작 스크립트 |
| `deployment_config.json` | 배포 설정 |

### 1.2 분석에서 제외한 영역

- `src/observer/analysis/` - Observer 코어 실행 경로에 직접 포함되지 않음
- `src/observer/inputs/` - 입력 어댑터 (코어 실행 흐름 외부)
- `src/backup/`, `src/maintenance/`, `src/retention/` - Observer 외부 모듈
- `src/decision_pipeline/` - Observer 범위 외부 (ETEDA 파이프라인)
- 테스트 파일 및 로그 파일
- 주석 처리된 코드 및 실험적 코드

---

## 2. 디렉터리 구조 개요

### 2.1 상위 디렉터리 구조 요약

```
app/qts_ops_deploy/
├── app/                          # 애플리케이션 루트
│   ├── observer.py               # 메인 실행 파일
│   ├── paths.py                  # 경로 해석 모듈
│   ├── deployment_config.json    # 배포 메타데이터
│   ├── config/                   # 설정 디렉터리 (비어있음)
│   ├── data/                     # 데이터 디렉터리 (비어있음)
│   └── src/                      # 소스 코드
│       ├── __init__.py
│       ├── observer/             # Observer 코어 모듈
│       ├── backup/               # 백업 모듈
│       ├── decision_pipeline/    # 의사결정 파이프라인
│       ├── maintenance/          # 유지보수 모듈
│       ├── retention/            # 보존 정책 모듈
│       ├── runtime/              # 런타임 모듈
│       ├── safety/               # 안전 모듈
│       └── shared/               # 공유 유틸리티
├── Dockerfile                    # Docker 빌드 정의
├── docker-compose.yml            # 서비스 구성
├── start_ops.sh                  # 시작 스크립트
├── requirements.txt              # Python 의존성
├── MANIFEST.txt                  # 패키지 목록
└── README.md                     # 사용 가이드
```

### 2.2 Observer 관련 핵심 경로 식별

**Observer 코어 모듈 (`src/observer/`):**
```
src/observer/
├── __init__.py
├── observer.py              # Observer 클래스 (오케스트레이터)
├── event_bus.py             # EventBus, SnapshotSink, JsonlFileSink
├── pattern_record.py        # PatternRecord 데이터 구조
├── snapshot.py              # ObservationSnapshot, Meta, Context, Observation
├── validation.py            # DefaultSnapshotValidator
├── guard.py                 # DefaultGuard
├── phase4_enricher.py       # DefaultRecordEnricher
├── schema_lite.py           # 스키마 버전 관리
├── log_rotation.py          # 시간 기반 로그 로테이션
├── performance_metrics.py   # 성능 메트릭 (유틸리티)
├── buffered_sink.py         # 버퍼링 Sink (확장)
├── buffer_flush.py          # 버퍼 플러시 로직
├── config_manager.py        # 설정 관리
├── deployment_paths.py      # 배포 경로 유틸리티
├── tick_events.py           # 틱 이벤트 처리
├── scalp_config.py          # 스켈프 설정 (확장)
├── usage_metrics.py         # 사용량 메트릭
└── analysis/                # 분석 모듈 (38 items, 코어 외부)
```

---

## 3. 실행 진입점 분석

### 3.1 프로그램이 시작되는 위치

**메인 진입점:** `app/observer.py`

```python
# app/observer.py (line 98-99)
if __name__ == "__main__":
    run_observer()
```

### 3.2 실행 흐름의 진입 지점과 종료 지점

**진입 흐름:**
1. `observer.py` 실행
2. `sys.path`에 `src/` 디렉터리 추가 (line 17-18)
3. `run_observer()` 함수 호출 (line 62)
4. 로깅 설정 (`_configure_logging()`)
5. Observer 클래스 동적 임포트 (`_import_observer_cls()`)
6. EventBus 및 JsonlFileSink 임포트 (`_import_event_bus_and_sink()`)
7. Observer 인스턴스 생성
8. 무한 루프 진입 (`while True: time.sleep(0.5)`)

**종료 흐름:**
- `KeyboardInterrupt` (Ctrl+C) 수신 시 종료 (line 90-91)
- 명시적인 `observer.stop()` 호출은 현재 코드에서 확인되지 않음

**코드 증거:**
```python
# app/observer.py (line 87-91)
try:
    while True:
        time.sleep(0.5)
except KeyboardInterrupt:
    log.info("Observer stopped")
```

### 3.3 Observer 클래스 임포트 경로

**동적 임포트 시도 순서:**
1. `ops.observer.observer.Observer`
2. `ops.observer.core.observer.Observer`

```python
# app/observer.py (line 24-36)
def _import_observer_cls():
    candidates = [
        ("ops.observer.observer", "Observer"),
        ("ops.observer.core.observer", "Observer"),
    ]
    # ...
```

**실제 사용되는 경로:** `src/observer/observer.py`의 `Observer` 클래스

---

## 4. Observer Core 구성 요소

### 4.1 주요 클래스 및 모듈

#### 4.1.1 Observer 클래스 (`src/observer/observer.py`)

**역할:** Observer-Core 오케스트레이터 (중앙 제어 클래스)

**생성자 파라미터:**
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `session_id` | `str` | Yes | 세션 식별자 |
| `mode` | `str` | Yes | 실행 모드 |
| `event_bus` | `EventBus` | Yes | 이벤트 버스 인스턴스 |
| `validator` | `SnapshotValidator` | No | 검증기 (기본: DefaultSnapshotValidator) |
| `guard` | `DefaultGuard` | No | 가드 (기본: DefaultGuard) |
| `enricher` | `RecordEnricher` | No | 인리처 (기본: DefaultRecordEnricher) |

**주요 메서드:**
| 메서드 | 역할 |
|--------|------|
| `start()` | `_running = True` 설정, 로그 출력 |
| `stop()` | `_running = False` 설정, 로그 출력 |
| `on_snapshot(snapshot)` | 스냅샷 처리 메인 로직 |

**내부 상태:**
- `_running: bool` - 실행 상태 플래그
- `_event_bus: EventBus` - 이벤트 버스 참조
- `_validator` - 검증기 인스턴스
- `_guard` - 가드 인스턴스
- `_enricher` - 인리처 인스턴스

#### 4.1.2 EventBus 클래스 (`src/observer/event_bus.py`)

**역할:** PatternRecord를 등록된 Sink들에게 전달

**생성자 파라미터:**
| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `sinks` | `Iterable[SnapshotSink]` | Sink 목록 |

**주요 메서드:**
| 메서드 | 역할 |
|--------|------|
| `dispatch(record)` | 모든 Sink에 PatternRecord 전달 |

**오류 처리:**
- 개별 Sink 오류는 로깅 후 계속 진행 (다른 Sink에 영향 없음)

#### 4.1.3 JsonlFileSink 클래스 (`src/observer/event_bus.py`)

**역할:** PatternRecord를 JSONL 파일로 저장

**생성자 파라미터:**
| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `filename` | `str` | `"observer.jsonl"` | 파일명 |
| `rotation_config` | `RotationConfig` | `None` | 로테이션 설정 |

**저장 규칙:**
- Append-only (기존 내용 수정 없음)
- 1 PatternRecord = 1 JSON line
- UTF-8 인코딩
- 경로는 `paths.py`의 `observer_asset_dir()`가 결정

#### 4.1.4 PatternRecord 클래스 (`src/observer/pattern_record.py`)

**역할:** Observer 최종 출력 데이터 자산 단위

**필드 구조:**
| 필드 | 타입 | 설명 |
|------|------|------|
| `snapshot` | `ObservationSnapshot` | 원본 스냅샷 (불변) |
| `regime_tags` | `Dict[str, Any]` | 시장 국면 태그 (현재 빈 dict) |
| `condition_tags` | `List[Dict[str, Any]]` | 조건 태그 (현재 빈 list) |
| `outcome_labels` | `Dict[str, Any]` | 결과 라벨 (현재 빈 dict) |
| `metadata` | `Dict[str, Any]` | 메타데이터 |

**특성:**
- `frozen=True` dataclass (불변)
- `to_dict()` 메서드로 직렬화

#### 4.1.5 ObservationSnapshot 클래스 (`src/observer/snapshot.py`)

**역할:** 최소 관측 단위

**구조:**
```
ObservationSnapshot
├── meta: Meta
│   ├── timestamp: str (ISO-8601)
│   ├── timestamp_ms: int (epoch ms)
│   ├── session_id: str
│   ├── run_id: str
│   ├── mode: str
│   ├── observer_version: str
│   └── (확장 필드: iteration_id, loop_interval_ms, latency_ms, tick_source, buffer_depth, flush_reason)
├── context: Context
│   ├── source: str
│   ├── stage: str
│   ├── symbol: Optional[str]
│   └── market: Optional[str]
└── observation: Observation
    ├── inputs: Dict[str, Any]
    ├── computed: Dict[str, Any]
    └── state: Dict[str, Any]
```

#### 4.1.6 DefaultSnapshotValidator 클래스 (`src/observer/validation.py`)

**역할:** 스냅샷 정합성 검사

**검증 범위:**
1. `snapshot.meta` 필수 키 존재 확인
2. `snapshot.context` 필수 키 존재 확인
3. `snapshot.observation.inputs/computed/state` 존재 및 dict 타입 확인
4. 숫자값 내 NaN/Inf 차단

**출력:** `ValidationResult(is_valid, severity, errors, details)`

#### 4.1.7 DefaultGuard 클래스 (`src/observer/guard.py`)

**역할:** 사전 차단 결정

**정책:**
1. `ValidationResult.is_valid == False` → BLOCK
2. `context.stage`가 비정상 → BLOCK

**출력:** `GuardDecision(allow, action, reason, details)`

#### 4.1.8 DefaultRecordEnricher 클래스 (`src/observer/phase4_enricher.py`)

**역할:** PatternRecord metadata 확장

**추가하는 네임스페이스:**
| 네임스페이스 | 내용 |
|--------------|------|
| `_schema` | 스키마 버전, producer, build_id 등 |
| `_quality` | flags, stats (품질 태그) |
| `_interpretation` | summary, hints (해석 보조) |

**금지 사항:**
- 실행/전략/리스크 로직 금지
- 매수/매도 판단 금지
- 결과 라벨링 금지

### 4.2 각 구성 요소의 실제 책임 (코드 기준)

| 구성 요소 | 실제 책임 | 하지 않는 것 |
|-----------|-----------|--------------|
| Observer | 스냅샷 수신, 처리 흐름 조율 | 스냅샷 생성, 전략 판단 |
| EventBus | PatternRecord를 Sink에 전달 | 데이터 변환, 외부 연결 |
| JsonlFileSink | JSONL 파일 저장 | 데이터 수정, 저장 정책 결정 |
| PatternRecord | 데이터 구조 정의 | 태그/라벨 계산 |
| Validator | 구조 정합성 검사 | 데이터 수정, 복구 |
| Guard | 차단 결정 | 전략 판단, 리스크 평가 |
| Enricher | metadata 네임스페이스 추가 | 스냅샷 내용 변경 |

---

## 5. 데이터 흐름 분석

### 5.1 Snapshot 생성 또는 수신 위치

**코드 증거:**
- Observer 클래스는 스냅샷을 **생성하지 않음**
- `on_snapshot(snapshot: ObservationSnapshot)` 메서드로 외부에서 스냅샷을 **수신**

```python
# src/observer/observer.py (line 102)
def on_snapshot(self, snapshot: ObservationSnapshot) -> None:
```

**스냅샷 생성 책임:**
- Observer 외부 (QTS 모듈, 브로커 어댑터, 시뮬레이터 등)
- `snapshot.py`의 `build_snapshot()` 팩토리 함수 제공 (외부 사용용)

### 5.2 PatternRecord 생성 흐름

**생성 위치:** `src/observer/observer.py` line 167-193

**생성 시점:** Validation 및 Guard 통과 후

**생성 코드:**
```python
record = PatternRecord(
    snapshot=snapshot,
    regime_tags={},
    condition_tags=[],
    outcome_labels={},
    metadata={
        "schema_version": "v1.0.0",
        "dataset_version": "v1.0.0",
        "build_id": "observer_core_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "session_id": self.session_id,
        "mode": self.mode,
        "quality_flags": [],
        "validation": {"severity": v.severity},
        "guard": {"action": g.action, "reason": g.reason},
    },
)
```

**생성 후 처리:**
1. Enricher를 통한 metadata 확장
2. EventBus로 dispatch

### 5.3 Sink로 기록되는 과정

**전체 데이터 흐름:**
```
[외부] ObservationSnapshot 생성
    ↓
Observer.on_snapshot(snapshot) 호출
    ↓
[Validation] DefaultSnapshotValidator.validate()
    ↓ (is_valid == True)
[Guard] DefaultGuard.decide()
    ↓ (allow == True)
[PatternRecord 생성]
    ↓
[Enrichment] DefaultRecordEnricher.enrich()
    ↓
[Dispatch] EventBus.dispatch(record)
    ↓
[Sink] JsonlFileSink.publish(record)
    ↓
[파일 저장] observer_asset_dir() / filename
```

**차단 경로:**
- Validation 실패 → 로그 후 return (기록 안 함)
- Guard 차단 → 로그 후 return (기록 안 함)

**저장 경로 결정:**
```python
# src/observer/event_bus.py (line 109)
self.base_dir = observer_asset_dir()
```

```python
# paths.py (line 153-165)
def observer_asset_dir() -> Path:
    path = config_dir() / "observer"
    path.mkdir(parents=True, exist_ok=True)
    return path
```

**Standalone 모드 경로:**
- `QTS_OBSERVER_STANDALONE=1` 환경 변수 설정 시
- `paths.py`가 `Path(__file__).resolve().parent`를 프로젝트 루트로 사용

---

## 6. 런타임 동작 특성

### 6.1 Long-running 여부

**결론:** Long-running 프로세스로 설계됨

**코드 증거:**
```python
# app/observer.py (line 87-91)
try:
    while True:
        time.sleep(0.5)
except KeyboardInterrupt:
    log.info("Observer stopped")
```

- 무한 루프 (`while True`)
- 0.5초 간격 sleep (busy-loop 방지)
- `KeyboardInterrupt`로만 종료

### 6.2 루프 또는 이벤트 기반 동작 여부

**현재 구현:** 대기 루프 + 외부 호출 기반

**관찰 사항:**
- 메인 루프는 단순 대기 (`time.sleep(0.5)`)
- 실제 스냅샷 처리는 외부에서 `on_snapshot()` 호출 시 발생
- 현재 코드에서 `on_snapshot()` 호출 지점이 없음 (외부 연동 필요)

**불명확한 점:**
- 현재 `run_observer()` 함수에서 `observer.start()`가 호출되지 않음
- `on_snapshot()`을 호출하는 외부 트리거가 코드에 존재하지 않음

### 6.3 중단 및 종료 처리 방식

**종료 트리거:**
- `KeyboardInterrupt` (Ctrl+C)

**종료 시 동작:**
- 로그 출력: `"Observer stopped"`
- 명시적인 리소스 정리 코드 없음
- `observer.stop()` 호출 없음 (현재 코드 기준)

**Graceful Shutdown:**
- 현재 구현에서 명시적인 graceful shutdown 로직 없음
- 파일 Sink는 각 write 후 즉시 flush (데이터 손실 최소화)

---

## 7. 배포 및 운영 관련 코드 단서

### 7.1 배포 자동화와 직접적으로 연결된 코드 구조

#### 7.1.1 Dockerfile 분석

**파일:** `app/qts_ops_deploy/Dockerfile`

**주요 구성:**
| 항목 | 값 |
|------|-----|
| 베이스 이미지 | `python:3.11-slim` |
| 작업 디렉터리 | `/app` |
| 복사 대상 | `observer.py`, `paths.py`, `src/` |
| 생성 디렉터리 | `/app/data/observer`, `/app/logs`, `/app/config` |
| 실행 사용자 | `qts` (non-root) |
| 헬스체크 | `python -c "import sys; sys.exit(0)"` |
| 노출 포트 | 8000 |
| 실행 명령 | `python observer.py` |

**환경 변수:**
```dockerfile
ENV QTS_OBSERVER_STANDALONE=1
ENV PYTHONPATH=/app/src:/app
ENV OBSERVER_DATA_DIR=/app/data/observer
ENV OBSERVER_LOG_DIR=/app/logs
```

#### 7.1.2 docker-compose.yml 분석

**서비스 정의:**
| 항목 | 값 |
|------|-----|
| 서비스명 | `qts-observer` |
| 컨테이너명 | `qts-observer` |
| 재시작 정책 | `unless-stopped` |
| 포트 매핑 | `8000:8000` |
| 네트워크 | `qts-network` (bridge) |

**볼륨 마운트:**
| 호스트 | 컨테이너 |
|--------|----------|
| `./data` | `/app/data/observer` |
| `./logs` | `/app/logs` |
| `./config` | `/app/config` |

**리소스 제한:**
| 항목 | 제한 | 예약 |
|------|------|------|
| CPU | 1.0 | 0.5 |
| Memory | 512M | 256M |

#### 7.1.3 deployment_config.json 분석

```json
{
    "deployment": {
        "version": "1.0.0",
        "created": "2026-01-11T08:08:07+09:00",
        "structure": "/app",
        "mode": "standalone"
    },
    "paths": {
        "data_dir": "/app/data/observer",
        "log_dir": "/app/logs",
        "config_dir": "/app/config"
    },
    "environment": {
        "QTS_OBSERVER_STANDALONE": "1",
        "PYTHONPATH": "/app/src:/app",
        "OBSERVER_DATA_DIR": "/app/data/observer",
        "OBSERVER_LOG_DIR": "/app/logs"
    }
}
```

### 7.2 실행 환경에 의존하는 요소

#### 7.2.1 환경 변수 의존성

| 환경 변수 | 용도 | 필수 |
|-----------|------|------|
| `QTS_OBSERVER_STANDALONE` | Standalone 모드 활성화 | Yes (배포 시) |
| `PYTHONPATH` | Python 모듈 경로 | Yes |
| `OBSERVER_DATA_DIR` | 데이터 디렉터리 | No (참조용) |
| `OBSERVER_LOG_DIR` | 로그 디렉터리 | No (참조용) |

#### 7.2.2 경로 해석 의존성

**paths.py의 프로젝트 루트 결정 로직:**
```python
# paths.py (line 48-63)
# 1. QTS_OBSERVER_STANDALONE=1 → Path(__file__).resolve().parent
# 2. .git 디렉터리 존재
# 3. pyproject.toml 존재
# 4. src/ 및 tests/ 디렉터리 존재
```

**Standalone 모드:**
- `QTS_OBSERVER_STANDALONE=1` 설정 시 `paths.py` 위치가 프로젝트 루트
- 배포 환경에서 필수

#### 7.2.3 파일 시스템 의존성

**필수 디렉터리:**
- `/app/data/observer` - 데이터 저장
- `/app/logs` - 로그 저장
- `/app/config` - 설정 파일

**자동 생성:**
- `observer_asset_dir()` 호출 시 `config/observer/` 디렉터리 자동 생성

---

## 8. 불명확하거나 확인 불가한 영역

### 8.1 코드만으로 판단하기 어려운 부분

#### 8.1.1 스냅샷 트리거 메커니즘

**불명확한 점:**
- `on_snapshot()` 메서드가 존재하지만, 이를 호출하는 코드가 분석 범위 내에 없음
- 외부 시스템이 어떻게 스냅샷을 전달하는지 불명확

**코드 증거:**
```python
# app/observer.py (line 87-91)
# 메인 루프에서 on_snapshot() 호출 없음
try:
    while True:
        time.sleep(0.5)
except KeyboardInterrupt:
    log.info("Observer stopped")
```

#### 8.1.2 Observer 시작/종료 생명주기

**불명확한 점:**
- `run_observer()`에서 `observer.start()` 호출이 없음
- `observer.stop()` 호출이 종료 시 없음
- `_running` 플래그가 실제로 어떻게 사용되는지 불명확

**코드 증거:**
```python
# app/observer.py (line 76-84)
observer = ObserverCls(...)
log.info("Observer started | session_id=%s", session_id)
# observer.start() 호출 없음
```

#### 8.1.3 포트 8000 사용 목적

**불명확한 점:**
- Dockerfile에서 `EXPOSE 8000` 선언
- docker-compose에서 `8000:8000` 포트 매핑
- 실제 포트 8000을 사용하는 코드가 분석 범위 내에 없음

**추정:**
- 향후 웹 인터페이스 또는 API 엔드포인트용으로 예약된 것으로 보임
- 현재는 미구현 상태

### 8.2 추가 정보가 필요할 수 있는 지점

| 영역 | 필요한 정보 |
|------|-------------|
| 스냅샷 트리거 | 외부 시스템이 `on_snapshot()`을 호출하는 방식 |
| 생명주기 관리 | `start()`/`stop()` 호출 시점 및 책임 |
| 포트 8000 | 실제 사용 계획 또는 구현 예정 기능 |
| 성능 메트릭 접근 | `PerformanceMetrics` 데이터를 외부에서 조회하는 방법 |
| 로그 로테이션 활성화 | `RotationConfig` 설정 방법 및 기본값 |

---

## 9. 분석 결론

### 9.1 Observer 코어 구조 요약

Observer는 다음과 같은 계층 구조로 구성됨:

```
[실행 진입점] app/observer.py
    ↓
[오케스트레이터] Observer 클래스
    ↓
[처리 파이프라인]
    Validation → Guard → PatternRecord 생성 → Enrichment
    ↓
[전달 계층] EventBus
    ↓
[저장 계층] JsonlFileSink
    ↓
[파일 시스템] observer_asset_dir() / *.jsonl
```

### 9.2 코드에서 확인된 설계 원칙

1. **판단 금지:** Observer는 전략/매매/리스크 판단을 하지 않음
2. **불변성:** PatternRecord는 frozen dataclass
3. **Append-only:** 파일 저장은 추가만 가능
4. **오류 격리:** Sink 오류가 전체 파이프라인에 영향 없음
5. **경로 SSoT:** `paths.py`가 모든 경로의 단일 진실 소스

### 9.3 배포 구조 요약

- Docker 기반 컨테이너화
- Standalone 모드 지원 (`QTS_OBSERVER_STANDALONE=1`)
- 볼륨 마운트를 통한 데이터 지속성
- Non-root 사용자 실행 (보안)
- 리소스 제한 설정 (CPU/Memory)

---

**분석 완료**

이 보고서는 코드 기반 사실만을 기술하며, 설계 제안이나 개선 사항을 포함하지 않습니다.
