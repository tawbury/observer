# Meta
- Project Name: Stock Trading Observer - Data Collection System
- File Name: data_pipeline_architecture_observer_v1.0.md
- Document ID: ARCH-DATA-OBSERVER-001
- Status: Ready for Final Review
- Created Date: 2026-01-20
- Last Updated: 2026-01-20 (Revision 2)
- Author: Developer Agent (L1)
- Reviewer: PM Agent (L2 - Pending)
- Parent Document: stock_trading_system.workflow.md (Stage 3)
- Related Reference: obs_architecture.md, obs_prj_prd.md
- Related Specifications:
  - kis_api_specification_v1.0.md (KIS API 상세 명세 - C-001 해결)
  - data_validation_rules_v1.0.md (데이터 검증 규칙 - C-002 해결)
  - gap_detection_specification_v1.0.md (Gap 감지 명세 - C-003 해결)
  - implementation_details_supplement_v1.0.md (구현 상세 - M-001~M-005 해결)
- Version: 1.0.2
- Review Status: Critical Issues Resolved, Ready for PM Approval

---

# Stock Trading Observer - Data Collection Architecture Document

---

## Overview

### Architecture Vision

Stock Trading Observer는 다중 증권사 API를 통해 주식 시장 데이터를 실시간으로 수집하고 보관하는 **데이터 파이프라인 시스템**입니다. 본 아키텍처는 다음과 같은 비전을 추구합니다:

- **안정성 우선**: 시장 데이터 수집의 안정성과 무결성을 최우선으로 보장
- **최대 데이터 수집**: 리소스 제약 내에서 최대한의 시장 데이터 수집
- **재현 가능성**: 원천 로그를 통한 시장 상황 재현 및 백테스팅 지원
- **확장 가능성**: 다중 프로바이더 및 시장 확장을 고려한 설계
- **운영 효율성**: 자동화된 백업, 복구, 모니터링 체계

### System Boundaries

**시스템 범위:**
- 증권사 API를 통한 주식 시세 데이터 수집 (REST + WebSocket)
- 실시간 데이터 검증 및 품질 관리
- JSONL 기반 원천 로그 아카이브 생성
- 자동화된 백업 및 데이터 보관 관리

**시스템 외부 범위 (명시적 제외):**
- 트레이딩 전략 로직 및 의사결정 (별도 트레이딩 봇 담당)
- 실시간 주문 실행 (별도 주문 실행 시스템 담당)
- 데이터 분석 및 시각화 (별도 분석 시스템 담당)
- ETL 및 DB 변환 (Phase 2로 이관)

**외부 인터페이스:**
- **입력**: 증권사 REST API, WebSocket API (KIS, Kiwoom, Upbit, IB 등)
- **출력**: JSONL 아카이브 파일, 시스템 이벤트 로그, 백업 패키지

**시스템 책임:**
- 시장 데이터 수집 및 정규화
- 데이터 품질 검증 및 Guard 체크
- 로그 파티셔닝 및 아카이브 관리
- 백업 및 보관 주기 관리
- 시스템 모니터링 및 장애 대응

**시스템 제한:**
- Phase 1에서는 KIS API만 완전 구현 (다른 프로바이더는 인터페이스만 정의)
- 실시간 트레이딩 의사결정 없음 (데이터 수집만 담당)
- 고빈도 트레이딩(HFT) 수준의 밀리초 단위 처리는 미지원

---

## Architecture Principles

### Core Principles

1. **안정성 우선 (Stability First) - 가중 6/10**
   - **설명**: 데이터 수집 시스템의 안정성이 모든 기능보다 우선
   - **근거**: 시장 데이터 손실은 트레이딩 기회 손실로 직결되며 복구 불가능
   - **적용**: 장애 발생 시 증거 기록 필수, 조용한 실패 금지 (No Silent Failure)

2. **최대 로그 수집 (Maximum Data Collection) - 가중 4/10**
   - **설명**: 리소스 제약 내에서 가능한 최대한의 데이터 수집
   - **근거**: 더 많은 데이터가 더 나은 트레이딩 전략 개발 가능
   - **적용**: 완화(Mitigation) 정책을 통한 동적 부하 조절, 슬롯 커버리지 우선

3. **재현 가능성 (Reproducibility)**
   - **설명**: 모든 수집 데이터는 원천 형태로 보존하여 재현 가능
   - **근거**: 백테스팅, 전략 검증, 장애 분석에 필수
   - **적용**: JSONL 기반 Append-only 로그, 시간 순서 보장, 메타데이터 포함

4. **분리된 정책 계층 (Separated Policy Layer)**
   - **설명**: 데이터 수집과 트레이딩 로직을 명확히 분리
   - **근거**: 관심사의 분리로 유지보수성 및 확장성 향상
   - **적용**: Observer는 데이터 수집만 담당, 의사결정은 별도 시스템

5. **프로바이더 독립성 (Provider Independence)**
   - **설명**: 특정 증권사 API에 종속되지 않는 추상화 계층
   - **근거**: 다중 프로바이더 지원 및 프로바이더 변경 용이성
   - **적용**: IMarketDataProvider 인터페이스, 정규화된 데이터 스키마

### Design Guidelines

**모듈성 및 관심사 분리:**
- 각 컴포넌트는 단일 책임 원칙(SRP) 준수
- Provider Adapter 패턴을 통한 API 추상화
- Track A (REST/Swing)와 Track B (WebSocket/Scalp) 명확 분리
- 로그 파티셔닝을 통한 데이터 유형별 분리 (swing/, scalp/, system/)

**확장성 및 성능 고려사항:**
- 다중 프로바이더 동시 지원 가능한 구조
- 비동기 I/O 기반 WebSocket 처리
- 버퍼링 기반 JSONL Writer로 디스크 I/O 최적화
- 파티션 기반 파일 구조로 검색 성능 향상

**보안 및 컴플라이언스:**
- API 키 및 인증 정보의 안전한 관리 (환경 변수, Vault)
- HTTPS/WSS 기반 암호화 통신
- 데이터 백업 시 체크섬 검증
- 감사 로그(Audit Log) 기록

**유지보수성 및 확장성 원칙:**
- 명확한 인터페이스 정의 및 문서화
- 구조화된 로깅 (JSON 포맷)
- 단위 테스트 및 통합 테스트 가능한 설계
- Phase 기반 점진적 기능 확장

---

## System Structure

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 Provider Ingestion Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │   KIS    │  │   Kiwoom │  │  Upbit   │  │    IB    │      │
│  │   API    │  │   API    │  │  Crypto  │  │  Stocks  │      │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘      │
│        │              │              │              │          │
│        └──────────────┼──────────────┼──────────────┘          │
│                       │              │                         │
│              REST      │     WebSocket│                         │
└───────────────────────┼──────────────┼─────────────────────────┘
                        │              │
                        ▼              ▼
┌────────────────────────┐   ┌──────────────────────────┐
│   Track A (REST)       │   │   Track B (WebSocket)    │
│   Swing/Portfolio      │   │   Scalp High-Frequency   │
│   10분 주기            │   │   2Hz (완화시 1Hz)       │
│   09:00-15:30          │   │   09:30-15:00            │
└────────────┬───────────┘   └──────────┬───────────────┘
             │                          │
             └──────────┬───────────────┘
                        ▼
            ┌───────────────────────┐
            │  Universe Manager     │
            │  (전일 4,000원 이상)  │
            └───────────┬───────────┘
                        ▼
            ┌───────────────────────┐
            │   Observer Core       │
            │   - Validation        │
            │   - Guard             │
            │   - Enrichment        │
            └───────────┬───────────┘
                        ▼
            ┌───────────────────────┐
            │   Routing Engine      │
            │   (Track 분기)        │
            └─────┬─────────────┬───┘
                  │             │
        ┌─────────▼──┐    ┌────▼──────────┐
        │ Swing Path │    │  Scalp Path   │
        │            │    │  (41 Slots)   │
        └─────┬──────┘    └────┬──────────┘
              │                │
              │                ├──► Slot Manager
              │                └──► Overflow Ledger
              │
              └────────────┬───────────────┘
                           ▼
              ┌────────────────────────┐
              │  Log Partitioning      │
              │  - swing/              │
              │  - scalp/              │
              │  - system/             │
              └────────────┬───────────┘
                           ▼
              ┌────────────────────────┐
              │  Storage Layer         │
              │  - Raw Logs (3-10일)  │
              │  - Backup Verified     │
              └────────────┬───────────┘
                           ▼
              ┌────────────────────────┐
              │  Backup System         │
              │  (21:00 PC Pull)       │
              └────────────────────────┘
```

**주요 컴포넌트 관계:**
- **Provider Ingestion Layer**: 다중 증권사 API 추상화 및 정규화
- **Universe Manager**: 종목 선정 및 일일 Universe 스냅샷 관리
- **Track A/B Collector**: REST(10분) 및 WebSocket(2Hz) 기반 데이터 수집
- **Observer Core**: 데이터 검증, Guard, Enrichment 파이프라인
- **Log Partitioning**: swing/scalp/system 경로 분리 및 로그 저장
- **Backup System**: 일일 백업 및 보관 주기 관리

**데이터 흐름 패턴:**
1. **Track A**: REST API → Universe → 10분 주기 수집 → Observer → swing/ 로그
2. **Track B**: WebSocket → Trigger → 41 Slots → Observer → scalp/ 로그
3. **System**: 모든 이벤트 → System 로그 (gap, reconnect, overflow)

### Component Architecture

#### 1. Provider Ingestion Layer

**책임:**
- 다중 증권사 API 통합 및 추상화
- API 특성별 어댑터 패턴 적용
- 정규화된 MarketDataContract 생성
- 연결 상태 관리 및 Rate Limiting

**인터페이스:**
```python
class IMarketDataProvider(ABC):
    """Market data provider interface"""
    def fetch() -> Optional[MarketDataContract]
    def reset() -> None
    def close() -> None

class ProviderEngine:
    """Multi-provider orchestrator"""
    def __init__(self, providers: Dict[str, ProviderAdapter])
    def get_rest_client(self, provider: str) -> ProviderRestClient
    def get_ws_client(self, provider: str) -> ProviderWSClient
    def get_supported_markets(self) -> Dict[str, MarketInfo]
    def normalize_symbol(self, symbol: str, provider: str) -> str
    def normalize_data(self, data: Dict, provider: str) -> NormalizedData
```

**구현 상태:**
- **Phase 1**: KIS API 완전 구현 (REST + WebSocket)
- **Phase 2**: Kiwoom, Upbit, IB 인터페이스 정의 및 단계적 구현

#### 2. Universe Manager

**책임:**
- 거래 대상 종목 선정 (전일 종가 4,000원 이상)
- 일자별 Universe 스냅샷 파일 생성/관리
- 당일 Universe 고정 (재현성 보장)
- 다중 마켓별 Universe 통합 관리

**인터페이스:**
```python
class UniverseManager:
    def __init__(self, provider_engine: ProviderEngine)
    def load_universe(self, date: str, market: Market) -> List[Symbol]
    def create_daily_snapshot(self, date: str) -> Dict[Market, Path]
    def get_current_universe(self, market: Market) -> List[Symbol]
    def get_all_universes(self) -> Dict[Market, List[Symbol]]
```

**데이터 저장:**
- 경로: `config/universe/YYYYMMDD_{market}.json`
- 포맷: `{"date": "2026-01-20", "market": "kr_stocks", "symbols": ["005930", ...]}`

#### 3. Track A Collector (REST/Swing)

**책임:**
- 10분 주기 REST API 호출
- Universe 전체 종목 스냅샷 수집
- 스윙 트레이딩 및 포트폴리오 전략용 데이터

**수집 정책:**
- 시간: 09:00 ~ 15:30 (주식 시장 시간)
- 주기: 10분 (완화 시 조정 가능)
- 대상: Universe 전체 종목
- 필드: OHLCV + 기본 메타데이터

**인터페이스:**
```python
class TrackACollector:
    def __init__(self, provider_engine: ProviderEngine, universe_manager: UniverseManager)
    def collect_snapshot(self, market: Market) -> List[SwingSnapshot]
    def schedule_collection(self, market: Market, interval: timedelta = timedelta(minutes=10))
    def get_active_markets(self) -> List[Market]
```

#### 4. Track B Collector (WebSocket/Scalp)

**책임:**
- WebSocket 실시간 틱 데이터 수집
- 41개 슬롯 동시 모니터링
- 트리거 기반 종목 선정 및 교체
- Overflow 종목 Ledger 기록

**수집 정책:**
- 시간: 09:30 ~ 15:00 (변동성 높은 시간)
- 주기: 0.5초 (2Hz), 완화 시 1Hz
- 동시 보장: 41 종목
- 트리거: 거래량 급증, 체결 속도, 변동성, 수동

**인터페이스:**
```python
class TrackBCollector:
    def __init__(self, provider_engine: ProviderEngine, slot_manager: SlotManager)
    def stream_ticks(self, market: Market) -> Iterator[ScalpSnapshot]
    def handle_overflow(self, market: Market, candidates: List[Symbol])
    def get_active_markets(self) -> List[Market]

class SlotManager:
    MAX_SLOTS = 41
    def allocate_slot(self, market: Market, symbol: Symbol, trigger: TriggerType) -> Optional[Slot]
    def release_slot(self, market: Market, symbol: Symbol)
    def get_active_slots(self, market: Market) -> List[Slot]
    def record_overflow(self, market: Market, candidates: List[Candidate])
```

**트리거 우선순위:**
1. 거래량 급증 (Volume Surge) - 최우선
2. 체결 속도 증가 (Trade Velocity)
3. 변동성 급증 (Volatility Spike)
4. 수동 트리거 (Manual Override)

#### 5. Observer Core

**책임:**
- 데이터 검증 (Validation)
- Guard 체크 (비정상 데이터 필터링)
- 최소 Enrichment (메타데이터 추가)
- EventBus 디스패치

**파이프라인 (Phase 1 최소화):**
```python
class Observer:
    def observe(self, snapshot: ObservationSnapshot):
        # Phase 1: Validation (기본)
        if not self.validator.validate(snapshot):
            self.log_validation_failure(snapshot)
            return

        # Phase 2: Guard (기본)
        if not self.guard.check(snapshot):
            self.log_guard_rejection(snapshot)
            return

        # Phase 3: Record Creation (기본)
        record = self.create_pattern_record(snapshot)

        # Phase 4: Enrichment (최소화)
        enriched = self.enricher.enrich_minimal(record)

        # Phase 5: Dispatch (아카이브용)
        self.event_bus.dispatch_to_archive(enriched)
```

**Phase 1 최소화 원칙:**
- 판단/실행 없음
- 기본 메타데이터만 추가 (session_id, timestamp, quality_flag)
- 전략별 가공은 Phase 2 ETL로 이관

#### 6. Log Partitioning System

**책임:**
- Track별 로그 파일 분리 (swing/, scalp/, system/)
- 시간 기반 파일 Rotation
- 파일 무결성 검증

**디렉토리 구조:**
```
data/observer/
  ├── swing/
  │   └── {provider}/{market}/YYYYMMDD/HH_00.jsonl
  ├── scalp/
  │   └── {provider}/{market}/YYYYMMDD/HH_MM_SS.jsonl
  └── system/
      ├── events/{provider}/YYYYMMDD.jsonl
      └── overflow/{provider}/YYYYMMDD_overflow.jsonl
```

**Rotation 정책:**
- Swing: 1시간 단위 (HH_00.jsonl)
- Scalp: 위험 레벨별 (Level 0: 10분, Level 1: 30분, Level 2: 1시간)
- System: 1일 단위

**인터페이스:**
```python
class LogRotationManager:
    def rotate_swing_log(self, hour: int)
    def rotate_scalp_log(self, timestamp: datetime, risk_level: int)
    def rotate_system_log(self, date: str)
    def verify_integrity(self, log_file: Path) -> bool
```

#### 7. Backup System

**책임:**
- 일일 백업 패키지 생성
- Manifest 및 Checksum 검증
- PC → Server Pull 방식 백업
- Gap-marker 기록 (복원 없음)

**백업 정책:**
- 실행 시간: 매일 21:00 (시장 종료 후)
- 방향: PC → Server (Pull)
- 검증: MD5/SHA256 Checksum
- Gap 처리: 증거 기록만, 복원 시도 없음

**인터페이스:**
```python
class BackupManager:
    def create_daily_package(self, date: str) -> BackupPackage
    def generate_manifest(self, files: List[Path]) -> Manifest
    def calculate_checksums(self, files: List[Path]) -> Dict[str, str]
    def mark_success(self, package: BackupPackage)
```

**Gap-marker 정책:**
- "Record gap evidence, don't restore"
- 갭 발생 시 복원 시도 없이 증거만 기록
- `system/events/` 디렉토리에 `gap_marker` 이벤트 저장
- 분석 시 갭 구간 명확히 식별하여 데이터 품질 평가

#### 8. Retention & Lifecycle Manager

**책임:**
- Raw 로그 보관 주기 관리 (3-10일)
- 이상일 감지 및 보관 기간 연장
- 백업 완료 확인 후 삭제

**보관 정책:**
- 기본 보관: 3일
- 이상일 연장: 7일
- 백업 미완료: 삭제 금지
- 최대 캡: 10일

**이상일 판정 조건:**
- WS 재연결 ≥ 20회/일
- WS 끊김 누적 ≥ 10분/일
- 로그 공백 60초 이상 2회 이상/일
- Scalp 기록률 < 97% (5분 이상)
- CPU ≥ 85% (10분 이상)
- 디스크 사용률 > 80%

**인터페이스:**
```python
class RetentionManager:
    def evaluate_retention(self, date: str) -> RetentionPolicy
    def extend_for_anomaly(self, date: str, reason: str)
    def cleanup_expired(self, backup_verified: bool)
    def get_retention_status(self) -> Dict[str, RetentionInfo]
```

#### 9. Mitigation System

**책임:**
- 시스템 리소스 모니터링
- 부하 상황 감지 및 완화 레벨 결정
- 주파수 조절 (2Hz → 1Hz → 0.5Hz)

**완화 우선순위:**
> **Symbol Coverage (41 slots) > Hz (Frequency)**
> 슬롯 커버리지를 먼저 보장하고, 부하 시 주파수를 낮춘다.

**완화 레벨:**
| 레벨 | 주파수 | 상태 | 설명 |
|------|--------|------|------|
| Level 0 | 2Hz | 정상 | 기본 운영 모드 |
| Level 1 | 1Hz | 경미한 부하 | 리소스 사용량 증가 시 |
| Level 2 | 0.5Hz | 심각한 부하 | 시스템 안정성 우선 모드 |

**발동 조건 (5분 지속):**
| 조건 | Level 1 | Level 2 |
|------|---------|---------|
| CPU 사용률 | ≥ 80% | ≥ 90% |
| 메모리 사용률 | ≥ 85% | ≥ 95% |
| 디스크 쓰기 지연 | ≥ 500ms | ≥ 1000ms |
| 이벤트 큐 지연 | ≥ 2초 | ≥ 5초 |

**인터페이스:**
```python
class MitigationController:
    PRIORITY = ["symbol_coverage", "frequency"]
    def monitor_resources(self) -> ResourceMetrics
    def evaluate_mitigation(self, metrics: ResourceMetrics) -> MitigationLevel
    def apply_mitigation(self, level: MitigationLevel)
    def get_current_hz(self, level: MitigationLevel) -> float
```

#### 10. WebSocket Reconnection Manager

**책임:**
- WebSocket 연결 상태 모니터링
- 끊김 감지 및 자동 재연결
- Backoff 정책 적용
- 재연결 이벤트 로깅

**Backoff 정책:**
```
1s → 2s → 5s → 10s → 20s → 30s → 60s (반복)
```

**연속 실패 처리 (5분):**
- Scalp 기록 일시 중지
- System 로그에 강력 기록 (CRITICAL level)
- 이상일 마킹

**인터페이스:**
```python
class ReconnectionManager:
    def handle_disconnect(self, reason: str)
    def calculate_backoff(self, attempt: int) -> float
    def attempt_reconnect(self) -> bool
    def log_reconnection_event(self, event: ReconnectionEvent)
```

### Data Architecture

**데이터 모델:**

#### MarketDataContract (정규화 데이터)

```json
{
  "meta": {
    "source": "kis",
    "market": "kr_stocks",
    "captured_at": "2026-01-20T09:31:05.123Z",
    "schema_version": "1.0"
  },
  "instruments": [
    {
      "symbol": "005930",
      "timestamp": "2026-01-20T09:31:05.000Z",
      "price": {
        "open": 71000,
        "high": 71200,
        "low": 70800,
        "close": 71100
      },
      "volume": 1523400,
      "bid_price": 71000,
      "ask_price": 71100,
      "bid_size": 5200,
      "ask_size": 3100
    }
  ]
}
```

#### PatternRecordContract (Phase 1 아카이브)

```json
{
  "session_id": "sess_20260120_093000",
  "generated_at": "2026-01-20T09:31:05.200Z",
  "observation": {
    // MarketDataContract 내용
  },
  "schema": {
    "version": "1.0.0",
    "field_count": 12
  },
  "quality": {
    "validation_passed": true,
    "guard_passed": true,
    "quality_flag": "normal"
  },
  "interpretation": {
    "mitigation_level": 0,
    "track": "scalp",
    "slot_number": 15
  }
}
```

**데이터 저장 전략:**
- **Format**: JSONL (JSON Lines) - 한 줄당 하나의 JSON 객체
- **Append-only**: 데이터 추가만 가능, 수정/삭제 불가
- **Partitioning**: 날짜/시간/프로바이더/마켓 기준 파티셔닝
- **Compression**: 백업 시 gzip 압축

**데이터 흐름:**
```
Provider API
  → MarketDataContract (정규화)
  → Observer Core (검증/Guard/Enrichment)
  → PatternRecordContract (아카이브)
  → JSONL 파일 (swing/ or scalp/)
  → Backup (21:00 daily)
```

---

## Technology Stack

### Backend Technologies

| 기술 | 버전 | 목적 및 근거 |
|-----|------|------------|
| **Python** | 3.11+ | 주요 개발 언어. 데이터 처리 라이브러리 생태계 풍부 |
| **pandas** | 1.5.0+ | 데이터 프레임 조작 및 분석 |
| **numpy** | 1.24.0+ | 수치 계산 및 배열 연산 |
| **python-json-logger** | 2.0.0+ | 구조화된 JSON 로깅 |
| **requests** | Latest | REST API 클라이언트 |
| **websocket-client** | Latest | WebSocket 클라이언트 |
| **pyarrow** | Latest | Parquet 파일 I/O (Phase 2) |
| **asyncio** | Stdlib | 비동기 I/O 처리 |

**선정 근거:**
- **Python**: 데이터 처리 및 금융 분석에 최적화된 언어
- **pandas/numpy**: 시계열 데이터 처리의 사실상 표준
- **asyncio**: WebSocket 다중 연결 효율적 관리

### Infrastructure

| 기술 | 목적 및 설정 |
|-----|------------|
| **Docker** | 컨테이너화 배포, Python 3.11 이미지 기반 |
| **Docker Compose** | 다중 컨테이너 오케스트레이션 |
| **Azure VM** | 클라우드 호스팅 (Ubuntu 22.04 LTS) |
| **Terraform** | IaC 기반 인프라 프로비저닝 |
| **systemd** | 프로세스 관리 및 자동 재시작 |

**인프라 구성:**
- VM 스펙: Standard_B2s (2 vCPU, 4GB RAM) - Phase 1 기준
- 스토리지: Premium SSD 128GB (IOPS 보장)
- 네트워크: VNet + NSG (필요한 포트만 개방)

### Development & Operations

| 도구 | 목적 |
|-----|------|
| **Git** | 소스 코드 버전 관리 |
| **GitHub Actions** | CI/CD 파이프라인 |
| **pytest** | 단위 테스트 및 통합 테스트 |
| **black** | 코드 포맷팅 |
| **mypy** | 정적 타입 체킹 |
| **ruff** | 린팅 |

---

## Implementation Plan

### Development Phases

#### Phase 1: Foundation & KIS Integration (현재 단계)

**목표:**
- 기본 인프라 구축
- KIS API 완전 통합
- 아카이브 생성 파이프라인 완성

**주요 산출물:**
- Provider Ingestion Layer (KIS 완전 구현)
- Universe Manager
- Track A/B Collector (KIS WebSocket + REST)
- Observer Core (최소 기능)
- Log Partitioning System
- Backup System

**성공 기준:**
- KIS API 정상 데이터 수집 (Track A: 10분, Track B: 2Hz)
- 41 슬롯 안정적 운영
- 일일 백업 자동화 성공
- 데이터 품질 검증 통과

**타임라인:** 4주 (2026-01-20 ~ 2026-02-16)

#### Phase 2: Multi-Provider Expansion (계획 중)

**목표:**
- 다중 프로바이더 지원
- ETL 파이프라인 구현
- DB 저장 기능

**주요 산출물:**
- Kiwoom, Upbit, IB Provider Adapter 구현
- TradingETLPipeline (아카이브 → DB)
- PostgreSQL 스키마 구현
- Cross-provider 정규화 검증

**성공 기준:**
- 2개 이상 프로바이더 동시 운영
- ETL 파이프라인 일일 자동 실행
- DB 데이터 품질 검증

**타임라인:** 6주 (Phase 1 완료 후)

#### Phase 3: Advanced Features (미래)

**목표:**
- 고급 모니터링 및 알림
- 데이터 품질 자동 분석
- 백테스팅 지원 인터페이스

**주요 산출물:**
- 실시간 모니터링 대시보드
- 이상 감지 및 알림 시스템
- 백테스팅 데이터 API

**타임라인:** Phase 2 완료 후 결정

### Technical Roadmap

**Milestone 1: KIS Data Collection (Week 1-2)**
- KIS REST/WebSocket 어댑터 구현
- Universe Manager 구현
- Track A Collector 구현

**Milestone 2: Scalp & Monitoring (Week 3)**
- Track B Collector 구현
- Slot Manager 구현
- Mitigation System 구현

**Milestone 3: Persistence & Backup (Week 4)**
- Log Partitioning 구현
- Backup System 구현
- Retention Manager 구현

**Milestone 4: Integration Testing (Week 4)**
- 통합 테스트 실행
- 부하 테스트 (41 slots, 2Hz)
- 백업/복구 테스트

---

## Decision Items

### Architecture Decisions

#### AD-001: JSONL vs Database for Raw Data

**Context:**
Phase 1에서 원천 데이터 저장 포맷 선택 필요

**Options:**
1. JSONL (JSON Lines) 파일
2. PostgreSQL Database
3. NoSQL (MongoDB, Cassandra)

**Decision:** JSONL 파일 선택

**Rationale:**
- **재현성**: 파일 기반이 시간 순서 보장 및 재현 용이
- **단순성**: DB 의존성 없이 독립 실행 가능
- **백업**: 파일 복사만으로 백업 완료
- **검증**: 체크섬 검증 용이
- **비용**: DB 인프라 비용 절감
- **Phase 분리**: Phase 2에서 DB 변환 예정

#### AD-002: Pull vs Push Backup Strategy

**Context:**
백업 방향 결정 (PC → Server vs Server → PC)

**Options:**
1. Push: Server → PC (서버가 능동적으로 전송)
2. Pull: PC → Server (PC가 서버에서 가져옴)

**Decision:** Pull 방식 (PC → Server)

**Rationale:**
- **보안**: 서버에 PC 접근 권한 불필요
- **유연성**: PC 오프라인 시에도 서버 정상 운영
- **스케줄**: PC 주도 백업 시간 조정 용이
- **복원**: PC 측에서 복원 시점 선택 가능

#### AD-003: Symbol Coverage vs Frequency Priority

**Context:**
시스템 부하 시 완화 우선순위 결정

**Options:**
1. Symbol Coverage 우선: 41개 종목 유지 → 주파수 낮춤
2. Frequency 우선: 2Hz 유지 → 종목 수 감소

**Decision:** Symbol Coverage 우선

**Rationale:**
- **트레이딩 기회**: 더 많은 종목 모니터링이 기회 확대
- **다변화**: 포트폴리오 다변화 효과
- **주파수 영향**: 2Hz → 1Hz 감소는 스캘핑에 수용 가능
- **시스템 안정성**: 종목 수 유지가 시스템 안정성 향상

#### AD-004: Gap Restore vs Gap Marker

**Context:**
데이터 갭 발생 시 복원 시도 여부

**Options:**
1. Gap Restore: 갭 발생 시 API 재호출로 데이터 복원 시도
2. Gap Marker: 갭 증거만 기록, 복원 시도 없음

**Decision:** Gap Marker 방식

**Rationale:**
- **안정성**: 복원 시도가 시스템 부하 가중 가능
- **정확성**: 실시간 데이터와 복원 데이터 혼재 방지
- **투명성**: 갭 명확히 표시하여 데이터 품질 신뢰도 향상
- **분석 용이**: 갭 구간 인지하고 분석 가능

### Trade-offs

#### TO-001: Real-time vs Batch Processing

**고려 사항:**
- Real-time: 즉각 처리, 높은 리소스 사용
- Batch: 지연 허용, 효율적 리소스 사용

**선택:** Hybrid 방식
- **Track B (Scalp)**: Real-time 처리 (2Hz)
- **Track A (Swing)**: Semi-batch 처리 (10분)

**근거:** 트레이딩 전략 특성에 맞춤 (스캘핑은 실시간 필수, 스윙은 주기적 수집 충분)

#### TO-002: Memory vs Disk I/O

**고려 사항:**
- Memory Buffering: 빠른 처리, 장애 시 데이터 손실 위험
- Direct Disk Write: 안정적, 느린 I/O

**선택:** Buffered Write with Periodic Flush
- 버퍼 크기: 1000 레코드 또는 60초 중 먼저 도달
- Flush 정책: 시간/크기 기반

**근거:** 성능과 안정성 균형, 최대 60초 데이터만 손실 위험

#### TO-003: Vertical vs Horizontal Scaling

**고려 사항:**
- Vertical: 단일 서버 스펙 향상
- Horizontal: 다중 서버 분산

**선택 (Phase 1):** Vertical Scaling
- 단일 VM 스펙 점진적 증가 (B2s → B2ms → B4ms)

**선택 (Phase 2+):** Horizontal Scaling 고려
- 마켓별 서버 분리 (kr_stocks, crypto, us_stocks)

**근거:** Phase 1 단순성 우선, 확장 시 수평 확장 전환

---

## Quality Attributes

### Performance

**Response Time Requirements:**
- Track A REST API 호출: < 2초
- Track B WebSocket 수신: < 100ms (평균)
- 로그 Write 지연: < 500ms (버퍼링 포함)

**Throughput Requirements:**
- Track A: 4,000+ 종목 / 10분 = 약 7 종목/초
- Track B: 41 종목 × 2Hz = 82 틱/초

**Scalability Targets:**
- Phase 1: 41 슬롯, 2Hz
- Phase 2: 100 슬롯 확장 가능 (마켓별 분리)
- Phase 3: 다중 서버 분산 아키텍처

**Performance Monitoring Strategy:**
- 수집률 모니터링: Track A 99.5%+, Track B 97%+
- 레이턴시 추적: P50, P95, P99 메트릭
- 리소스 모니터링: CPU, Memory, Disk I/O

### Security

**Security Requirements:**
- API 키 암호화 저장 (환경 변수 또는 Vault)
- HTTPS/WSS 통신 (TLS 1.2+)
- 백업 파일 체크섬 검증 (SHA256)
- 로그 파일 권한 제한 (600)

**Authentication & Authorization:**
- 증권사 API: OAuth 2.0 또는 API Key + Secret
- Azure VM: SSH 키 기반 인증 (비밀번호 비활성화)
- 백업 전송: SCP/SFTP (SSH 키 인증)

**Data Protection Measures:**
- 민감 정보 로깅 금지 (API 키, 개인정보)
- 백업 데이터 암호화 (선택적, Phase 2)
- 네트워크 격리 (VNet + NSG)

**Security Testing Approach:**
- API 키 노출 검사 (pre-commit hook)
- 의존성 취약점 스캔 (Dependabot)
- 정기 보안 패치 적용

### Reliability

**Availability Requirements:**
- 시장 시간 가동률: 99.9% (월 약 43분 다운타임 허용)
- 백업 성공률: 100% (실패 시 알림 필수)

**Fault Tolerance Strategies:**
- WebSocket 자동 재연결 (Backoff 정책)
- REST API Retry (3회, Exponential Backoff)
- Graceful Degradation (Mitigation System)
- 데이터 검증 실패 시 로깅 후 계속 (No Silent Failure)

**Disaster Recovery Plans:**
- 백업: 일일 백업, 3일 로컬 보관, 30일 원격 보관
- 복구: 백업에서 특정 날짜 데이터 복원 (manual)
- VM 스냅샷: 주간 자동 스냅샷 (인프라 재구성용)

**Monitoring & Alerting:**
- 시스템 메트릭: CPU, Memory, Disk (5분 간격)
- 수집 품질: Track A/B 기록률 (실시간)
- WebSocket 상태: 연결/재연결 횟수 (실시간)
- 백업 상태: 성공/실패 (일일)

**알림 채널:**
- Critical: 즉시 Telegram 알림
- Warning: 로그 기록, 일일 요약 리포트
- Info: 로그 기록만

### Maintainability

**Code Quality Standards:**
- PEP 8 준수 (black 포맷터)
- Type Hints 사용 (mypy 검증)
- 함수 복잡도: Cyclomatic Complexity < 10
- 테스트 커버리지: 80%+ (core 모듈)

**Documentation Requirements:**
- 모든 public 함수/클래스 Docstring
- 아키텍처 문서 (본 문서)
- API 명세서 (Swagger/OpenAPI - Phase 2)
- 운영 매뉴얼 (Runbook)

**Testing Strategies:**
- 단위 테스트: pytest 기반, 80%+ 커버리지
- 통합 테스트: Mock Provider 사용
- 부하 테스트: 41 slots × 2Hz 시뮬레이션
- 백업 테스트: 복원 시나리오 검증

**Deployment & Maintenance Procedures:**
- CI/CD: GitHub Actions (테스트 → 빌드 → 배포)
- Blue-Green Deployment (Phase 2)
- 롤백 절차: Docker 이미지 태그 기반
- 로그 순환: 30일 보관 후 삭제

---

## Integration Points

### External Systems

#### 1. KIS (한국투자증권) OpenAPI

**Interface Specifications:**
- **REST API**: `https://openapi.koreainvestment.com:9443`
- **WebSocket**: `wss://openapi.koreainvestment.com:9443/ws`
- **Auth**: OAuth 2.0 (Access Token + App Key/Secret)
- **Rate Limit**: REST 20 req/sec, WebSocket 41 concurrent

**Data Format:**
- Request: JSON
- Response: JSON (REST), Text (WebSocket - 변환 필요)

**Endpoints:**
- `/uapi/domestic-stock/v1/quotations/inquire-price`: 현재가 조회
- `/uapi/domestic-stock/v1/quotations/inquire-daily-price`: 일봉 조회
- WebSocket: 실시간 체결 (H0STCNT0)

#### 2. Kiwoom API (Phase 2)

**Interface Specifications:**
- **Type**: COM/OCX + WebSocket
- **Platform**: Windows Only
- **Auth**: 공인인증서 기반

**Status:** 인터페이스 정의만, 구현 Phase 2

#### 3. Upbit API (Phase 2)

**Interface Specifications:**
- **REST API**: `https://api.upbit.com/v1`
- **WebSocket**: `wss://api.upbit.com/websocket/v1`
- **Auth**: JWT (Access Key + Secret Key)

**Status:** 인터페이스 정의만, 구현 Phase 2

### APIs

#### Internal Event Bus API

**Purpose:** Observer Core → Log Partitioning 이벤트 전달

**Endpoint:** In-process message queue (asyncio.Queue)

**Format:**
```python
@dataclass
class ArchiveEvent:
    event_type: str  # "swing" | "scalp" | "system"
    timestamp: datetime
    data: PatternRecordContract
    metadata: Dict[str, Any]
```

**Authentication:** N/A (internal)

#### Backup API (Phase 1 - File-based)

**Purpose:** PC → Server 백업 파일 전송

**Protocol:** SCP/SFTP

**Format:**
```
backup/{YYYYMMDD}/
  ├── manifest.json
  ├── swing_YYYYMMDD.tar.gz
  ├── scalp_YYYYMMDD.tar.gz
  └── system_YYYYMMDD.tar.gz
```

**Authentication:** SSH 키 기반

---

## Deployment Architecture

### Environment Architecture

#### Development Environment

**Location:** 로컬 개발 머신

**Configuration:**
- Docker Compose 기반 로컬 실행
- Mock Provider 사용 (실제 API 호출 없음)
- 환경 변수: `.env.dev`
- 로그 레벨: DEBUG

**Purpose:** 개발 및 단위 테스트

#### Testing Environment (Staging)

**Location:** Azure VM (Staging)

**Configuration:**
- Docker Compose 기반
- KIS API 테스트 계정 사용
- Universe: 소규모 (100종목)
- 환경 변수: `.env.staging`
- 로그 레벨: INFO

**Purpose:** 통합 테스트 및 배포 검증

#### Production Environment

**Location:** Azure VM (Production)

**Configuration:**
- Docker Compose 기반
- KIS API 실 계정 사용
- Universe: 전체 (4,000+ 종목)
- 환경 변수: `.env.prod` (Vault 연동)
- 로그 레벨: WARNING
- 모니터링: 활성화
- 백업: 자동화

**Purpose:** 실제 데이터 수집 운영

### Infrastructure Components

#### Component 1: Observer Application Container

**Configuration:**
- **Base Image**: `python:3.11-slim`
- **Volumes**:
  - `/app/data`: 데이터 저장 (persistent)
  - `/app/logs`: 로그 저장 (persistent)
  - `/app/config`: 설정 파일 (read-only)
- **Environment Variables**:
  - `OBSERVER_STANDALONE=1`
  - `PYTHONPATH=/app/src:/app`
  - `OBSERVER_DATA_DIR=/app/data/observer`
- **Resources**:
  - Memory: 2GB
  - CPU: 1 vCPU

**Purpose:** Observer 메인 애플리케이션 실행

#### Component 2: Backup Coordinator (Phase 1 - Cron)

**Configuration:**
- **Type**: Cron Job (systemd timer)
- **Schedule**: 매일 21:00 KST
- **Script**: `backup_daily.sh`
- **Target**: SCP to local PC

**Purpose:** 일일 백업 자동화

#### Component 3: Azure Storage (Phase 2)

**Configuration:**
- **Type**: Azure Blob Storage (Archive tier)
- **Purpose**: 장기 백업 보관 (30일+)
- **Access**: SAS Token

**Status:** Phase 2에서 구현 예정

### Monitoring and Observability

#### Logging Strategy

**Log Levels:**
- **DEBUG**: 개발 환경에서만 사용
- **INFO**: 주요 이벤트 (데이터 수집, 백업 시작/종료)
- **WARNING**: 경고 (Mitigation 발동, 재연결)
- **ERROR**: 오류 (API 호출 실패, 검증 실패)
- **CRITICAL**: 치명적 오류 (시스템 중단)

**Log Format:** JSON Lines
```json
{
  "timestamp": "2026-01-20T09:31:05.123Z",
  "level": "INFO",
  "logger": "observer.core",
  "message": "Track B slot allocated",
  "extra": {
    "symbol": "005930",
    "slot": 15,
    "trigger": "volume_surge"
  }
}
```

**Log Rotation:**
- 파일: `/app/logs/observer_YYYYMMDD.log`
- 보관: 30일
- 압축: gzip (7일 이후)

#### Metrics Collection

**Key Metrics:**
- `track_a_collection_rate`: Track A 수집 성공률 (%)
- `track_b_collection_rate`: Track B 수집 성공률 (%)
- `ws_reconnect_count`: WebSocket 재연결 횟수 (count/hour)
- `slot_utilization`: 슬롯 활용률 (%)
- `mitigation_level`: 현재 완화 레벨 (0/1/2)
- `disk_usage_percent`: 디스크 사용률 (%)
- `cpu_usage_percent`: CPU 사용률 (%)

**Collection Interval:** 5분

**Storage:** JSONL 파일 (metrics/YYYYMMDD.jsonl)

#### Alerting and Notification

**Alert Rules:**

| 조건 | 심각도 | 알림 채널 | 조치 |
|-----|--------|---------|------|
| Track A 수집률 < 95% (10분) | WARNING | Log | 모니터링 |
| Track B 수집률 < 90% (5분) | WARNING | Telegram | 확인 필요 |
| WebSocket 재연결 > 20회/일 | WARNING | Telegram | 네트워크 점검 |
| 백업 실패 | CRITICAL | Telegram | 즉시 조치 |
| 디스크 사용률 > 80% | CRITICAL | Telegram | 정리 필요 |
| CPU > 90% (10분) | CRITICAL | Telegram | 리소스 증설 |

**Telegram Bot 설정:**
- Bot Token: 환경 변수 `TELEGRAM_BOT_TOKEN`
- Chat ID: 환경 변수 `TELEGRAM_CHAT_ID`

#### Performance Monitoring

**Dashboard (Phase 2):**
- Grafana 기반 시각화
- 실시간 메트릭 그래프
- 이상 감지 하이라이트

**Current (Phase 1):**
- 로그 기반 수동 분석
- 일일 요약 리포트 (자동 생성)

---

## Risk Assessment

### Technical Risks

#### TR-001: API Rate Limiting

**Impact:** 높음 (데이터 수집 중단)
**Probability:** 중간 (API 정책 변경 시)
**Mitigation:**
- Rate Limiter 구현 (토큰 버킷 알고리즘)
- API 호출 로그 분석 및 최적화
- 백업 프로바이더 준비 (Kiwoom, Upbit)
- Graceful Degradation (완화 레벨 적용)

#### TR-002: WebSocket Connection Instability

**Impact:** 중간 (Scalp 데이터 갭 발생)
**Probability:** 높음 (네트워크 불안정 시)
**Mitigation:**
- Backoff 기반 자동 재연결
- 갭 마커 기록 (Gap-marker policy)
- 이상일 마킹 및 보관 기간 연장
- 알림 시스템으로 즉시 인지

#### TR-003: Disk Space Exhaustion

**Impact:** 치명적 (데이터 수집 중단)
**Probability:** 낮음 (모니터링 시)
**Mitigation:**
- 디스크 사용률 모니터링 (80% 알림)
- Retention Policy 엄격 적용 (3-10일)
- 백업 완료 후 자동 정리
- 디스크 확장 계획 (Azure 관리 디스크)

#### TR-004: Data Quality Issues

**Impact:** 중간 (잘못된 데이터 기록)
**Probability:** 중간 (API 응답 변경 시)
**Mitigation:**
- Validation Layer 구현 (스키마 검증)
- Guard 체크 (비정상 데이터 필터링)
- Quality Flag 기록 (normal, degraded, gap)
- 정기 데이터 품질 감사

### Operational Risks

#### OR-001: Backup Failure

**Impact:** 높음 (데이터 손실 위험)
**Probability:** 낮음 (자동화 시)
**Mitigation:**
- 백업 성공 검증 (Checksum, Manifest)
- 백업 실패 시 즉시 알림 (Telegram)
- 백업 미완료 시 로그 삭제 금지
- 백업 이중화 (로컬 + Azure Blob - Phase 2)

#### OR-002: Operator Error

**Impact:** 중간 (설정 오류, 수동 작업 실수)
**Probability:** 중간 (수동 개입 시)
**Mitigation:**
- 자동화 최대화 (백업, 정리, 모니터링)
- 운영 매뉴얼 작성 및 교육
- 수동 작업 체크리스트
- 롤백 절차 문서화

#### OR-003: System Downtime during Market Hours

**Impact:** 치명적 (트레이딩 기회 손실)
**Probability:** 낮음 (안정화 후)
**Mitigation:**
- 시장 시간 외 유지보수 (15:30 ~ 09:00)
- Blue-Green 배포 (Phase 2)
- 헬스 체크 및 자동 재시작 (systemd)
- 긴급 롤백 절차

#### OR-004: Monitoring Blind Spot

**Impact:** 중간 (문제 인지 지연)
**Probability:** 중간 (초기 운영)
**Mitigation:**
- 핵심 메트릭 우선 모니터링
- 알림 규칙 점진적 개선
- 일일 요약 리포트 확인
- Phase 2 대시보드 구축

---

## Evolution Strategy

### Future Considerations

**Scalability Evolution Paths:**
- **Vertical Scaling (Phase 1-2)**: VM 스펙 증가 (B2s → B4ms)
- **Horizontal Scaling (Phase 3+)**: 마켓별 서버 분리
  - Server 1: kr_stocks (KIS, Kiwoom)
  - Server 2: crypto (Upbit)
  - Server 3: us_stocks (IB)
- **Cloud-Native (Future)**: Kubernetes 기반 컨테이너 오케스트레이션

**Technology Migration Strategies:**
- **Database Migration (Phase 2)**: JSONL → PostgreSQL ETL
- **Messaging Queue (Phase 3)**: In-process Queue → Redis/RabbitMQ
- **Storage Migration (Future)**: Local Disk → Azure Blob Storage

**Architecture Evolution Roadmap:**
- **Phase 1 (현재)**: Monolithic 구조, KIS 단일 프로바이더
- **Phase 2**: Multi-Provider, ETL 분리, DB 통합
- **Phase 3**: Microservices 전환 고려 (Provider별 서비스 분리)
- **Phase 4**: 실시간 스트리밍 아키텍처 (Apache Kafka 고려)

### Maintenance Strategy

**Regular Review Cycles:**
- **주간**: 시스템 메트릭 리뷰, 알림 검토
- **월간**: 데이터 품질 감사, 성능 분석
- **분기**: 아키텍처 리뷰, 기술 부채 평가
- **반기**: 인프라 스펙 재평가, 비용 최적화

**Update and Upgrade Procedures:**
- **보안 패치**: 즉시 적용 (Critical), 주간 적용 (일반)
- **의존성 업그레이드**: 월간 정기 업데이트
- **메이저 버전 업그레이드**: 분기별 계획 및 테스트

**Technical Debt Management:**
- 코드 리뷰 시 기술 부채 태그 (`TODO`, `FIXME`)
- 월간 기술 부채 백로그 정리
- 각 스프린트에 20% 기술 부채 해소 시간 할당

---

## Appendix

### Glossary

- **Track A**: REST API 기반 10분 주기 데이터 수집 (스윙/포트폴리오 전략용)
- **Track B**: WebSocket 기반 2Hz 실시간 데이터 수집 (스캘핑 전략용)
- **Universe**: 거래 대상 종목 리스트 (전일 종가 4,000원 이상)
- **Slot**: Track B에서 동시 모니터링 가능한 종목 슬롯 (최대 41개)
- **Mitigation Level**: 시스템 부하에 따른 완화 단계 (0: 정상, 1: 경미, 2: 심각)
- **Gap-marker**: 데이터 갭 발생 시 복원 없이 증거만 기록하는 정책
- **PatternRecord**: Observer가 생성하는 아카이브용 데이터 레코드

### References

- **PRD**: `docs/dev/obs_prj_prd.md` - Product Requirements Document
- **기존 아키텍처**: `docs/dev/obs_architecture.md` v0.3
- **워크플로우**: `.ai/workflows/stock_trading_system.workflow.md`
- **KIS API 문서**: `https://apiportal.koreainvestment.com/`

### Related Detailed Specifications

이 아키텍처 문서는 다음 상세 명세서들과 함께 읽어야 합니다:

1. **[KIS API Specification](kis_api_specification_v1.0.md)**
   - KIS REST/WebSocket API 상세 명세
   - 인증, Rate Limiting, 에러 처리
   - **해결**: C-001 (KIS API 상세 명세 누락)

2. **[Data Validation Rules](data_validation_rules_v1.0.md)**
   - Schema, Range, Guard 검증 규칙
   - Quality Flag 할당 로직
   - **해결**: C-002 (데이터 검증 규칙 불완전)

3. **[Gap Detection Specification](gap_detection_specification_v1.0.md)**
   - Gap 감지 알고리즘 (Track A/B별)
   - Gap-marker 데이터 스키마
   - 이상일 마킹 정책
   - **해결**: C-003 (Gap-marker 상세 정보 부족)

4. **[Implementation Details Supplement](implementation_details_supplement_v1.0.md)**
   - Universe Manager 구현 플로우
   - Mitigation System 슬라이딩 윈도우
   - 백업 Pull SSH/SCP 설정
   - Retention 긴급 정리 절차
   - WebSocket 슬롯 복구 로직
   - **해결**: M-001 ~ M-005 (Major 이슈들)

### Document Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-20 | Developer Agent | Initial architecture design document created based on workflow Stage 3 |
| 1.0.1 | 2026-01-20 | Developer Agent | Added related specifications references (C-001~C-003) |
| 1.0.2 | 2026-01-20 | Developer Agent | Added implementation details supplement (M-001~M-005), ready for final review |

---

**Document Status:** Ready for Final Review - Critical Issues Resolved

**Review Summary:**
- ✅ **Critical Issues (C-001~C-003)**: Resolved with detailed specification documents
- ✅ **Major Issues (M-001~M-005)**: Resolved with implementation details supplement
- ⏳ **Minor Issues**: Acknowledged for Phase 2 improvements
- 📋 **PM L2 Review**: Pending final approval

**Next Steps:**
1. ✅ Critical 이슈 해결 완료 (C-001, C-002, C-003)
2. ✅ Major 이슈 해결 완료 (M-001~M-005)
3. ⏳ PM Agent 최종 승인 대기
4. → Stage 4: Trading System Architecture Design (별도 문서)
5. → Stage 5: Integrated Specification 작성
6. → Stage 6: Decision Making 및 구현 시작
