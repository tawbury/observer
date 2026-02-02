# GHCR 빌드·서버 구조 분석 및 리팩토링 가이드

**대상**: oracle-obs-vm-01, observer (장중 09:00~15:30 데이터 수집)  
**목표**: 1서버 / 2앱 / 1 docker-compose, 볼륨 마운트 풀림 사고 원인 정리 및 재현 가능한 구조 정비

---

## 1. GHCR 이미지 빌드 추적 요약

### 1.1 GitHub Actions 워크플로우

| 항목 | 현재 값 | 비고 |
|------|---------|------|
| **트리거** | `pull_request` (master 머지 시) + `workflow_dispatch` | PR 머지 또는 수동 실행 시에만 빌드 |
| **context** | `.` (저장소 루트) | 빌드 시 전체 레포가 context로 전달됨 |
| **file** | `./Dockerfile` | **문제**: 저장소에 루트 `Dockerfile` 없음. 실제 Dockerfile은 `infra/docker/Dockerfile` |
| **플랫폼** | `linux/arm64` | oracle-obs-vm-01용 단일 플랫폼 |
| **태그** | `build-YYYYMMDD-HHMMSS`, `latest` | |

**결론**: 워크플로우가 `file: ./Dockerfile`을 참조하지만, 레포에는 **루트 Dockerfile이 없고** `infra/docker/Dockerfile`만 존재합니다.  
→ CI에서 `failed to read Dockerfile`로 실패하거나, 과거에 루트 Dockerfile이 있었다가 이동된 상태일 수 있습니다. **반드시 수정 필요.**

### 1.2 실제 사용 중인 Dockerfile (`infra/docker/Dockerfile`)

- **빌드 컨텍스트**: 프로젝트 루트 가정 (compose 로컬 빌드 시 `context: ../../..` 사용).
- **COPY 경로**:
  - `app/observer/requirements.txt` → `/build`
  - `app/observer/` → `/app/` (이미지 내 앱 루트)
- **이미지 내부 구조**:
  - `/app/` = `app/observer/` 내용 (플랫)
  - `/app/data`, `/app/logs`, `/app/config`, `/app/secrets/.kis_cache` 등은 `RUN mkdir -p`로 빈 디렉터리만 생성.
- **환경 변수**: `OBSERVER_STANDALONE=1`, `PYTHONPATH=/app/src:/app`, `OBSERVER_*_DIR`, `KIS_TOKEN_CACHE_DIR`, `OBSERVER_ENV_FILE` 등.

### 1.3 .dockerignore 영향

| 위치 | 적용 여부 (context: `.`) |
|------|---------------------------|
| **루트 `.dockerignore`** | `.gitignore`에 `.dockerignore`가 포함되어 있어 **저장소에 커밋되지 않음**. CI checkout 시 루트에 `.dockerignore` 없음 → **미적용**. |
| **`app/observer/.dockerignore`** | Docker는 **context 루트**의 `.dockerignore`만 사용. 서브디렉터리 `.dockerignore`는 **무시**됨. |

**결과**: GHCR 빌드 시 **context 루트에 .dockerignore가 없으므로**, context로 전달되는 파일은 **git에 추적된 모든 파일**이 포함됨.  
(`.gitignore`는 Docker 빌드와 무관; Docker는 `.dockerignore`만 사용.)

- **포함되는 경로 예**: `app/observer/` 전체, `infra/`, `tests/`, `docs/`, `.github/` 등.
- **실제 이미지에 들어가는 것**: Dockerfile의 `COPY app/observer/ /app/`에 의해 **`app/observer/` 아래만** 이미지 레이어에 포함.  
  즉, context는 크지만 **최종 이미지 내용은 `app/observer/` 기준**으로만 결정됨.

**`.dockerignore` 권장**:  
- **context 루트**에 `.dockerignore`를 두고, `app/observer/` 외 불필요 디렉터리(`.git`, `docs/`, `tests/`, `infra/` 등) 제외 시 빌드 속도·캐시 안정성 향상.  
- `app/observer/.dockerignore`에 있는 규칙(`__pycache__`, `*.log`, `logs/`, `data/`, `.env` 등)은 **루트 `.dockerignore`로 이전**해야 GHCR 빌드에 반영됨.

### 1.4 GHCR 이미지에 실제 포함되는 파일/디렉터리 (추론)

Dockerfile 기준:

- **복사되는 소스**: `app/observer/` 전체 (단, context에 포함된 범위 내).
  - `__init__.py`, `__main__.py`, `observer.py`, `paths.py`, `requirements.txt`
  - `src/` 하위 모듈 전체
  - `scripts/`, `env.template`, `deployment_config.json` 등
- **제외되는 것**: Dockerfile이 복사하지 않는 상위 경로(`app/` 밖, `infra/`, `tests/` 등)는 **이미지에 없음**.
- **루트 .dockerignore가 없는 현재**: context에는 레포 전체가 들어가지만, **이미지 레이어에는 `COPY app/observer/` 결과만** 들어감.  
  단, `app/observer/.dockerignore`는 적용되지 않으므로, **이미지 안에는** `app/observer/` 내 `__pycache__`, `logs/`, `data/`, `.env` 등도 **이론상 포함될 수 있는 상태** (실제로는 보통 로컬에만 있고 git에는 없을 수 있음).

**정리**:  
- **이미지 내용**: `app/observer/` 트리 + Dockerfile에서 만든 빈 디렉터리.  
- **볼륨과의 관계**: 런타임에 `/app/data`, `/app/logs`, `/app/config`, `/app/secrets`를 호스트와 바인드하므로, 이미지 내 해당 경로는 마운트에 의해 **덮어씌워짐**.

---

## 2. 위험 지점 목록

### 2.1 빌드·CI

| # | 위험 | 설명 | 대응 |
|---|------|------|------|
| 1 | **워크플로우 Dockerfile 경로 오류** | `file: ./Dockerfile`인데 루트에 Dockerfile 없음. 실제는 `infra/docker/Dockerfile`. | `file: infra/docker/Dockerfile` 로 변경. |
| 2 | **context와 file 불일치** | context는 `.`(루트)인데 file만 바꾸면 됨. Dockerfile 내부 COPY 경로(`app/observer/`)는 루트 기준이므로 유지. | file만 수정. |
| 3 | **.dockerignore 미적용** | 루트 `.dockerignore`가 .gitignore에 있어 CI에 없음. 서브디렉터리 `.dockerignore`는 Docker가 사용하지 않음. | 루트 `.dockerignore` 추가 후 .gitignore에서 제거하여 커밋. |

### 2.2 서버 배포·볼륨 (사고와 직결)

| # | 위험 | 설명 | 대응 |
|---|------|------|------|
| 4 | **compose 볼륨 경로와 실행 위치 가정** | `docker-compose.server.yml`은 `../observer/data`, `../observer/logs` 등 **형제 디렉터리 `~/observer`** 가정. 실행 위치는 `~/observer-deploy`. | 서버에서 **항상** `~/observer-deploy`에서만 compose 실행, `~/observer`는 init_server_dirs.sh 등으로 사전 생성. |
| 5 | **server_deploy.sh가 만드는 디렉터리와 compose 불일치** | `create_required_directories`는 **DEPLOY_DIR(observer-deploy) 안**에 `data/`, `logs/`, `config/`, `secrets/` 생성. compose는 **`../observer`** 에 마운트. | observer 데이터 디렉터리는 **observer-deploy 밖** `~/observer`에 두고, init_server_dirs.sh 또는 deploy 시 **그쪽** 생성/검증하도록 정리. |
| 6 | **볼륨 마운트 풀림 가능성** | 서버 점검 문서(SERVER_CHECK_20260129)에 “볼륨 마운트(Binds)가 없음” 기록. 다른 compose 파일로 기동했거나, 상대 경로(`../observer`)가 다른 CWD에서 해석되어 빈 마운트/미마운트 가능. | 단일 compose·단일 CWD(`~/observer-deploy`)로 통일하고, 마운트 경로를 절대 경로 또는 compose 프로젝트 기준으로 명확히. |
| 7 | **migrations / monitoring 경로** | compose는 `../migrations`, `../monitoring`을 사용. 서버에 `~/migrations`, `~/monitoring`이 없으면 postgres init / Prometheus·Grafana 설정 실패. | 서버 폴더 구조에 migrations, monitoring 위치를 포함하고, 배포 스크립트/문서에 생성·복사 절차 명시. |

### 2.3 배포 스크립트·아티팩트

| # | 위험 | 설명 | 대응 |
|---|------|------|------|
| 8 | **deploy.ps1 아티팩트 경로** | `ArtifactDir = "app\observer\docker\compose"`, `requiredArtifacts = docker-compose.server.yml`. 실제 파일은 `infra/_shared/compose/docker-compose.server.yml`. | ArtifactDir를 `infra/_shared/compose`로 변경하거나, 아티팩트 목록과 실제 경로를 일치시킴. |
| 9 | **2앱 확장 시 compose** | 현재는 observer 단일 서비스. “1서버·2앱·1 compose”로 확장 시 서비스·볼륨·네트워크를 한 compose에 정의해야 함. | 서버 폴더 구조에서 “앱별 데이터 디렉터리”와 “단일 compose” 위치를 미리 설계. |

---

## 3. 서버 폴더 구조 리팩토링 초안 (1서버·2앱·1 compose)

### 3.1 원칙

- **단일 실행 경로**: 서버에서는 **한 디렉터리**에서만 `docker compose -f <단일파일> up -d` 실행.
- **데이터와 배포 아티팩트 분리**: compose·env·스크립트는 “배포 디렉터리”, 데이터·로그·설정·시크릿은 “데이터 디렉터리”로 분리.
- **다음 배포에서도 재현 가능**: 모든 경로와 절차를 레포·문서·스크립트에 고정하고, 서버에서의 임시 수정 없이 동일하게 재현.

### 3.2 제안 디렉터리 구조 (oracle-obs-vm-01)

```
/home/ubuntu/
├── observer-deploy/                    # 단일 배포 루트 (compose 실행 위치)
│   ├── docker-compose.yml              # 단일 compose (이름 고정 권장)
│   ├── .env                            # IMAGE_TAG, POSTGRES_PASSWORD 등
│   ├── server_deploy.sh
│   ├── runtime/
│   │   └── state/
│   │       └── last_good_tag
│   └── backups/
│       └── archives/
│
├── observer/                           # Observer 앱 전용 데이터 (볼륨 소스)
│   ├── data/
│   │   ├── scalp/
│   │   └── swing/
│   ├── logs/
│   │   ├── scalp/
│   │   ├── swing/
│   │   ├── system/
│   │   └── maintenance/
│   ├── config/
│   │   ├── scalp/
│   │   ├── swing/
│   │   ├── symbols/
│   │   └── universe/
│   └── secrets/
│       ├── .env
│       └── .kis_cache/
│
├── migrations/                         # Postgres init (compose에서 참조)
│   └── *.sql
│
└── monitoring/                         # Prometheus/Grafana 설정 (compose에서 참조)
    ├── prometheus.yml
    ├── prometheus_alerting_rules.yaml
    ├── grafana_dashboard.json
    ├── grafana_datasources.yml
    └── alertmanager.yml
```

- **실행**: `cd ~/observer-deploy && docker compose -f docker-compose.yml up -d`
- **compose 내부**:  
  - observer 서비스 볼륨은 `/home/ubuntu/observer/data` 등 **절대 경로** 또는 `$HOME/observer/...` 형태로 명시하면 CWD 오해 소지 제거.  
  - 또는 compose 파일만 `observer-deploy`에 두고, `env_file`/볼륨은 `../observer/...`로 유지하되, **문서·스크립트에서 “반드시 ~/observer-deploy에서 실행”** 고정.

### 3.3 두 번째 앱 추가 시 (2앱·1 compose)

- `observer-deploy/docker-compose.yml`에 서비스 한 개 더 추가 (예: `app2`).
- 데이터는 별도 디렉터리 예: `~/app2/` (data, logs, config, secrets).
- 동일하게 “배포 디렉터리”는 `observer-deploy` 하나, 데이터만 앱별로 분리.

### 3.4 compose 볼륨 경로 권장

- **옵션 A (상대 경로 유지)**:  
  - `../observer/data:/app/data` 등 유지.  
  - 조건: **항상** `~/observer-deploy`에서만 실행. server_deploy.sh와 문서에 명시.
- **옵션 B (환경 변수로 절대 경로)**:  
  - compose에 `environment: OBSERVER_DATA_HOST=/home/ubuntu/observer` 같은 변수는 Docker volume에 직접 쓰기 어려우므로, **볼륨 마운트만** 예:  
    `- ${OBSERVER_DATA_DIR:-/home/ubuntu/observer/data}:/app/data`  
  - 서버 `.env`에 `OBSERVER_DATA_DIR=/home/ubuntu/observer/data` 설정.  
  - CWD와 무관하게 동일 경로로 마운트됨.

리팩토링 시 **옵션 B**로 통일하면 “실행 위치에 따른 마운트 풀림” 위험을 줄일 수 있음.

---

## 4. 다음 단계 작업 체크리스트

### 4.1 CI / GHCR 빌드 (즉시)

- [ ] `.github/workflows/ghcr-build-image.yml`에서 `file: ./Dockerfile` → `file: infra/docker/Dockerfile` 로 수정.
- [ ] 루트에 `.dockerignore` 추가 (규칙: `.git`, `docs/`, `tests/`, `infra/` 중 이미지에 불필요한 것, `app/observer/` 내 `__pycache__`, `*.pyc`, `logs/`, `data/`, `.env` 등).  
  `app/observer/.dockerignore` 내용을 루트로 이전·통합.
- [ ] `.gitignore`에서 `.dockerignore` 제거하여 루트 `.dockerignore`가 커밋되도록 변경.
- [ ] PR 머지 또는 수동 실행으로 GHCR 빌드가 성공하는지 확인.

### 4.2 서버 배포 구조 (리팩토링)

- [ ] **단일 compose 파일명 결정**: 서버에서는 `docker-compose.yml` 또는 `docker-compose.server.yml` 중 하나로 고정하고, 모든 문서·스크립트에서 동일하게 사용.
- [ ] **compose 볼륨 경로**:  
  - [ ] 옵션 B 적용 시 `docker-compose.server.yml`에서 observer 볼륨을 `${OBSERVER_DATA_DIR}` 등 환경 변수 기반 절대 경로로 변경.  
  - [ ] 서버 `~/observer-deploy/.env`에 `OBSERVER_DATA_DIR=/home/ubuntu/observer/data` 등 정의.
- [ ] **server_deploy.sh**:  
  - [ ] `create_required_directories`에서 observer용 디렉터리는 **`~/observer`** (또는 `$OBSERVER_DATA_DIR` 상위)에 생성하도록 변경.  
  - [ ] `DEPLOY_DIR` 내부에는 `runtime/state`, `backups/archives` 등 배포 전용만 생성.
- [ ] **init_server_dirs.sh**:  
  - [ ] `~/observer` 구조 생성은 유지.  
  - [ ] 필요 시 `~/migrations`, `~/monitoring` 생성 및 레포 내용 복사 안내 추가.
- [ ] **deploy.ps1**:  
  - [ ] `ArtifactDir`를 `infra/_shared/compose`로 변경.  
  - [ ] `requiredArtifacts`에 사용할 compose 파일명이 실제 파일과 일치하는지 확인.
- [ ] **문서**:  
  - [ ] DEPLOYMENT_GUIDE, SERVER_ENV, README(deploy)에 “실행은 반드시 ~/observer-deploy”, “~/observer는 init_server_dirs.sh 또는 스크립트로 생성” 명시.  
  - [ ] “1서버·2앱·1 compose” 시 추가할 서비스·폴더 위치 가이드 추가.

### 4.3 검증

- [ ] 서버에서 `~/observer-deploy`만 사용해 `docker compose up -d` 실행 후 `docker inspect observer`로 Binds에 `observer/data`, `observer/logs` 등이 포함되는지 확인.
- [ ] 컨테이너 내부에서 `/app/logs`, `/app/data`에 쓰기 후 호스트 `~/observer/logs`, `~/observer/data`에 파일이 생기는지 확인.
- [ ] 장중 한 번 구동해 로그·데이터가 호스트에 유지되는지 확인.

### 4.4 (선택) 2앱 확장

- [ ] compose에 두 번째 앱 서비스 추가.
- [ ] 해당 앱용 데이터 디렉터리(`~/app2/` 등) 구조 및 볼륨 마운트 정의.
- [ ] server_deploy.sh 또는 init 스크립트에 두 번째 앱 디렉터리 생성 단계 추가.

---

## 5. 요약

| 구분 | 내용 |
|------|------|
| **GHCR 빌드** | context=루트, Dockerfile은 `infra/docker/Dockerfile`로 통일 필요. 루트 `.dockerignore` 추가로 context 정리. |
| **위험** | (1) 워크플로우 Dockerfile 경로 오류, (2) compose 볼륨과 server_deploy.sh 디렉터리 불일치, (3) 실행 CWD에 따른 상대 경로 해석으로 인한 마운트 풀림. |
| **서버 구조** | 배포 디렉터리(`observer-deploy`)와 데이터 디렉터리(`observer`) 분리, 단일 compose, 볼륨 경로를 환경 변수 기반으로 고정. |
| **다음 단계** | 워크플로우·.dockerignore 수정 → compose·server_deploy.sh·deploy.ps1 경로 정리 → 서버에서 마운트·로그 검증. |

이 문서와 체크리스트를 따라 수정하면 “다음 배포에서도 재현 가능”한 구조로 정리할 수 있습니다.
