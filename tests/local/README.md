# Track A/B 로컬-Docker 통합 테스트 가이드

## 테스트 구조

```
tests/
├── local/
│   ├── test_track_ab_config_creation.py   # Phase 1.1: 경로 함수 테스트
│   ├── test_track_ab_mock.py              # Phase 1.2-1.3: Mock 기반 테스트
│   ├── test_track_ab_file_verification.py # Phase 2: 파일 생성 검증
│   ├── test_track_a_local.py              # Track A 로컬 실행 (KIS API 필요)
│   └── test_track_b_local.py              # Track B 로컬 실행 (KIS API 필요)
└── integration/
    ├── test_docker_config_verification.py # Phase 3.1: Docker 설정 검증
    ├── test_docker_volume_mapping.py      # Phase 3.1: 볼륨 매핑 검증 (Docker 필요)
    └── test_docker_track_ab_integration.py # Phase 3.2-3.3: Docker 통합 테스트
```

## 테스트 실행 순서

### Phase 1: 로컬 단위 테스트 (Docker 불필요)

```powershell
# 1.1 경로 함수 테스트
python tests/local/test_track_ab_config_creation.py

# 1.2-1.3 Mock 기반 테스트
python tests/local/test_track_ab_mock.py
```

### Phase 2: 로컬 통합 테스트 (Docker 불필요)

```powershell
# 파일 생성 검증
python tests/local/test_track_ab_file_verification.py

# KIS API 연동 테스트 (선택사항, .env 필요)
# python tests/local/test_track_a_local.py --run-once
# $env:TRACK_B_DEBUG="1"; python tests/local/test_track_b_local.py --run-once
```

### Phase 3: Docker 테스트

```powershell
# 3.1 Docker 설정 검증 (Docker 불필요)
python tests/integration/test_docker_config_verification.py

# 3.1-3.3 Docker 통합 테스트 (Docker 필요)
# 먼저 Docker 컨테이너 시작
cd infra/docker/compose
docker-compose up -d

# 테스트 실행
python tests/integration/test_docker_volume_mapping.py
python tests/integration/test_docker_track_ab_integration.py
```

## 예상 결과 파일 구조

```
app/observer/
├── config/
│   └── observer/
│       ├── scalp/
│       │   └── YYYYMMDD.jsonl  # Track B 실시간 데이터
│       └── swing/
│           └── YYYYMMDD.jsonl  # Track A 10분봉 데이터
├── logs/
│   ├── scalp/
│   │   └── YYYYMMDD.log        # Track B 로그
│   ├── swing/
│   │   └── YYYYMMDD.log        # Track A 로그
│   └── system/
│       └── observer.log        # 시스템 로그
└── data/                       # PostgreSQL 사용 (파일 없음)
```

## 경로 매핑

| 기능 | 로컬 경로 | Docker 경로 |
|------|----------|-------------|
| Config (JSONL) | `app/observer/config/observer/{scalp,swing}/` | `/app/config/observer/{scalp,swing}/` |
| Log (로그) | `logs/{scalp,swing}/` | `/app/logs/{scalp,swing}/` |
| Data | `app/observer/data/` | `/app/data/` |

## 환경 변수

| 변수 | 로컬 기본값 | Docker 값 |
|------|------------|-----------|
| `OBSERVER_STANDALONE` | (미설정) | `1` |
| `OBSERVER_CONFIG_DIR` | (미설정) | `/app/config` |
| `OBSERVER_LOG_DIR` | (미설정) | `/app/logs` |
| `OBSERVER_DATA_DIR` | (미설정) | `/app/data` |

## 문제 해결

### Docker 연결 실패
```
Docker is not running
```
→ Docker Desktop을 시작하세요.

### Observer 컨테이너 없음
```
Observer container is not running
```
→ `cd infra/docker/compose && docker-compose up -d`

### KIS API 자격 증명 없음
```
KIS_APP_KEY/SECRET not found
```
→ `app/observer/.env` 파일에 자격 증명 설정
