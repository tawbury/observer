# Phase 04: Trading DB Runner (Reserved Draft)

**목적:** Archive → Trading DB 변환 (자동매매/분석 DB 생성)  
**상태:** 초안 단계, 상세 구현 보류  
**SSoT:** ETL 관련 단일 진실 소스 (예약)

---

## 1. 목적과 범위

### 1.1 목적
- JSONL 아카이브를 자동매매/분석용 DB로 변환
- 전략별 데이터 가공 지원
- 실시간 분석 기반 제공

### 1.2 범위 (하지 않는 것)
- 매매/전략 판단 로직 (ETL은 데이터 가공까지)
- 실시간 트레이딩 실행
- 외부 시스템과의 직접 거래 연동

---

## 2. DB 형태 후보와 선택 기준

### 2.1 DB 형태 후보
| DB 형태 | 장점 | 단점 | 선택 기준 |
|---------|------|------|-----------|
| **SQLite** | 단일 파일, 간단한 운영 | 동시성 제한, 확장성 한계 | 단일 서버, 소규모 |
| **DuckDB** | 분석 쿼리 최적화, 벡터 연산 | OLTP 부적합, 신생 기술 | 분석 워크로드 |
| **PostgreSQL** | 다중 사용자, 고성능, 안정적 | 복잡한 운영, 리소스 많음 | 다중 사용자, 대규모 |

### 2.2 선택 기준
1. **운영 복잡도:** 단일 서버 → SQLite
2. **분석 성능:** 쿼리 최적화 중요 → DuckDB
3. **동시성:** 다중 접속 필요 → PostgreSQL

### 2.3 초기 추천
- **Phase 04.1:** SQLite로 시작 (단순성)
- **Phase 04.2:** 필요시 DuckDB로 전환 (분석 성능)
- **Phase 04.3:** 대규모 시 PostgreSQL로 확장

---

## 3. Idempotency 키 (중복 방지 개념)

### 3.1 중복 방지 전략
- **기본 키:** `session_id + timestamp + symbol`
- **추가 키:** `provider + data_type`
- **처리:** UPSERT (INSERT ON CONFLICT UPDATE)

### 3.2 Idempotency 키 구조
```sql
-- 예시: scalp_ticks 테이블
PRIMARY KEY (session_id, symbol, event_time)
UNIQUE (provider, symbol, event_time)
```

### 3.3 중복 처리 로직
```python
def ensure_idempotency(record):
    key = f"{record.session_id}_{record.symbol}_{record.event_time}"
    if exists_in_db(key):
        return update_existing(key, record)
    else:
        return insert_new(key, record)
```

---

## 4. Watermark/증분 처리 개념

### 4.1 Watermark 정의
- **목적:** 마지막 처리 위치 추적
- **기준:** timestamp 또는 sequence_id
- **저장:** 별도 watermark 테이블

### 4.2 Watermark 테이블 구조
```sql
CREATE TABLE etl_watermark (
    source_type VARCHAR(50) PRIMARY KEY,  -- swing, scalp, system
    last_processed_ts TIMESTAMPTZ,
    last_processed_file VARCHAR(255),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.3 증분 처리 흐름
```
1. Watermark 조회 (마지막 처리 시각)
2. 아카이브 파일 스캔 (Watermark 이후)
3. 레코드 변환 및 적재
4. Watermark 업데이트
5. 다음 배치 대기
```

---

## 5. 전략별 가공 경계 (ETL 책임 범위)

### 5.1 ETL 책임 (하는 것)
- **데이터 정제:** 결측치 처리, 이상치 필터링
- **구조 변환:** JSONL → 관계형 DB
- **기본 집계:** OHLCV, 통계량
- **품질 관리:** 데이터 검증, 품질 플래그
- **메타데이터:** 처리 시각, 소스 추적

### 5.2 ETL 책임 외 (하지 않는 것)
- **전략 판단:** 매수/매도 신호 생성
- **리스크 평가:** 포지션 사이징, 손절 설정
- **포트폴리오 최적화:** 자산 배분, 리밸런싱
- **실시간 트레이딩:** 주문 실행, 체결 관리

### 5.3 경계 명확화
| 영역 | ETL 책임 | 외부 책임 |
|------|-----------|-----------|
| **데이터** | 정제/변환/적재 | 전략 판단 |
| **시간** | 증분 처리/워터마크 | 실시간 실행 |
| **품질** | 검증/플래깅 | 리스크 평가 |
| **구조** | 스키마 관리 | 포트폴리오 운용 |

---

## 6. Runner 모드 설계

### 6.1 실행 모드
```bash
# ETL 모드 실행
observer etl --source=archive --target=trading_db

# 특정 일자 처리
observer etl --date=2026-01-14 --incremental

# 전체 재처리
observer etl --full-refresh --confirm
```

### 6.2 ETL 파이프라인 구조
```python
class TradingETLPipeline:
    def extract_from_archive(self, date: str) -> List[EnrichedRecord]
    def transform_for_trading(self, records: List[EnrichedRecord]) -> List[TradingRecord]
    def load_to_trading_db(self, trading_records: List[TradingRecord])
    def verify_etl_success(self, date: str) -> bool
    def update_watermark(self, source_type: str, timestamp: datetime)
```

---

## 7. 데이터 스키마 개요

### 7.1 핵심 테이블
| 테이블 | 용도 | 키 |
|--------|------|-----|
| `scalp_ticks` | 고빈도 틱 데이터 | (symbol, event_time) |
| `swing_bars_10m` | 10분봉 데이터 | (symbol, bar_time) |
| `eod_prices` | 일별 종가 | (symbol, trade_date) |
| `market_universe` | 시장 종목 목록 | (symbol, market, date) |
| `etl_watermark` | 처리 위치 추적 | (source_type) |

### 7.2 공통 메타 필드
```sql
-- 모든 테이블 공통
schema_version VARCHAR(10) DEFAULT '1.0',
etl_timestamp TIMESTAMPTZ DEFAULT NOW(),
source_file VARCHAR(255),
quality_flag VARCHAR(20) DEFAULT 'normal',
session_id VARCHAR(50)
```

---

## 8. 성능 및 운영 고려사항

### 8.1 배치 처리
- **배치 크기:** 10,000 레코드 단위
- **처리 주기:** 5분 또는 1시간
- **병렬 처리:** 마켓별/종목별 분리

### 8.2 모니터링 지표
- **처리량:** records/second
- **지연:** archive → DB 시간차
- **품질:** 결측률, 중복률
- **리소스:** CPU, 메모리, 디스크

### 8.3 장애 대응
- **재처리:** 특정 일자 재실행
- **부분 실패:** 레코드 단위 롤백
- **데이터 일관성:** 트랜잭션 보장

---

## 9. 구현 우선순위 (예약)

### 9.1 Phase 04.1: SQLite 기반 ETL
1. 기본 ETL 파이프라인 구현
2. SQLite 스키마 설계
3. Watermark 기반 증분 처리
4. 기본 모니터링

### 9.2 Phase 04.2: 성능 최적화
1. 배치 처리 최적화
2. 인덱스 튜닝
3. 병렬 처리 도입
4. DuckDB 전환 고려

### 9.3 Phase 04.3: 고급 기능
1. 다중 마켓 지원
2. 실시간 ETL
3. PostgreSQL 확장
4. 고급 모니터링

---

## 10. 현재 상태 및 다음 단계

### 10.1 현재 상태
- **Phase 03:** Archive 생성 완료 (로그 미작동 문제 해결 필요)
- **Phase 04:** 설계 단계, 구현 보류

### 10.2 선행 조건
1. Phase 03 안정화 (로그 생성 정상화)
2. 아카이브 데이터 축적 (최소 1주일)
3. DB 형태 최종 결정

### 10.3 다음 단계
1. **즉시:** Phase 03 문제 해결 집중
2. **단기:** SQLite 기반 ETL 프로토타이핑
3. **중기:** 전체 ETL 파이프라인 구현

---

**SSoT 선언 (예약):** 이 문서는 Observer ETL의 단일 진실 소스가 될 것입니다. 모든 ETL 관련 구현은 이 문서를 기준으로 합니다.
