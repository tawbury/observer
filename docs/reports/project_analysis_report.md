# Observer 프로젝트 종합 분석 및 리팩토링 제안

## 1. 현 프로젝트 구조 분석
- 상위 배포 단위: `app/obs_deploy/` (Dockerfile, docker-compose, env.template, 앱 소스). 컨테이너 엔트리포인트는 `observer.py`를 `/app` 루트에 복사 후 실행.
- 실행 스텁: [app/obs_deploy/app/observer.py](app/obs_deploy/app/observer.py) — 단순 무한 루프/로깅만 수행, EventBus·Snapshot 파이프라인 미사용.
- 핵심 도메인 코드: `app/obs_deploy/app/src/observer/` 하위에 관찰 파이프라인(Observer, EventBus, JsonlFileSink, Guard/Validation, Enricher), 로테이션([log_rotation.py](app/obs_deploy/app/src/observer/log_rotation.py)), 배포 경로 해석([deployment_paths.py](app/obs_deploy/app/src/observer/deployment_paths.py)).
- 런타임 브리지: `app/obs_deploy/app/src/runtime/` 하위에 Phase 15 입력 브리지·KIS 현재가 소스 스텁([phase15_current_price_source.py](app/obs_deploy/app/src/runtime/phase15_current_price_source.py)), 실시간 틱 러너 스텁([real_tick_runner.py](app/obs_deploy/app/src/runtime/real_tick_runner.py)).
- 설정: [deployment_config.json](app/obs_deploy/app/deployment_config.json) (standalone, /app 구조), `env.template`는 PowerShell 스크립트 형태로 실제 `.env`가 아님.
- 인프라/문서: `docs/`에 배포/운영 가이드, `infra/`에 Terraform, `app/obs_deploy/docker-compose.yml`로 로컬 배포 정의.

## 2. 로깅 시스템 결함 진단 (Critical)
- **엔트리포인트 불일치**: 컨테이너는 [app/obs_deploy/app/observer.py](app/obs_deploy/app/observer.py)를 실행하지만, 이 파일은 Snapshot 생성·EventBus 디스패치가 없는 스텁이다. 따라서 JsonlFileSink가 호출되지 않아 어떤 로그/JSONL도 생성되지 않는다.
- **경로 불일치**: JsonlFileSink는 [deployment_paths.py](app/obs_deploy/app/src/observer/deployment_paths.py)에서 `observer_asset_dir()`(기본 `/app/data/observer`)에 기록한다. docker-compose는 `/app/logs` 볼륨을 마운트하지만 실제 JSONL은 `/app/data/observer`에 쌓이도록 설계되어 로그 경로 기대치와 다르다. (서버에서 `find /app -name '*.jsonl'`에도 없었던 것은 상기 스텁 실행 때문.)
- **로깅 설정 최소화**: 엔트리포인트에서 `logging.basicConfig`만 호출하고 파일 핸들러/로테이션/구조화 로그 설정이 없다. stdout만 남고 파일 미생성.
- **환경 템플릿 오류**: [env.template](app/obs_deploy/env.template)가 PowerShell 스크립트 형태라 실제 `.env`를 만들지 않으면 KIS 자격/경로 변수가 주입되지 않는다. (KIS 소스는 env 미존재 시 즉시 RuntimeError 발생.)
- **경로 생성 시점**: EventBus 초기화 시에는 디렉터리를 생성하지만, 스텁 엔트리포인트가 EventBus를 생성하지 않아 `/app/data/observer`·`/app/logs`가 실제 런타임에서 보장되지 않는다.

## 3. KIS API 연동 상태 점검 (2,000종목 스캔 관점)
- 현재 구현은 **Phase 15 스텁** 수준. `MockCurrentPriceSource` 기본, `KisCurrentPriceSource`는 `fetch_current_price_raw()` 미구현 상태이며 env 자격만 검사.
- 실시간 틱 러너 [real_tick_runner.py](app/obs_deploy/app/src/runtime/real_tick_runner.py)는 `_observer._snapshot_factory` 호출을 가정하지만 실제 Observer 구현에는 존재하지 않는다. 입출력 계약 불일치로 대량 종목 스캔 파이프라인이 동작하지 않는다.
- 멀티심볼/배치 스케줄링, 토큰/레이트리밋 관리, 장애 격리(심볼별 큐) 로직 부재. 1,500~2,000 종목 대상 확장성 검증 전무.
- 상태 관측/백프레셔/중복 필터링, 재시도, 실패 격리 등이 정의되지 않아 대규모 종목 수집 시 병목/누락 위험이 높다.

## 4. 리팩토링 제안 (Architecture)
### 4.1 로깅/스냅샷 파이프라인 개선
- **단일 엔트리포인트 재구성**: `main.py`(신규)에서 `validate_deployment_paths()` 실행 → EventBus(Jsonl + File Rotating) → Observer → Runner 체인 구성. Docker CMD를 `python -m observer.main` 형태로 고정.
- **핸들러 분리**: 구조화 파일 로그(`RotatingFileHandler` to `/app/logs/observer.log`), JSONL 스냅샷(`JsonlFileSink` to `/app/data/observer/*.jsonl`), stdout(handler=INFO) 3-way 로깅. 로테이션/보존기간 옵션화.
- **환경 변수 일원화**: `OBSERVER_LOG_DIR`, `OBSERVER_DATA_DIR`, `PHASE15_SOURCE_MODE`, `PHASE15_SYMBOL(S)` 등 `.env` → `docker-compose` → `systemd`로 동일하게 주입. `.env` 템플릿을 실제 key=value 포맷으로 재작성.

### 4.2 2,000 종목 스캔 아키텍처
- **심볼 샤딩 워커**: 심볼을 N개 워커(예: asyncio + aiohttp/웹소켓)로 분할, 워커별 큐/백프레셔 적용. 심볼 메타/상태는 Redis(또는 in-memory + periodic flush)로 관리.
- **입력 추상화**: `CurrentPriceSource`를 REST/WS/Kafka 등으로 플러거블하게 유지. KIS 토큰 리프레시·레이트리밋을 별도 `TokenManager`/`RateLimiter`로 분리.
- **스냅샷 파이프라인**: Phase15InputBridge → ObservationSnapshot → Observer → EventBus. 실패 격리는 심볼 단위 재시도(지수·ETF 등 중요 심볼 가중치 가능).

### 4.3 DB 전환 전략
- **모델링**: `pattern_records` (id, symbol, received_at, payload_raw JSONB, quality/meta, ingest_source, created_at), `ingest_errors`, `usage_metrics` 테이블. PostgreSQL/TimescaleDB 추천.
- **Ingestion Sink**: EventBus에 `DbSink` 추가 (비동기 큐 + 배치 insert). DB 장애 시 파일 JSONL을 계속 적재 후 `replay` 명령으로 복구.
- **마이그레이션/스키마 관리**: Alembic 스크립트 추가. CI에서 lint + migration 체크.

### 4.4 로컬 PC 백업 워크플로
- **스냅샷 백업**: 서버 `/app/data/observer/*.jsonl` → 로컬 Windows `D:\observer_backup\jsonl`로 `rclone`/`rsync`(WSL) 또는 `robocopy`(smb 마운트) 스케줄링. 무결성 체크섬 + 전송 로그.
- **로그 백업**: `/app/logs/*.log` 동일 스케줄. 실패 시 알림(이메일/Slack).
- **폴더 구조 표준화**: 날짜별 파티션 `/YYYY/MM/DD/HH/`로 저장해 검색성 확보.

## 5. 향후 To-Do 리스트 (우선순위)
1) **엔트리포인트 교체**: 실제 Observer 파이프라인을 구동하는 `main.py` 작성, Docker CMD 갱신. 스텁 `observer.py`는 제거/테스트 전용으로 분리.
2) **로깅 경로 정합성**: JsonlFileSink를 `/app/data/observer`, 파일 로그를 `/app/logs`로 명확히 분리하고 디렉터리 생성/권한을 부팅 시 검증.
3) **.env 템플릿 수정**: PowerShell 스크립트 형태 제거, 순수 key=value 포맷으로 재배포. KIS 자격 필수값 검증 로직 추가.
4) **Phase15 파이프라인 완성**: `_snapshot_factory` 구현 또는 Phase15InputBridge + Snapshot dataclass로 일원화. Mock/KIS 소스 스위칭 및 단일/다중 심볼 실행 파라미터 지원.
5) **멀티심볼 스케줄러**: 심볼 리스트를 샤딩해 워커 실행, 레이트리밋/토큰 리프레시 모듈화. 장애 심볼 격리 및 재시도 정책 추가.
6) **DB Sink 도입**: PostgreSQL 연결 + 배치 insert Sink 구현. JSONL 파일은 백업/리플레이 경로로 유지.
7) **백업 자동화**: 서버→로컬 동기화 스크립트 작성, 스케줄러 등록, 전송 로그/알림 추가.
8) **운영 관측성**: Health/metrics 엔드포인트(상태, 큐 적재량, 로테이션 파일명), 로그 로테이션/디스크 사용 모니터링.
