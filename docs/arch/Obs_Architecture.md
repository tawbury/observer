# Observer 아키텍처

**버전:** v1.0.0  
**상태:** 최종 앵커 아키텍처 (Anchor Architecture)  
**작성일:** 2026-01-11  
**범위:** Observer 독립 실행 서비스의 프로그램, 배포, 운영 아키텍처

---

## 0. 문서 상태 및 목적

### 0.1 문서의 역할

본 문서는 **QTS Observer 시스템의 최종 앵커 아키텍처 문서(Single Source of Truth)**로서 다음을 정의한다:

- **프로그램 아키텍처**: 코어 구성 요소, 실행 흐름, 데이터 흐름
- **배포 아키텍처**: 컨테이너화, 환경 설정, 경로 구조
- **운영 아키텍처**: 런타임 모델, 모니터링, 복구 시나리오

### 0.2 기반 문서

본 아키텍처는 다음을 기반으로 작성되었다:

1. **참조 아키텍처**: `09_Ops_Automation_Architecture.md` (Phase 15 검증 완료)
2. **코드 분석 보고서**: `Observer_Code_Analysis_Report.md` (실제 코드베이스 분석)
3. **실제 코드베이스**: `app/qts_ops_deploy/` 디렉터리 구조

### 0.3 아키텍처 원칙

- **코드 우선**: 코드 현실이 문서보다 우선한다
- **실행 신뢰성**: 이론적 우아함보다 실행 안정성이 중요하다
- **독립 실행**: Observer는 독립 실행 가능한 서비스다
- **판단 금지**: Observer는 전략/매매/리스크 판단을 하지 않는다

---

## 1. Observer 역할 및 책임

### 1.1 목적

Observer는 **판단 없는 관측 및 기록 시스템**이다.

**핵심 역할:**
- 시장 및 시스템 이벤트 관측
- 관측 상태를 스냅샷으로 기록
- 해석이나 의사결정 없이 데이터 저장

### 1.2 위치 선언

Observer는 **QTS 호환 독립 데이터 생산자**로 설계되었다:
- Standalone 또는 QTS 통합 모드로 실행 가능
- QTS 전략, 실행, 리스크 엔진에 의존하지 않음
- 실행 모드와 무관하게 데이터 호환성 유지

### 1.3 우선순위

Observer는 범용 구조를 유지하지만, **스켈프 전략 운영을 주요 설계 우선순위**로 한다:
- 고빈도 의사결정 데이터 수집
- 빈번한 판단, 차단, 미실행 상태 기록
- 스켈프 트레이딩 의사결정의 사후 재구성 가능성

### 1.4 책임 경계

**Observer가 담당하는 것:**
- ObservationSnapshot 구조 수신
- PatternRecord 래퍼 생성
- 빈 태그/라벨 슬롯 유지
- EventBus로 레코드 전달
- 데이터 계약 준수 보장

**Observer가 절대 하지 않는 것:**
- 전략 판단
- 조건 평가
- 매매 의사결정
- 포지션 상태 관리
- 리스크 승인
- 학습 라벨 생성
- 레짐 분류 생성
- 조건 태그 생성
- 결과 라벨 생성
- 입력 데이터 수정/보정
- 데이터 정규화/변환
- 지표 계산
- ETEDA 파이프라인 개입

---

## 2. QTS 아키텍처 내 위치

### 2.1 ETEDA 파이프라인과의 관계

Observer는 ETEDA 파이프라인 **외부 및 이전**에 위치한다:

```
[실세계 데이터]
    ↓
[Observer] ← Phase 15 위치
    ↓
[Extract]
    ↓
[Transform]
    ↓
[Evaluate]
    ↓
[Decide]
    ↓
[Act]
```

**Observer는 아니다:**
- 전략 시스템의 일부
- 엔진 파이프라인의 일부
- 브로커 실행의 일부

**Observer는:**
- 실세계 데이터를 관측 가능하게 만드는 사전 단계 장치

### 2.2 Ops 레이어와의 관계

Observer는 Ops 레이어 내에서 **데이터 수집 인프라 구성 요소**로 위치한다.

**Observer가 소유하지 않는 것:**
- 스케줄링 또는 트리거링
- 실행 흐름 제어
- 자동화 정책 관리

### 2.3 데이터 흐름 위치

Observer는 유입 경계에 위치한다:

```
외부/QTS 이벤트
 → ObservationSnapshot
 → Observer
 → PatternRecord
 → EventBus
 → Sink
 → 데이터 자산 (jsonl)
```

각 단계는 격리되어 있으며 다른 단계의 내부 상태를 참조하지 않는다.

---

## 3. 프로그램 아키텍처

### 3.1 코어 구성 요소

#### 3.1.1 Observer 컴포넌트

**파일 위치:** `src/observer/observer.py`

**책임:**
- ObservationSnapshot 수신
- PatternRecord 구조 생성
- 빈 태그/라벨 슬롯 유지
- EventBus로 전달

**경계:**
- 레짐 분류 생성 금지
- 조건 판단 생성 금지
- 결과 라벨 생성 금지
- 스냅샷 내용 수정 금지

**구현 상태:** 구현 완료

**주요 인터페이스:**
```python
class Observer:
    def __init__(
        self,
        *,
        session_id: str,
        mode: str,
        event_bus: EventBus,
        validator: SnapshotValidator | None = None,
        guard: DefaultGuard | None = None,
        enricher: RecordEnricher | None = None,
    ) -> None
    
    def start(self) -> None
    def stop(self) -> None
    def on_snapshot(self, snapshot: ObservationSnapshot) -> None
```

#### 3.1.2 EventBus 컴포넌트

**파일 위치:** `src/observer/event_bus.py`

**책임:**
- PatternRecord를 등록된 Sink들로 팬아웃
- 개별 Sink 실패를 전체 흐름에서 격리

**경계:**
- 외부 이벤트 수신 금지
- 브로커 API 연결 금지
- 데이터 정규화 금지
- 재시도 정책 결정 금지

**구현 상태:** 구현 완료

**주요 인터페이스:**
```python
class EventBus:
    def __init__(self, sinks: Iterable[SnapshotSink]) -> None
    def dispatch(self, record: PatternRecord) -> None
```

#### 3.1.3 Sink 컴포넌트

**파일 위치:** `src/observer/event_bus.py`

**책임:**
- PatternRecord를 영구 저장소에 기록
- Append-only 기록 규칙 준수
- 경로 및 포맷 규칙 준수

**경계:**
- PatternRecord 내용 수정 금지
- 저장 정책 결정 금지 (계약에서 정의)

**구현 상태:** 구현 완료 (JsonlFileSink)

**주요 인터페이스:**
```python
class SnapshotSink(ABC):
    @abstractmethod
    def publish(self, record: PatternRecord) -> None

class JsonlFileSink(SnapshotSink):
    def __init__(
        self,
        filename: str = "observer.jsonl",
        *,
        rotation_config: Optional[RotationConfig] = None,
    ) -> None
    
    def publish(self, record: PatternRecord) -> None
```

#### 3.1.4 PatternRecord (데이터 단위)

**파일 위치:** `src/observer/pattern_record.py`

**책임:**
- ObservationSnapshot을 수정 없이 래핑
- 향후 태깅/라벨링을 위한 슬롯 제공
- 추적을 위한 메타데이터 유지

**경계:**
- 태그 또는 라벨 계산 금지
- 스냅샷 필드 수정 금지

**구현 상태:** 구현 완료

**데이터 구조:**
```python
@dataclass(frozen=True)
class PatternRecord:
    snapshot: ObservationSnapshot
    regime_tags: Dict[str, Any]          # 현재 빈 dict
    condition_tags: List[Dict[str, Any]] # 현재 빈 list
    outcome_labels: Dict[str, Any]       # 현재 빈 dict
    metadata: Dict[str, Any]             # 메타데이터
```

#### 3.1.5 Validation Layer

**파일 위치:** `src/observer/validation.py`

**책임:**
- 스냅샷 구조 정합성 검사
- 필수 필드 존재 확인
- NaN/Inf 차단

**경계:**
- 데이터 수정 금지
- 복구 시도 금지

**구현 상태:** 구현 완료 (DefaultSnapshotValidator)

#### 3.1.6 Guard Layer

**파일 위치:** `src/observer/guard.py`

**책임:**
- Validation 결과 기반 차단 결정
- 안전 검사 적용

**경계:**
- 전략 판단 금지
- 리스크 평가 금지

**구현 상태:** 구현 완료 (DefaultGuard)

#### 3.1.7 Enrichment Layer

**파일 위치:** `src/observer/phase4_enricher.py`

**책임:**
- PatternRecord metadata 네임스페이스 추가
- 품질 태깅 (중립 지표만)
- 해석 메타데이터 (요약 힌트만)

**경계:**
- 실행/전략/리스크 로직 금지
- 매수/매도 판단 금지
- 결과 라벨링 금지

**구현 상태:** 구현 완료 (DefaultRecordEnricher)

**추가 네임스페이스:**
- `_schema`: 스키마 버전, producer, build_id
- `_quality`: flags, stats (품질 지표)
- `_interpretation`: summary, hints (해석 보조)

### 3.2 스냅샷 아키텍처

#### 3.2.1 스냅샷 정의

ObservationSnapshot은 **최소 관측 단위**로, 특정 시점의 시장 또는 시스템 상태를 판단 없이 기록한다.

**구조:**
```
ObservationSnapshot
 ├─ Meta (timestamp, session_id, run_id, mode, observer_version)
 ├─ Context (source, stage, symbol, market)
 ├─ Observation (inputs, computed, state)
 └─ Trace (schema_version, config_snapshot, notes)
```

**파일 위치:** `src/observer/snapshot.py`

#### 3.2.2 스냅샷 생성 책임

**Observer는 스냅샷을 생성하지 않는다.**

스냅샷 생성은 Observer-Core 외부에서 수행된다:
- QTS 내부 모듈
- 브로커 어댑터
- 시뮬레이터
- 외부 수집 시스템

Observer는 수신 시 스냅샷이 이미 계약 구조를 만족한다고 가정한다.

#### 3.2.3 트리거 모델

**현재 구현된 것:**
- 주기적 스냅샷: 고정 간격 (기본 1.0초)
- 이벤트 기반 스냅샷: 시장 데이터 이벤트, 틱 이벤트

**명시적으로 구현되지 않은 것:**
- 시장 조건 기반 적응형 빈도
- 고빈도 모드 전환 (예: 0.5초 간격)
- SCALP 이벤트 트리거 빈도 변경
- 조건부 스냅샷 주기 조정

#### 3.2.4 빈도 동작

**고정 동작:**
- 기본: 1.0초 간격
- `interval_sec` 파라미터로 설정 가능
- 현재 구현에서 조건부 빈도 변경 없음

**지원하지 않는 동작:**
- 동적 간격 조정
- 이벤트 기반 빈도 전환
- 전략 모드 의존 스냅샷 비율

#### 3.2.5 저장 및 결정성

**저장 메커니즘:** 파일 기반 (JSONL)

**저장 위치:**
```
<PROJECT_ROOT>/config/observer/
```
- 경로는 실행 위치 독립적
- `paths.py`가 단일 진실 소스(SSoT)로 결정

**저장 규칙:**
- Append-only (덮어쓰기 없음)
- 1줄 = 1 PatternRecord
- UTF-8 인코딩
- 병렬 쓰기에 대한 순서 보장 없음

**결정성:** 명시적이고 결정적
- 스냅샷 동작은 코드에 명시적
- 암묵적 또는 추론된 로직 없음
- 모든 트리거 조건이 문서화됨

### 3.3 실행 및 제어 흐름

#### 3.3.1 Observer 실행 방식

**생명주기:**
1. `start()` - 관측 시작
2. `on_snapshot(snapshot)` - 유입 스냅샷 처리
3. Validation → Guard → PatternRecord 생성 → Enrichment → EventBus 전달
4. `stop()` - 관측 종료

#### 3.3.2 스냅샷 처리 흐름

각 스냅샷에 대해:
1. **Validation** - 계약 준수 확인
2. **Guard** - 안전 검사 적용
3. **PatternRecord 조립** - 빈 슬롯과 함께 스냅샷 래핑
4. **Enrichment** - 메타데이터 네임스페이스 추가 (Phase 4)
5. **Dispatch** - EventBus로 전송

#### 3.3.3 Observer가 절대 트리거하지 않는 것

Observer는 다음을 트리거하지 않는다:
- 매매 실행
- 전략 평가
- 리스크 평가
- 포지션 관리
- 외부 시스템 호출
- ETEDA 파이프라인 단계

#### 3.3.4 런타임 모드

**지원 모드:**
- DEV
- PROD

**모드 목적:**
- 로그 레벨 제어
- metadata.mode 값 기록
- 운영/테스트 데이터 구분

**모드가 변경하지 않는 것:**
- 데이터 구조
- 저장 경로
- 파일 포맷
- 계약 규칙

### 3.4 데이터 흐름 아키텍처

#### 3.4.1 전체 데이터 흐름

```
[외부 시스템]
    ↓
ObservationSnapshot 생성
    ↓
Observer.on_snapshot() 호출
    ↓
┌─────────────────────────────┐
│ Validation Layer            │
│ - 구조 검사                 │
│ - 필수 필드 확인            │
│ - NaN/Inf 차단              │
└─────────────────────────────┘
    ↓ (is_valid == True)
┌─────────────────────────────┐
│ Guard Layer                 │
│ - 차단 결정                 │
│ - 안전 검사                 │
└─────────────────────────────┘
    ↓ (allow == True)
┌─────────────────────────────┐
│ PatternRecord 생성          │
│ - 스냅샷 래핑               │
│ - 빈 슬롯 유지              │
│ - 기본 메타데이터 추가      │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│ Enrichment Layer            │
│ - _schema 네임스페이스      │
│ - _quality 네임스페이스     │
│ - _interpretation 네임스페이스│
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│ EventBus                    │
│ - Sink 팬아웃               │
│ - 오류 격리                 │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│ JsonlFileSink               │
│ - JSONL 파일 기록           │
│ - Append-only               │
└─────────────────────────────┘
    ↓
[파일 시스템]
config/observer/*.jsonl
```

#### 3.4.2 차단 경로

**Validation 실패:**
- 스냅샷 차단, 로깅, 기록하지 않음

**Guard 차단:**
- 스냅샷 차단, 로깅, 기록하지 않음

**Sink 실패:**
- 로깅, 다른 Sink는 계속 진행

**스키마 위반:**
- Validation에서 스냅샷 거부

### 3.5 안전, 검증 및 가드레일

#### 3.5.1 기존 안전장치

**Validation Layer (Phase 3):**
- 스냅샷 meta 필수 필드 확인
- 스냅샷 context 필수 필드 확인
- Observation 구조 검증
- 숫자값의 NaN/Inf 차단

**Guard Layer (Phase 3):**
- Validation 결과 기반 스냅샷 차단
- 안전 결정 로깅
- 허용/차단 결정

**Enrichment Layer (Phase 4):**
- 품질 태깅 (중립 지표만)
- 해석 메타데이터 (요약 힌트)
- 스키마 버전 메타데이터

#### 3.5.2 의도적으로 부재한 것

Observer는 다음을 구현하지 않는다:
- 자동 복구
- 재시도 정책
- 데이터 보정
- 값 대체
- 차단 이상의 누락 데이터 처리

#### 3.5.3 오류 처리 정책

**Observer 내부 오류:** 실행 중단

**Sink 오류:** 로그 후 계속 (실패 격리)

**데이터 오류:** 스냅샷 무시 (선택적 차단)

### 3.6 설정 및 스키마 의존성

#### 3.6.1 설정 입력

Observer가 수신하는 설정:
- Session ID
- 런타임 모드 (DEV/PROD)
- EventBus sink 설정
- Validator/Guard/Enricher 인스턴스 (선택)

Observer가 하지 않는 것:
- 전략 설정 로드
- 매매 파라미터 접근
- 시스템 전역 설정 수정

#### 3.6.2 스키마 강제

Observer는 Schema Engine 정의 필드 내에서 동작:
- 스냅샷 구조는 스키마 계약을 따름
- 임의 필드 생성 금지
- 메타데이터에 스키마 버전 추적

#### 3.6.3 실패 동작

**Validation 실패:** 스냅샷 차단, 로깅, 기록 안 함

**Guard 실패:** 스냅샷 차단, 로깅, 기록 안 함

**Sink 실패:** 로깅, 다른 Sink는 계속

**스키마 위반:** Validation에서 스냅샷 거부

---

## 4. 배포 아키텍처

### 4.1 실행 진입점

#### 4.1.1 메인 진입점

**파일:** `app/observer.py`

**실행 흐름:**
```python
if __name__ == "__main__":
    run_observer()
```

**초기화 순서:**
1. 로깅 설정
2. Observer 클래스 동적 임포트
3. EventBus 및 JsonlFileSink 임포트
4. Observer 인스턴스 생성
5. 무한 대기 루프 진입

#### 4.1.2 모듈 임포트 전략

**동적 임포트 시도 순서:**
1. `ops.observer.observer.Observer`
2. `ops.observer.core.observer.Observer`

**목적:** 다양한 디렉터리 구조에서 유연한 실행

### 4.2 컨테이너화 구조

#### 4.2.1 Dockerfile 아키텍처

**파일:** `app/qts_ops_deploy/Dockerfile`

**계층 구조:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app

# 필수 파일 복사
COPY observer.py /app/
COPY paths.py /app/
COPY src/ /app/src/

# 디렉터리 생성
RUN mkdir -p /app/data/observer \
    && mkdir -p /app/logs \
    && mkdir -p /app/config

# 환경 변수
ENV QTS_OBSERVER_STANDALONE=1
ENV PYTHONPATH=/app/src:/app

# 보안: non-root 사용자
RUN groupadd -r qts && useradd -r -g qts qts
RUN chown -R qts:qts /app
USER qts

# 실행
CMD ["python", "observer.py"]
```

**주요 특징:**
- 경량 베이스 이미지 (python:3.11-slim)
- Non-root 사용자 실행 (보안)
- Standalone 모드 환경 변수 설정
- 필수 디렉터리 사전 생성

#### 4.2.2 docker-compose 구성

**파일:** `app/qts_ops_deploy/docker-compose.yml`

**서비스 정의:**
```yaml
services:
  qts-observer:
    build: .
    container_name: qts-observer
    restart: unless-stopped
    environment:
      - QTS_OBSERVER_STANDALONE=1
      - PYTHONPATH=/app/src:/app
    volumes:
      - ./data:/app/data/observer
      - ./logs:/app/logs
      - ./config:/app/config
    ports:
      - "8000:8000"
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
```

**주요 특징:**
- 자동 재시작 정책
- 볼륨 마운트를 통한 데이터 지속성
- 리소스 제한 (CPU 1.0, Memory 512M)
- 포트 8000 노출 (향후 확장용)

### 4.3 경로 아키텍처

#### 4.3.1 경로 해석 SSoT

**파일:** `app/paths.py`

**역할:** 모든 파일 시스템 경로의 단일 진실 소스

**프로젝트 루트 결정 로직:**
```python
def _resolve_project_root(start: Optional[Path] = None) -> Path:
    # 1. Observer standalone 모드 (강제)
    if os.environ.get("QTS_OBSERVER_STANDALONE") == "1":
        return Path(__file__).resolve().parent
    
    # 2. 일반 QTS 프로젝트 해석
    # - .git 디렉터리 존재
    # - pyproject.toml 존재
    # - src/ 및 tests/ 디렉터리 존재
```

**Observer 자산 디렉터리:**
```python
def observer_asset_dir() -> Path:
    path = config_dir() / "observer"
    path.mkdir(parents=True, exist_ok=True)
    return path
```

#### 4.3.2 Standalone 모드 경로

**환경 변수:** `QTS_OBSERVER_STANDALONE=1`

**효과:**
- `paths.py` 위치를 프로젝트 루트로 사용
- 배포 환경에서 필수
- 실행 위치 독립적 동작 보장

**경로 매핑:**
| 논리 경로 | Standalone 물리 경로 |
|-----------|---------------------|
| `project_root()` | `/app` |
| `config_dir()` | `/app/config` |
| `observer_asset_dir()` | `/app/config/observer` |
| `data_dir()` | `/app/data` |

#### 4.3.3 디렉터리 구조

**컨테이너 내부 구조:**
```
/app/
├── observer.py           # 실행 진입점
├── paths.py              # 경로 SSoT
├── src/
│   └── observer/         # Observer 코어 모듈
├── config/
│   └── observer/         # Observer 자산 (JSONL)
├── data/
│   └── observer/         # 임시 데이터 (deprecated)
└── logs/                 # 로그 파일
```

**볼륨 마운트:**
- `./data` → `/app/data/observer` (데이터 지속성)
- `./logs` → `/app/logs` (로그 지속성)
- `./config` → `/app/config` (설정 지속성)

### 4.4 환경 설정

#### 4.4.1 필수 환경 변수

| 환경 변수 | 값 | 목적 |
|-----------|-----|------|
| `QTS_OBSERVER_STANDALONE` | `1` | Standalone 모드 활성화 |
| `PYTHONPATH` | `/app/src:/app` | Python 모듈 경로 |

#### 4.4.2 선택 환경 변수

| 환경 변수 | 기본값 | 목적 |
|-----------|--------|------|
| `OBSERVER_DATA_DIR` | `/app/data/observer` | 데이터 디렉터리 (참조용) |
| `OBSERVER_LOG_DIR` | `/app/logs` | 로그 디렉터리 (참조용) |

#### 4.4.3 배포 설정 파일

**파일:** `app/deployment_config.json`

**내용:**
```json
{
    "deployment": {
        "version": "1.0.0",
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
        "PYTHONPATH": "/app/src:/app"
    }
}
```

**목적:** 배포 메타데이터 및 설정 문서화

### 4.5 배포 흐름

#### 4.5.1 개념적 배포 흐름

```
[소스 코드]
    ↓
[Docker Build]
    ↓
[컨테이너 이미지]
    ↓
[컨테이너 실행]
    ↓
[Observer 프로세스]
```

#### 4.5.2 도구 독립성

배포 아키텍처는 특정 도구에 종속되지 않는다:
- Docker는 교체 가능 (Podman, containerd 등)
- docker-compose는 교체 가능 (Kubernetes, Nomad 등)
- 핵심은 환경 변수 및 경로 구조 준수

#### 4.5.3 책임 분리

| 계층 | 책임 |
|------|------|
| 소스 코드 | 프로그램 로직 |
| Dockerfile | 컨테이너 이미지 빌드 |
| docker-compose | 서비스 오케스트레이션 |
| 환경 변수 | 런타임 설정 |
| 볼륨 | 데이터 지속성 |

---

## 5. 운영 아키텍처

### 5.1 런타임 실행 모델

#### 5.1.1 프로세스 특성

**실행 모델:** Long-running daemon-like 프로세스

**코드 증거:**
```python
# app/observer.py
try:
    while True:
        time.sleep(0.5)
except KeyboardInterrupt:
    log.info("Observer stopped")
```

**특징:**
- 무한 루프 기반 대기
- 0.5초 간격 sleep (busy-loop 방지)
- 외부 호출 기반 스냅샷 처리

#### 5.1.2 생명주기

**시작:**
1. 컨테이너 시작
2. `python observer.py` 실행
3. Observer 인스턴스 생성
4. 대기 루프 진입

**실행:**
- 외부 시스템이 `on_snapshot()` 호출
- 스냅샷 처리 파이프라인 실행
- JSONL 파일에 기록

**종료:**
- `KeyboardInterrupt` (Ctrl+C)
- 컨테이너 중지 신호
- 로그 출력 후 종료

#### 5.1.3 재시작 정책

**docker-compose 설정:**
```yaml
restart: unless-stopped
```

**의미:**
- 프로세스 실패 시 자동 재시작
- 명시적 중지 전까지 재시작 유지
- 시스템 재부팅 후 자동 시작

### 5.2 관측성 및 모니터링

#### 5.2.1 모니터링 포인트

**프로세스 레벨:**
- 프로세스 실행 상태
- CPU 사용률
- 메모리 사용량
- 컨테이너 재시작 횟수

**애플리케이션 레벨:**
- 스냅샷 수신 카운트
- Validation 실패 카운트
- Guard 차단 카운트
- 스냅샷 처리 성공 카운트

**데이터 레벨:**
- JSONL 파일 크기
- 기록 속도 (records/sec)
- 파일 로테이션 상태

#### 5.2.2 로깅

**로그 출력:**
- 표준 출력 (stdout)
- 구조화된 로그 포맷
- 로그 레벨: INFO, WARNING, ERROR

**로그 내용:**
- Observer 시작/종료
- 스냅샷 처리 결과
- Validation/Guard 차단 사유
- Sink 오류

**로그 로테이션:**
- Docker 로그 드라이버 설정
- 최대 크기: 10MB
- 최대 파일 수: 3

#### 5.2.3 성능 메트릭

**파일:** `src/observer/performance_metrics.py`

**메트릭 타입:**
- **Counters**: 누적 카운트 (스냅샷 수신, 처리, 차단)
- **Gauges**: 현재 값 (버퍼 깊이)
- **Timings**: 지연 시간 (처리 시간, Validation 시간)

**특징:**
- 인메모리 전용 (프로세스 재시작 시 리셋)
- 동작에 영향 없음 (순수 관측)
- 스레드 안전

**접근:**
```python
from observer.performance_metrics import get_metrics

metrics = get_metrics()
summary = metrics.get_metrics_summary()
```

### 5.3 재시작 및 복구

#### 5.3.1 재시작 시나리오

**정상 재시작:**
1. 컨테이너 중지
2. 컨테이너 시작
3. Observer 프로세스 재시작
4. 대기 루프 재진입

**비정상 종료 후 재시작:**
1. 프로세스 크래시 감지
2. docker-compose 자동 재시작
3. 새 Observer 인스턴스 생성
4. 이전 JSONL 파일 유지 (append-only)

#### 5.3.2 데이터 복구

**JSONL 파일:**
- Append-only 특성으로 데이터 손실 최소화
- 각 write 후 즉시 flush
- 재시작 시 기존 파일에 계속 추가

**메트릭:**
- 인메모리 메트릭은 재시작 시 리셋
- 지속성 필요 시 외부 모니터링 시스템 사용

#### 5.3.3 복구 제약사항

**Observer는 다음을 복구하지 않는다:**
- 처리 중이던 스냅샷 (재전송 필요)
- 인메모리 메트릭
- 버퍼링된 데이터 (현재 버퍼링 미사용)

**복구 책임:**
- 외부 시스템이 스냅샷 재전송
- 모니터링 시스템이 메트릭 수집
- 볼륨 마운트가 파일 지속성 보장

### 5.4 운영 실패 시나리오

#### 5.4.1 컨테이너 실패

**증상:**
- 컨테이너 종료
- 프로세스 크래시

**자동 대응:**
- docker-compose 자동 재시작
- 새 Observer 인스턴스 시작

**수동 대응:**
- 로그 확인: `docker logs qts-observer`
- 컨테이너 재시작: `docker-compose restart qts-observer`

#### 5.4.2 디스크 공간 부족

**증상:**
- JSONL 파일 쓰기 실패
- Sink 오류 로그

**자동 대응:**
- Sink 오류 격리 (Observer 계속 실행)
- 오류 로깅

**수동 대응:**
- 디스크 공간 확보
- 오래된 JSONL 파일 아카이브/삭제
- 로그 로테이션 확인

#### 5.4.3 메모리 부족

**증상:**
- OOM (Out of Memory) 킬
- 컨테이너 재시작

**자동 대응:**
- docker-compose 자동 재시작

**수동 대응:**
- 메모리 제한 증가 (docker-compose.yml)
- 메모리 사용 패턴 분석
- 메모리 누수 확인

#### 5.4.4 Validation/Guard 과도한 차단

**증상:**
- 스냅샷 처리 성공률 저하
- 차단 로그 증가

**자동 대응:**
- 없음 (설계상 의도된 동작)

**수동 대응:**
- 차단 사유 분석
- 외부 시스템 스냅샷 품질 개선
- Validation 규칙 검토 (필요 시)

### 5.5 운영 명령

#### 5.5.1 시작/중지

**시작:**
```bash
docker-compose up -d
```

**중지:**
```bash
docker-compose down
```

**재시작:**
```bash
docker-compose restart qts-observer
```

#### 5.5.2 로그 확인

**실시간 로그:**
```bash
docker-compose logs -f qts-observer
```

**최근 로그:**
```bash
docker-compose logs --tail=100 qts-observer
```

#### 5.5.3 상태 확인

**컨테이너 상태:**
```bash
docker-compose ps
```

**리소스 사용:**
```bash
docker stats qts-observer
```

#### 5.5.4 데이터 확인

**JSONL 파일 확인:**
```bash
ls -lh ./config/observer/*.jsonl
```

**최근 레코드 확인:**
```bash
tail -n 10 ./config/observer/observer.jsonl | jq .
```

---

## 6. 아키텍처 제약 및 불변 요소

### 6.1 Phase 15 이후 동결된 요소

**동결된 요소:**
- Observer 컴포넌트 책임
- 데이터 흐름 아키텍처
- 스냅샷 계약 구조
- 저장 규칙
- Validation/Guard 경계

**동결되지 않은 요소:**
- Sink 구현 (확장 가능)
- Enrichment 메타데이터 내용 (네임스페이스 내)
- 외부 스냅샷 생성 방법

### 6.2 재검토하지 않을 결정

**영구 결정:**
- Observer는 매매 의사결정을 하지 않는다
- Observer는 태그/라벨을 생성하지 않는다
- Observer는 스냅샷을 수정하지 않는다
- Append-only 저장 모델
- 파일 기반 데이터 자산
- 계약 우선 설계 계층

### 6.3 명시적 비목표

Observer는 명시적으로 다음을 하지 않으며 향후에도 하지 않을 것이다:

**전략 및 매매:**
- 전략 판단
- 조건 평가
- 매매 의사결정
- 포지션 관리
- 리스크 승인

**데이터 처리:**
- 데이터 정규화
- 값 보정
- 누락 데이터 대체
- 지표 계산
- 신호 생성

**시스템 통합:**
- ETEDA 파이프라인 오케스트레이션
- 브로커 실행
- 스케줄링/트리거링 소유
- 자동 복구
- 재시도 정책 관리

**태깅 및 라벨링:**
- 레짐 분류
- 조건 태그 생성
- 결과 라벨 생성
- 패턴 감지 (오프라인으로 이동)

### 6.4 확장 포인트

#### 6.4.1 허용된 확장 (v1.x)

**허용:**
- 추가 Sink 구현 (DB, Stream, Object Storage)
- Log Sink 추가
- Metric collection Sink 추가

**불허:**
- Observer 내부 로직 확장
- 태그/라벨 생성 로직 추가
- 스냅샷 구조 수정
- 계약 규칙 변경

#### 6.4.2 Standalone vs 통합 실행

**두 모드 모두 지원:**
- Standalone: Observer-Core 독립 실행
- 통합: Observer-Core가 QTS 내에서 실행

**모드 간 불변:**
- 동일한 PatternRecord 구조
- 동일한 데이터 계약
- 동일한 저장 규칙

---

## 7. 데이터 무결성 규칙

모든 PatternRecord 출력은 다음을 만족해야 한다:

1. `snapshot` 필드가 항상 존재
2. `snapshot` 내부 필드는 불변
3. PatternRecord 저장은 append-only
4. 저장된 PatternRecord는 수정 또는 삭제 불가

**위반 결과:** 데이터가 QTS 학습/분석에서 자동 제외됨

---

## 8. 계약 계층

**우선순위 순서:**
1. QTS_Observer_Contract.md (최고 권한)
2. Observer_Architecture.md (본 문서)
3. 구현 코드

**규칙:** 아키텍처는 계약을 재정의하거나 확장할 수 없다. 계약 위반은 아키텍처를 무효화한다.

---

## 9. 아키텍처 잠금 선언

본 아키텍처는 Phase 15 완료 시점에 **잠금(LOCKED)**되었다.

**잠금 조건 충족:**
- QTS_Observer_Contract.md v1.0.0 확인
- Observer-Core v1.0.0 실행 검증
- 실시간 입력 통합 검증
- 구조 안정성 확인
- 아키텍처-계약 정렬 검증

**잠금 후 제한:**
- 컴포넌트 책임 변경 금지
- 데이터 흐름 변경 금지
- 계약 위반 구조 금지

---

## 10. 최종 아키텍처 선언

> **Observer_Architecture.md는 QTS Observer 시스템의 컴포넌트 책임, 데이터 흐름, 운영 경계에 대한 단일 진실 소스(Single Source of Truth)이다.**

> **모든 구현은 상위 계약 문서를 우선하면서 본 아키텍처를 따라야 한다.**

> **Observer는 해석, 의사결정, 실행 권한 없이 상태를 기록하는 판단 없는 관측 전용 시스템이다.**

---

**문서 종료**
