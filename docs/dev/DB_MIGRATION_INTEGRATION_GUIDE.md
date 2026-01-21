# DB 마이그레이션 및 통합 가이드 (Phase 13)

## 📋 개요

이 문서는 현재 구현된 **Phase 5-12 (JSONL 파일 기반)** 데이터 구조를 PostgreSQL DB로 마이그레이션하기 위한 적용 가능성 분석 및 보완 가이드입니다.

**작성일**: 2026-01-22  
**대상**: Phase 13 (Database Ingestion Layer)  
**상태**: 설계 문서 (Implementation Ready)

---

## 1️⃣ 현재 데이터 구조 분석

### 1.1 Track A (Swing) - REST Polling 10분 주기

**저장 위치**: `config/observer/swing/YYYYMMDD_HHMM.jsonl`

**현재 JSONL 레코드 구조**:
```json
{
  "ts": "2026-01-22T09:31:05.200Z",
  "session": "track_a_session",
  "dataset": "track_a_swing",
  "market": "kr_stocks",
  "symbol": "005930",
  "price": {
    "open": 70000,
    "high": 72000,
    "low": 69500,
    "close": 71500
  },
  "volume": 1234567,
  "bid_price": 71450,
  "ask_price": 71500,
  "source": "kis"
}
```

**필드 매핑 분석**:
| JSONL 필드 | 타입 | DB 테이블 | DB 컬럼 | 호환성 |
|-----------|------|---------|--------|--------|
| ts | ISO8601 | swing_bars_10m | bar_time | ✅ 맵핑 가능 |
| symbol | string | swing_bars_10m | symbol | ✅ 정확 일치 |
| price.open | float | swing_bars_10m | open | ✅ 정확 일치 |
| price.high | float | swing_bars_10m | high | ✅ 정확 일치 |
| price.low | float | swing_bars_10m | low | ✅ 정확 일치 |
| price.close | float | swing_bars_10m | close | ✅ 정확 일치 |
| volume | int | swing_bars_10m | volume | ✅ 정확 일치 |
| bid_price | float | swing_bars_10m | - | ⚠️ 스키마에 없음 |
| ask_price | float | swing_bars_10m | - | ⚠️ 스키마에 없음 |
| session | string | swing_bars_10m | session_id | ✅ 맵핑 가능 |

**분석 결과**: 
- ✅ **적용 가능** (Core 필드 모두 일치)
- ⚠️ **추가 필드**: bid_price, ask_price 처리 필요
  - 옵션 1: 신규 컬럼 추가 (swing_bars_10m 수정)
  - 옵션 2: 별도 테이블 (swing_bid_ask) 생성
  - **추천**: 옵션 1 (단순성)

---

### 1.2 Track B (Scalp) - WebSocket 실시간 2Hz

**저장 위치**: `config/observer/scalp/YYYYMMDD_HHMM.jsonl`

**예상 JSONL 레코드 구조** (WebSocket 틱 데이터):
```json
{
  "ts": "2026-01-22T09:31:05.123Z",
  "event_time": "2026-01-22T09:31:05.120Z",
  "symbol": "005930",
  "bid_price": 71450,
  "ask_price": 71500,
  "bid_size": 100,
  "ask_size": 50,
  "last_price": 71475,
  "volume": 10,
  "session_id": "track_b_session",
  "mitigation_level": 0,
  "quality_flag": "normal"
}
```

**필드 매핑 분석**:
| JSONL 필드 | 타입 | DB 테이블 | DB 컬럼 | 호환성 |
|-----------|------|---------|--------|--------|
| event_time | ISO8601 | scalp_ticks | event_time | ✅ 정확 일치 |
| symbol | string | scalp_ticks | symbol | ✅ 정확 일치 |
| bid_price | float | scalp_ticks | bid_price | ✅ 정확 일치 |
| ask_price | float | scalp_ticks | ask_price | ✅ 정확 일치 |
| bid_size | int | scalp_ticks | bid_size | ✅ 정확 일치 |
| ask_size | int | scalp_ticks | ask_size | ✅ 정확 일치 |
| last_price | float | scalp_ticks | last_price | ✅ 정확 일치 |
| volume | int | scalp_ticks | volume | ✅ 정확 일치 |
| session_id | string | scalp_ticks | session_id | ✅ 정확 일치 |
| mitigation_level | int | scalp_ticks | mitigation_level | ✅ 정확 일치 |
| quality_flag | string | scalp_ticks | quality_flag | ✅ 정확 일치 |

**분석 결과**: 
- ✅ **완벽 호환** (모든 필드 일치)
- **추가 필드 없음**
- **바로 적용 가능** (마이그레이션 시 데이터 변환 불필요)

---

### 1.3 Gap Ledger (시스템 이벤트)

**저장 위치**: `logs/system/gap_YYYYMMDD.jsonl`

**현재 JSONL 레코드 구조**:
```json
{
  "timestamp": "2026-01-22T09:31:05.123Z",
  "gap_start_ts": "2026-01-22T09:31:00.000Z",
  "gap_end_ts": "2026-01-22T09:31:05.000Z",
  "gap_seconds": 5,
  "scope": "scalp",
  "reason": "ws_disconnect",
  "session_id": "track_b_session"
}
```

**필드 매핑 분석**:
| JSONL 필드 | 타입 | DB 테이블 | DB 컬럼 | 호환성 |
|-----------|------|---------|--------|--------|
| gap_start_ts | ISO8601 | scalp_gaps | gap_start_ts | ✅ 정확 일치 |
| gap_end_ts | ISO8601 | scalp_gaps | gap_end_ts | ✅ 정확 일치 |
| gap_seconds | int | scalp_gaps | gap_seconds | ✅ 정확 일치 |
| scope | string | scalp_gaps | scope | ✅ 정확 일치 |
| reason | string | scalp_gaps | reason | ✅ 정확 일치 |
| session_id | string | scalp_gaps | session_id | ✅ 정확 일치 |

**분석 결과**: 
- ✅ **완벽 호환** (모든 필드 일치)
- **바로 적용 가능**

---

## 2️⃣ DB 스키마 적용 가능성 검증

### 2.1 Scalp 테이블 ✅ 준비 완료

#### scalp_ticks
```sql
CREATE TABLE scalp_ticks (
    id              BIGSERIAL PRIMARY KEY,
    symbol          VARCHAR(20) NOT NULL,
    event_time      TIMESTAMPTZ NOT NULL,
    bid_price       NUMERIC(15,4),
    ask_price       NUMERIC(15,4),
    bid_size        BIGINT,
    ask_size        BIGINT,
    last_price      NUMERIC(15,4),
    volume          BIGINT,
    session_id      VARCHAR(50) NOT NULL,
    schema_version  VARCHAR(10) DEFAULT '1.0',
    receive_time    TIMESTAMPTZ DEFAULT NOW(),
    mitigation_level INT DEFAULT 0,
    quality_flag    VARCHAR(20) DEFAULT 'normal'
);

CREATE INDEX idx_scalp_ticks_symbol_time ON scalp_ticks(symbol, event_time);
CREATE INDEX idx_scalp_ticks_session ON scalp_ticks(session_id);
```

**적용 상태**: ✅ **즉시 적용 가능**
- JSONL 필드와 완벽 일치
- 인덱스 전략 적절 (symbol+time: 범위 쿼리 최적화)

---

#### scalp_1m_bars
```sql
CREATE TABLE scalp_1m_bars (
    symbol          VARCHAR(20) NOT NULL,
    bar_time        TIMESTAMPTZ NOT NULL,
    open            NUMERIC(15,4),
    high            NUMERIC(15,4),
    low             NUMERIC(15,4),
    close           NUMERIC(15,4),
    volume          BIGINT,
    coverage_ratio  FLOAT,
    session_id      VARCHAR(50) NOT NULL,
    schema_version  VARCHAR(10) DEFAULT '1.0',
    mitigation_level INT DEFAULT 0,
    quality_flag    VARCHAR(20) DEFAULT 'normal',
    PRIMARY KEY (symbol, bar_time)
);

CREATE INDEX idx_scalp_1m_bars_session ON scalp_1m_bars(session_id);
```

**적용 상태**: ✅ **즉시 적용 가능**
- JSONL 틱 데이터를 1분 봉으로 그룹핑 후 저장
- coverage_ratio: JSONL에 없음 (DB 계산 필요)
  - 계산: (실제 데이터 포인트 수) / (이론적 최대 포인트 수 at 2Hz) 

---

#### scalp_gaps
```sql
CREATE TABLE scalp_gaps (
    id              SERIAL PRIMARY KEY,
    gap_start_ts    TIMESTAMPTZ NOT NULL,
    gap_end_ts      TIMESTAMPTZ NOT NULL,
    gap_seconds     INT NOT NULL,
    scope           VARCHAR(20),
    reason          VARCHAR(100),
    session_id      VARCHAR(50) NOT NULL
);

CREATE INDEX idx_scalp_gaps_session ON scalp_gaps(session_id);
CREATE INDEX idx_scalp_gaps_time ON scalp_gaps(gap_start_ts);
```

**적용 상태**: ✅ **즉시 적용 가능**
- JSONL 필드와 완벽 일치

---

### 2.2 Swing 테이블 ⚠️ 스키마 수정 필요

#### swing_bars_10m (수정 필요)
```sql
-- 원본 스키마
CREATE TABLE swing_bars_10m (
    symbol          VARCHAR(20) NOT NULL,
    bar_time        TIMESTAMPTZ NOT NULL,
    open            NUMERIC(15,4),
    high            NUMERIC(15,4),
    low             NUMERIC(15,4),
    close           NUMERIC(15,4),
    volume          BIGINT,
    session_id      VARCHAR(50) NOT NULL,
    schema_version  VARCHAR(10) DEFAULT '1.0',
    mitigation_level INT DEFAULT 0,
    quality_flag    VARCHAR(20) DEFAULT 'normal',
    PRIMARY KEY (symbol, bar_time)
);

-- 🔧 보완: bid/ask 필드 추가
CREATE TABLE swing_bars_10m (
    symbol          VARCHAR(20) NOT NULL,
    bar_time        TIMESTAMPTZ NOT NULL,
    open            NUMERIC(15,4),
    high            NUMERIC(15,4),
    low             NUMERIC(15,4),
    close           NUMERIC(15,4),
    volume          BIGINT,
    bid_price       NUMERIC(15,4),      -- ✨ 추가
    ask_price       NUMERIC(15,4),      -- ✨ 추가
    session_id      VARCHAR(50) NOT NULL,
    schema_version  VARCHAR(10) DEFAULT '1.0',
    mitigation_level INT DEFAULT 0,
    quality_flag    VARCHAR(20) DEFAULT 'normal',
    PRIMARY KEY (symbol, bar_time)
);

CREATE INDEX idx_swing_10m_session ON swing_bars_10m(session_id);
```

**적용 상태**: ⚠️ **스키마 수정 후 적용 가능**
- **필요 수정**: bid_price, ask_price 컬럼 추가
- **대안**: bid/ask를 별도 테이블로 분리 (정규화)
  - 권장 사항: 추가하기 (단순성 & 성능)

---

#### eod_prices (구현 불필요, 추후)
```sql
-- 이 테이블은 현재 Phase에서 사용 안 함
-- Phase 15+ 전략 수립 단계에서 구현 고려
CREATE TABLE eod_prices (
    symbol          VARCHAR(20) NOT NULL,
    trade_date      DATE NOT NULL,
    open            NUMERIC(15,4),
    high            NUMERIC(15,4),
    low             NUMERIC(15,4),
    close           NUMERIC(15,4),
    volume          BIGINT,
    prev_close      NUMERIC(15,4),
    schema_version  VARCHAR(10) DEFAULT '1.0',
    PRIMARY KEY (symbol, trade_date)
);

CREATE INDEX idx_eod_prices_date ON eod_prices(trade_date);
```

**적용 상태**: ⏸️ **현재 불필요** (미래 확장용)

---

### 2.3 Portfolio 테이블 ⏸️ 미구현 (Phase 15+)

**현재 상태**: Portfolio 리밸런싱 기능이 Phase 5-12에서 구현되지 않음

**스키마 완성도**: ✅ 설계 완료, 구현 미필요

**적용 시기**: Phase 14+ (트레이딩 로직 추가 시)

---

## 3️⃣ 마이그레이션 경로

### 3.1 Phase 13 태스크 구성 (권장)

#### Task 13.1: PostgreSQL 스키마 생성
- **범위**: scalp_ticks, scalp_1m_bars, scalp_gaps, swing_bars_10m (수정)
- **산출물**: 
  - `migrations/001_create_core_tables.sql`
  - Alembic 마이그레이션 스크립트
- **검증**: `pytest app/obs_deploy/app/src/db/test_schema_creation.py`

#### Task 13.2: JSONL → DB 데이터 변환 레이어
- **범위**: JSONL 파서 → DB 삽입
- **모듈**: `app/obs_deploy/app/src/db/ingestion/`
- **구현 항목**:
  - `scalp_ticks_ingester.py`: JSONL → scalp_ticks
  - `scalp_1m_bars_aggregator.py`: ticks → 1분 봉
  - `scalp_gaps_ingester.py`: JSONL → scalp_gaps
  - `swing_bars_ingester.py`: JSONL → swing_bars_10m
- **성능**: 배치 처리 (1,000 records/batch)

#### Task 13.3: 백필 (Back-fill) - 과거 JSONL 데이터
- **범위**: config/observer/swing/, scalp/ 전체 파일 읽기
- **모듈**: `app/obs_deploy/app/src/db/backfill/`
- **구현 항목**:
  - `backfill_runner.py`: 병렬 처리 (asyncio)
  - 진행률 추적 (checksum 기반)
  - 재시도 로직
- **예상 시간**: 데이터 크기에 따라 1-2시간

#### Task 13.4: DB 쿼리 API
- **범위**: 고수준 쿼리 인터페이스
- **모듈**: `app/obs_deploy/app/src/db/queries/`
- **구현 항목**:
  ```python
  # 예시
  async def get_latest_bars(symbol: str, limit: int = 100) -> List[SwingBar]:
      """최근 100개 10분봉 조회"""
      pass
  
  async def get_ticks_in_range(symbol: str, start_ts: datetime, end_ts: datetime) -> List[ScalpTick]:
      """시간 범위별 틱 조회"""
      pass
  
  async def count_gaps(scope: str, start_date: date, end_date: date) -> int:
      """기간별 갭 발생 횟수"""
      pass
  ```

---

### 3.2 데이터 흐름 다이어그램

```
Phase 12 (현재)
├── Track A Collector
│   └── JSONL: config/observer/swing/YYYYMMDD_HHMM.jsonl ✅
├── Track B Collector
│   └── JSONL: config/observer/scalp/YYYYMMDD_HHMM.jsonl ✅
└── Gap Detector
    └── JSONL: logs/system/gap_YYYYMMDD.jsonl ✅

Phase 13 (DB Ingestion) 🆕
├── Task 13.1: PostgreSQL 스키마 생성
│   ├── scalp_ticks
│   ├── scalp_1m_bars
│   ├── scalp_gaps
│   └── swing_bars_10m (수정: +bid_price, +ask_price)
├── Task 13.2: JSONL → DB 변환 레이어
│   ├── ScalpTicksIngester (실시간 수신 시)
│   ├── SwingBarsIngester (10분 주기)
│   └── GapsIngester (이벤트 기반)
├── Task 13.3: Back-fill (과거 데이터)
│   └── 기존 JSONL 파일 → DB 로드
└── Task 13.4: DB 쿼리 API
    ├── get_latest_bars()
    ├── get_ticks_in_range()
    └── count_gaps()

Phase 13+ (병렬 진행 가능)
├── 모니터링: Prometheus → DB 메트릭 저장
├── 분석: SQL 기반 리포팅
└── 포트폴리오: portfolio_* 테이블 (필요시)
```

---

## 4️⃣ 필수 보완 사항

### 4.1 선택적 컬럼 추가 (swing_bars_10m)

**현재 스키마**:
```sql
CREATE TABLE swing_bars_10m (
    symbol          VARCHAR(20) NOT NULL,
    bar_time        TIMESTAMPTZ NOT NULL,
    open            NUMERIC(15,4),
    high            NUMERIC(15,4),
    low             NUMERIC(15,4),
    close           NUMERIC(15,4),
    volume          BIGINT,
    session_id      VARCHAR(50) NOT NULL,
    ...
);
```

**보완 옵션 1: 직접 추가 (권장)** ✅
```sql
ALTER TABLE swing_bars_10m ADD COLUMN bid_price NUMERIC(15,4);
ALTER TABLE swing_bars_10m ADD COLUMN ask_price NUMERIC(15,4);
```

**보완 옵션 2: 별도 테이블 분리**
```sql
CREATE TABLE swing_bid_ask (
    symbol          VARCHAR(20) NOT NULL,
    bar_time        TIMESTAMPTZ NOT NULL,
    bid_price       NUMERIC(15,4),
    ask_price       NUMERIC(15,4),
    PRIMARY KEY (symbol, bar_time),
    FOREIGN KEY (symbol, bar_time) REFERENCES swing_bars_10m
);
```

**선택 근거**:
- **옵션 1 선택**: 단순 쿼리, 조인 오버헤드 없음
- 데이터 크기: 추가 2 컬럼 = ~32 bytes/row (무시할 수준)

---

### 4.2 Coverage Ratio 계산 (scalp_1m_bars)

JSONL의 틱 데이터를 1분 봉으로 집계할 때 coverage_ratio 계산:

```python
# 예시 계산 로직
coverage_ratio = actual_ticks / theoretical_ticks

# 이론적 틱 개수 (2Hz, 1분 = 60초)
theoretical_ticks = 60 * 2  # 120

# 실제 틱 개수 (해당 1분 동안 수집된 틱)
actual_ticks = len([tick for tick in ticks if start_ts <= tick.event_time < end_ts])

coverage_ratio = actual_ticks / theoretical_ticks  # 0.0~1.0
```

**용도**: 
- 데이터 품질 모니터링
- Gap 감지 (coverage_ratio < 0.8 → 경고)

---

### 4.3 Performance Indexing 전략

**현재 인덱스**:
```sql
-- scalp_ticks
CREATE INDEX idx_scalp_ticks_symbol_time ON scalp_ticks(symbol, event_time);
CREATE INDEX idx_scalp_ticks_session ON scalp_ticks(session_id);

-- scalp_1m_bars
CREATE INDEX idx_scalp_1m_bars_session ON scalp_1m_bars(session_id);

-- scalp_gaps
CREATE INDEX idx_scalp_gaps_session ON scalp_gaps(session_id);
CREATE INDEX idx_scalp_gaps_time ON scalp_gaps(gap_start_ts);

-- swing_bars_10m
CREATE INDEX idx_swing_10m_session ON swing_bars_10m(session_id);
```

**추가 권장 인덱스**:
```sql
-- scalp_ticks: 시간 범위 쿼리 최적화
CREATE INDEX idx_scalp_ticks_time ON scalp_ticks(event_time DESC);

-- swing_bars_10m: 시간 범위 쿼리 최적화
CREATE INDEX idx_swing_10m_time ON swing_bars_10m(bar_time DESC);

-- 세션별 시간 범위 (복합)
CREATE INDEX idx_scalp_ticks_session_time ON scalp_ticks(session_id, event_time);
CREATE INDEX idx_swing_10m_session_time ON swing_bars_10m(session_id, bar_time);
```

**큰 테이블 (scalp_ticks) 성능 고려**:
```sql
-- 시계열 최적화 (TimescaleDB 추천)
SELECT create_hypertable('scalp_ticks', 'event_time', if_not_exists => TRUE);
SELECT add_compression_policy('scalp_ticks', INTERVAL '7 days');
```

---

## 5️⃣ 구현 체크리스트

### Phase 13.1: 스키마 생성

- [ ] PostgreSQL 설치 및 DB 초기화
- [ ] `migrations/001_create_core_tables.sql` 작성
  - [ ] scalp_ticks 테이블
  - [ ] scalp_1m_bars 테이블 (coverage_ratio 포함)
  - [ ] scalp_gaps 테이블
  - [ ] swing_bars_10m 테이블 (bid_price, ask_price 추가)
  - [ ] 모든 인덱스
- [ ] Alembic 설정 (마이그레이션 관리)
- [ ] 스키마 테스트 (pytest)

### Phase 13.2: 데이터 변환 레이어

- [ ] `ingestion/scalp_ticks_ingester.py` 구현
- [ ] `ingestion/scalp_1m_bars_aggregator.py` 구현
- [ ] `ingestion/scalp_gaps_ingester.py` 구현
- [ ] `ingestion/swing_bars_ingester.py` 구현
- [ ] 배치 처리 로직 (1,000 records/batch)
- [ ] 에러 핸들링 및 재시도 로직
- [ ] 단위 테스트 (각 ingester)

### Phase 13.3: Back-fill

- [ ] `backfill/backfill_runner.py` 구현
- [ ] 병렬 처리 (asyncio, max 10 concurrent)
- [ ] 진행률 추적 (체크포인트)
- [ ] 재시도 로직 (3회, exponential backoff)
- [ ] 로깅 (성공/실패 통계)
- [ ] Back-fill 검증 테스트

### Phase 13.4: 쿼리 API

- [ ] `queries/swing_queries.py` 구현
  - [ ] get_latest_bars(symbol, limit)
  - [ ] get_bars_in_range(symbol, start_ts, end_ts)
- [ ] `queries/scalp_queries.py` 구현
  - [ ] get_latest_ticks(symbol, limit)
  - [ ] get_ticks_in_range(symbol, start_ts, end_ts)
  - [ ] get_1m_bars(symbol, start_ts, end_ts)
- [ ] `queries/gap_queries.py` 구현
  - [ ] count_gaps(scope, start_date, end_date)
  - [ ] get_critical_gaps(start_date, end_date)
- [ ] 통합 테스트

---

## 6️⃣ 마이그레이션 영향 분석

### 6.1 변경 영향도

| 컴포넌트 | 영향 | 수정 필요 | 우선순위 |
|---------|------|---------|---------|
| Track A Collector | Dual write (JSONL + DB) | ⚠️ 필요 | HIGH |
| Track B Collector | Dual write (JSONL + DB) | ⚠️ 필요 | HIGH |
| Gap Detector | Dual write (JSONL + DB) | ⚠️ 필요 | HIGH |
| Log Rotation | 파일 기반 계속 유지 | ❌ 불필요 | - |
| Backup Manager | JSONL 백업 계속 | ❌ 불필요 | - |
| Monitoring | Prometheus 계속 | ❌ 불필요 | - |
| Test 코드 | DB 모의 객체 추가 | ⚠️ 필요 | MEDIUM |

### 6.2 성능 영향

**예상 지표** (단위: ms/record):
| 작업 | JSONL | DB | 차이 |
|-----|------|-----|------|
| 단일 레코드 쓰기 | 0.5 | 2-5 | +3-5x (배치로 상쇄 가능) |
| 배치 쓰기 (1000) | 500 | 100-200 | -50-80% ✅ |
| 범위 쿼리 (1일) | 100ms (파일 읽기) | 5-10ms (DB 쿼리) | -90% ✅ |

**권장**: 배치 쓰기 사용 → 성능 향상

---

## 7️⃣ 구현 예시 코드

### 7.1 scalp_ticks_ingester.py 스켈레톤

```python
# app/obs_deploy/app/src/db/ingestion/scalp_ticks_ingester.py

from dataclasses import dataclass
from typing import Dict, Any, List
import asyncpg
from datetime import datetime

@dataclass
class ScalpTick:
    symbol: str
    event_time: datetime
    bid_price: float
    ask_price: float
    bid_size: int
    ask_size: int
    last_price: float
    volume: int
    session_id: str
    mitigation_level: int = 0
    quality_flag: str = "normal"

class ScalpTicksIngester:
    def __init__(self, db_pool: asyncpg.Pool):
        self.pool = db_pool
    
    async def insert_batch(self, ticks: List[ScalpTick]) -> int:
        """
        배치 삽입 (1,000 records/batch)
        
        Returns: 삽입된 레코드 수
        """
        async with self.pool.acquire() as conn:
            # 배치 삽입 쿼리
            rows = [
                (
                    tick.symbol,
                    tick.event_time,
                    tick.bid_price,
                    tick.ask_price,
                    tick.bid_size,
                    tick.ask_size,
                    tick.last_price,
                    tick.volume,
                    tick.session_id,
                    tick.mitigation_level,
                    tick.quality_flag,
                )
                for tick in ticks
            ]
            
            result = await conn.executemany(
                """
                INSERT INTO scalp_ticks (
                    symbol, event_time, bid_price, ask_price,
                    bid_size, ask_size, last_price, volume,
                    session_id, mitigation_level, quality_flag
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """,
                rows
            )
            
            return len(rows)
    
    @staticmethod
    def from_jsonl_record(raw: Dict[str, Any]) -> ScalpTick:
        """JSONL 레코드 → ScalpTick 변환"""
        return ScalpTick(
            symbol=raw["symbol"],
            event_time=datetime.fromisoformat(raw["event_time"].replace("Z", "+00:00")),
            bid_price=raw["bid_price"],
            ask_price=raw["ask_price"],
            bid_size=raw["bid_size"],
            ask_size=raw["ask_size"],
            last_price=raw["last_price"],
            volume=raw["volume"],
            session_id=raw["session_id"],
            mitigation_level=raw.get("mitigation_level", 0),
            quality_flag=raw.get("quality_flag", "normal"),
        )
```

### 7.2 Back-fill Runner 스켈레톤

```python
# app/obs_deploy/app/src/db/backfill/backfill_runner.py

import asyncio
from pathlib import Path
from typing import List
import asyncpg
import json

class BackfillRunner:
    def __init__(self, db_pool: asyncpg.Pool, jsonl_root: Path):
        self.pool = db_pool
        self.jsonl_root = jsonl_root
    
    async def run(self) -> None:
        """모든 JSONL 파일을 DB로 로드"""
        
        # config/observer/scalp/ 스캔
        scalp_files = list(self.jsonl_root.glob("scalp/**/*.jsonl"))
        swing_files = list(self.jsonl_root.glob("swing/**/*.jsonl"))
        gap_files = list(self.jsonl_root.glob("system/**/gap_*.jsonl"))
        
        print(f"Found {len(scalp_files)} scalp files, {len(swing_files)} swing files, {len(gap_files)} gap files")
        
        # 병렬 처리 (max 10 concurrent)
        sem = asyncio.Semaphore(10)
        
        async def process_file(filepath: Path):
            async with sem:
                count = await self._process_scalp_file(filepath)
                print(f"Loaded {count} records from {filepath.name}")
        
        await asyncio.gather(
            *[process_file(f) for f in scalp_files],
            *[process_file(f) for f in swing_files],
            *[process_file(f) for f in gap_files],
        )
    
    async def _process_scalp_file(self, filepath: Path) -> int:
        """JSONL 파일 → scalp_ticks 테이블"""
        from .scalp_ticks_ingester import ScalpTicksIngester, ScalpTick
        
        ingester = ScalpTicksIngester(self.pool)
        batch = []
        count = 0
        
        with filepath.open("r", encoding="utf-8") as f:
            for line in f:
                raw = json.loads(line)
                tick = ScalpTick.from_jsonl_record(raw)
                batch.append(tick)
                
                if len(batch) >= 1000:
                    count += await ingester.insert_batch(batch)
                    batch = []
        
        if batch:
            count += await ingester.insert_batch(batch)
        
        return count
```

---

## 8️⃣ 비용 추정

### 8.1 개발 시간

| Task | 예상 기간 | 의존성 |
|------|---------|-------|
| 13.1 스키마 생성 | 2-3일 | PostgreSQL 설치 |
| 13.2 데이터 변환 | 3-4일 | 13.1 완료 |
| 13.3 Back-fill | 3-4일 | 13.2 완료 |
| 13.4 쿼리 API | 2-3일 | 13.3 완료 |
| **총합** | **10-14일** | **순차 진행** |

### 8.2 인프라 비용

| 항목 | 예상 | 비고 |
|-----|------|------|
| PostgreSQL 라이선스 | $0 | 오픈소스 |
| 서버 (8GB RAM, 200GB SSD) | $100-200/월 | AWS RDS 또는 온프레미스 |
| 백업 스토리지 | $20-50/월 | 주간 백업 |
| 모니터링 도구 | $0-50/월 | pgAdmin (무료) + Prometheus |

---

## 9️⃣ 리스크 및 완화 방안

### Risk 1: 데이터 무결성 (Back-fill)
**영향**: 부분 로드, 중복 데이터  
**확률**: 중간  
**대응**:
- 체크포인트 기반 재시작
- 파일 해시 검증 (SHA256)
- 트랜잭션 롤백 능력

### Risk 2: 성능 저하 (Large scalp_ticks)
**영향**: 쿼리 응답 시간 증가  
**확률**: 중간 (데이터 증가 시)  
**대응**:
- TimescaleDB 사용 (시계열 최적화)
- 파티셔닝 (월/주 단위)
- 읽기 전용 레플리카

### Risk 3: Dual-write 장애 (JSONL + DB)
**영향**: 데이터 동기화 불일치  
**확률**: 낮음  
**대응**:
- 이벤트 기반 아키텍처 (EventBus 활용)
- 보상 트랜잭션 (Compensation pattern)
- 모니터링 (로그 vs DB 비교)

---

## 🔟 결론

### 적용 가능성: ✅ **높음** (85-90%)

**준비 완료 (즉시 구현 가능)**:
- ✅ scalp_ticks (완벽 호환)
- ✅ scalp_gaps (완벽 호환)
- ✅ swing_bars_10m (스키마 수정 후)
- ✅ scalp_1m_bars (coverage_ratio 계산 필요)

**보완 필요 (경미)**:
- ⚠️ swing_bars_10m에 bid_price, ask_price 추가
- ⚠️ coverage_ratio 계산 로직
- ⚠️ Dual-write 아키텍처 설계

**미래 계획 (Phase 15+)**:
- ⏸️ portfolio_* 테이블 (리밸런싱 기능 추가 시)
- ⏸️ eod_prices (일별 종가 수집 추가 시)

---

## 📚 참고 문서

- [Observer Architecture v0.3](docs/dev/archi/obs_architecture.md#214-데이터-스키마-정의)
- [Data Pipeline Architecture](docs/dev/archi/data_pipeline_architecture_observer_v1.0.md)
- [Phase 12 Completion Report](docs/PHASE_12_FINAL_REPORT.md)
- [Gap Detection Specification](docs/dev/archi/gap_detection_specification_v1.0.md)

---

**작성일**: 2026-01-22  
**버전**: 1.0.0  
**상태**: Design Review Ready
