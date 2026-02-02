# DB 생성 및 데이터 마이그레이션 가이드

## 📂 데이터 디렉토리 구조

```
prj_obs/
├── data/assets/                        # 📥 소스 JSONL (읽기)
│   ├── scalp/                          # Scalp 소스 (WebSocket 틱/1분봉)
│   │   ├── scalp_ticks_*.jsonl
│   │   └── scalp_1m_bars_*.jsonl
│   └── swing/                          # Swing 소스 (REST 10분봉)
│       └── swing_bars_*.jsonl
│
├── data/                               # 기타 런타임 데이터 (선택)
│
├── src/db/
│   ├── schema/                         # SQL 스키마 파일 (12 테이블)
│   │   ├── 001_create_scalp_tables.sql
│   │   ├── 002_create_swing_tables.sql
│   │   └── 003_create_portfolio_tables.sql
│   ├── models.py                       # Pydantic 모델 (12 테이블)
│   └── migrate_jsonl_to_db.py          # JSONL → DB 마이그레이션
│
├── app/observer/scripts/
│   └── init_db.py                      # DB 초기화 스크립트
│
└── tests/
    ├── test_data/                      # 테스트용 JSONL 데이터
    ├── test_db_models.py               # Pydantic 모델 테스트
    ├── test_jsonl_migration.py         # 마이그레이션 로직 테스트
    └── test_data_structure.py          # 디렉토리 구조 검증
```

## 🗄️ 데이터베이스 테이블 구조

### Scalp Tables (WebSocket 실시간 데이터)
- `scalp_ticks` - 실시간 틱 데이터 (2Hz 주기)
- `scalp_1m_bars` - 1분 집계 봉 데이터
- `scalp_gaps` - 데이터 공백 추적

### Swing Tables (REST API 데이터)
- `swing_bars_10m` - 10분 봉 데이터

### Portfolio Tables (포트폴리오 관리)
- `portfolio_policy` - 포트폴리오 정책
- `target_weights` - 목표 비중
- `portfolio_snapshot` - 스냅샷
- `portfolio_positions` - 포지션
- `rebalance_plan` - 리밸런싱 계획
- `rebalance_orders` - 리밸런싱 주문
- `rebalance_execution` - 실행 기록

### Meta Tables
- `migration_log` - 마이그레이션 이력

## 🚀 사용 방법

### 1. 데이터베이스 초기화

```bash
# PostgreSQL이 실행 중이어야 함 (localhost:5432)
python -m app.observer.scripts.init_db
```

**환경 변수 설정 (선택)**
```bash
# 기본값: localhost:5432, observer DB, postgres 사용자
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=observer
export DB_USER=postgres
export DB_PASSWORD=observer_db_pwd
```

### 2. JSONL 데이터 마이그레이션

```bash
python -m app.observer.src.db.migrate_jsonl_to_db
```

**자동으로 처리되는 데이터 경로:**
- `app/observer/data/observer/scalp/` - Scalp 실제 데이터
- `app/observer/data/observer/swing/` - Swing 실제 데이터
- `tests/test_data/` - 테스트 데이터 (추가)

### 3. 테스트 실행

```bash
# 전체 DB 관련 테스트
pytest tests/test_db_models.py tests/test_jsonl_migration.py tests/test_data_structure.py -v

# Pydantic 모델 테스트만
pytest tests/test_db_models.py -v

# 데이터 구조 검증만
pytest tests/test_data_structure.py -v
```

## 📊 테스트 데이터 생성

```bash
# tests/test_data/ 폴더에 테스트용 JSONL 파일 생성
python tests/generate_test_data.py
```

**생성되는 파일:**
- `scalp_ticks_test.jsonl` (300 lines)
- `scalp_1m_bars_test.jsonl` (90 lines)
- `swing_bars_test.jsonl` (60 lines)

## 🔧 주요 파일 설명

### 1. models.py
12개 테이블에 대응하는 Pydantic 모델:
- 타입 안전성 보장
- 자동 유효성 검증
- JSON 직렬화/역직렬화

### 2. migrate_jsonl_to_db.py
JSONL 파일을 PostgreSQL로 마이그레이션:
- 배치 처리 (기본 1,000개씩)
- 중복 데이터 처리 (ON CONFLICT)
- 자동 경로 탐색

### 3. init_db.py
데이터베이스 자동 초기화:
- 데이터베이스 생성
- 스키마 설정 (12 테이블)
- 테이블 상태 확인

## ⚠️ 주의사항

### 데이터 경로 규칙
- **소스 데이터**: `data/assets/scalp/`, `data/assets/swing/` (읽기)
- **테스트 데이터**: `tests/test_data/` (개발/테스트)
- **처리된 데이터**: `app/observer/data/observer/scalp/`, `app/observer/data/observer/swing/` (선택 사항)

### 파일명 패턴
- Scalp ticks: `*scalp*ticks*.jsonl`
- Scalp 1m bars: `*scalp*1m*.jsonl`
- Swing bars: `*swing*.jsonl` (10분 봉 포함)

### PostgreSQL 연결
- 로컬 개발: `localhost:5432`
- Docker 환경: `DB_HOST` 환경 변수 사용
- OCI 배포: 환경 변수로 자동 연결

## 📝 로그 예시

```
======================================================================
PostgreSQL Database Initialization
======================================================================
DB Host: localhost:5432
DB Name: observer

[Step 1] 데이터베이스 확인 및 생성
✓ 데이터베이스 'observer' 이미 존재

[Step 2] 데이터베이스 연결
✓ PostgreSQL 연결 성공: localhost:5432/observer

[Step 3] 스키마 초기화
  실행 중: 001_create_scalp_tables.sql
✓ 001_create_scalp_tables.sql 실행 완료
  실행 중: 002_create_swing_tables.sql
✓ 002_create_swing_tables.sql 실행 완료
  실행 중: 003_create_portfolio_tables.sql
✓ 003_create_portfolio_tables.sql 실행 완료
✓ 스키마 초기화 완료: 3/3 파일 성공

[Step 4] 테이블 확인
✓ 생성된 테이블: 12개
  ✓ scalp_ticks
  ✓ scalp_1m_bars
  ✓ scalp_gaps
  ✓ swing_bars_10m
  ...

[Step 5] 테이블 상태 요약
======================================================================
데이터베이스 초기화 완료!
======================================================================
데이터베이스: observer
테이블 수: 12/12

테이블별 상태:
  ✓ scalp_ticks              :          0 행
  ✓ scalp_1m_bars            :          0 행
  ...
======================================================================
```

## 🧪 테스트 결과

모든 테스트가 PostgreSQL 연결 없이도 실행 가능:
- ✅ Pydantic 모델 검증 (8 tests)
- ✅ JSONL 파싱 로직 (5 tests)
- ✅ 디렉토리 구조 검증 (5 tests)

**Total: 18 tests passed**

---

**마지막 업데이트**: 2026-01-28
**버전**: 1.0