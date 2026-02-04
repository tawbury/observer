# DB 및 데이터 마이그레이션 가이드

이 모듈은 수집된 JSONL 아카이브 데이터를 PostgreSQL 데이터베이스로 마이그레이션하고 관리하는 기능을 제공합니다.

## 📂 데이터 디렉토리 구조

```
prj_obs/
├── data/                               # 런타임 데이터 및 아카이브
│   ├── observer/                       # Observer 아카이브 (JSONL)
│   │   ├── scalp/                      # 실시간 체결/1분봉
│   │   └── snapshot/                   # 시장 스냅샷
│   └── assets/                         # 정적 자산 (심볼 리스트 등)
│
├── src/db/
│   ├── schema/                         # SQL 스키마 (PostgreSQL)
│   │   ├── 001_create_scalp_tables.sql
│   │   ├── 002_create_swing_tables.sql
│   │   ├── 003_create_portfolio_tables.sql
│   │   └── 004_create_analysis_tables.sql
│   ├── models.py                       # Pydantic 기반 데이터 모델
│   └── migrate_jsonl_to_db.py          # JSONL -> DB 마이그레이션 도구
│
└── tests/
    ├── test_db_models.py               # 모델 검증 테스트
    └── test_jsonl_migration.py         # 마이그레이션 로직 테스트
```

## 🗄️ 데이터베이스 테이블 구조

### 1. Scalp Tables (실시간 데이터)
- `scalp_ticks`: 실시간 틱 데이터.
- `scalp_1m_bars`: 1분 단위 집계 봉 데이터.
- `scalp_gaps`: 수집 공백 추적.

### 2. Swing Tables (분석 데이터)
- `swing_bars_10m`: 10분 단위 봉 데이터 (분석용).

### 3. Portfolio Tables (운영 데이터)
- 포트폴리오 정책, 타겟 비중, 포지션, 주문 및 실행 기록 관리.

### 4. Analysis Tables (통계/분석 데이터)
- 수집된 데이터의 통계적 분석 및 패턴 식별 결과 저장.

## 🚀 사용 방법

### 1. 데이터베이스 초기화
스키마 파일들을 실생하여 테이블을 생성합니다.
```bash
# PostgreSQL 연결 설정 (환경변수)
export DB_HOST=localhost
export DB_NAME=observer
export DB_USER=postgres
export DB_PASSWORD=your_password

# 초기화 스크립트 실행 (환경에 따라 다름)
python -m src.db.init_db
```

### 2. JSONL 데이터 마이그레이션
`data/observer/` 경로의 JSONL 파일을 읽어 DB에 적재합니다.
```bash
python -m src.db.migrate_jsonl_to_db
```

## 🔧 주요 파일 설명

### models.py
- Pydantic 모델을 사용하여 데이터 유효성을 검증하고 타입 안전성을 보장합니다.
- 데이터베이스 행(Row)과 JSON 레코드 간의 변환을 담당합니다.

### migrate_jsonl_to_db.py
- 아카이브된 JSONL 파일을 효율적으로 읽어 배치(Batch) 단위로 DB에 INSERT합니다.
- `ON CONFLICT` 구문을 사용하여 중복 데이터 삽입을 방지합니다.

## ⚠️ 주의사항
- **데이터 경로**: 기본적으로 `data/observer/` 하위의 구조를 탐색합니다.
- **환경 변수**: DB 연결 정보는 환경 변수를 통해 관리하는 것을 권장합니다 (`.env` 파일 활용).

---
**마지막 업데이트**: 2026-02-04
**버전**: 2.0 (Observer Architecture v2.0 대응)
