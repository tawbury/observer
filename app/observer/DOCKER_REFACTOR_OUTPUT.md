# Observer 앱 전용 Docker 리팩토링 결과

## 1. 리팩토링 전 observer 폴더 구조 요약

- **진입점**: `__main__.py`, `observer.py`, `paths.py`, `__init__.py`
- **코드**: `src/` (observer, runtime, collector, db, provider, universe 등)
- **스크립트**: `scripts/` (init_db, create_tables_direct, collect_stock_symbols)
- **설정 템플릿**: `env.template`, `deployment_config.json`
- **의존성**: `requirements.txt`
- **런타임 디렉터리** (이미지에 넣지 않음): `data/`, `logs/`, `config/` 하위 런타임 파일, `secrets/`
- **Dockerfile 위치**: 레포 루트 기준 `infra/docker/Dockerfile`, 빌드 컨텍스트 = 프로젝트 루트, COPY 경로 `app/observer/` 사용

---

## 2. 리팩토링 후 observer 폴더 구조 (tree)

```
app/observer/
├── .dockerignore          # 신규 (빌드 컨텍스트 = app/observer 기준)
├── Dockerfile             # 신규 (앱 단독 빌드, 상위 COPY 없음)
├── __init__.py
├── __main__.py
├── observer.py
├── paths.py
├── requirements.txt
├── env.template
├── deployment_config.json
├── README_INDEPENDENT_TRACK_B.md
├── scripts/
│   ├── collect_stock_symbols.py
│   ├── create_tables_direct.py
│   └── init_db.py
└── src/
    ├── __init__.py
    ├── auth/
    ├── automation/
    ├── backup/
    ├── collector/
    ├── db/
    │   └── schema/
    ├── decision_pipeline/
    │   ├── contracts/
    │   ├── execution_stub/
    │   └── pipeline/
    ├── gap/
    ├── maintenance/
    │   ├── cleanup/
    │   ├── backup/
    │   └── retention/
    ├── monitoring/
    ├── observer/
    │   ├── analysis/
    │   │   ├── adapters/
    │   │   ├── contracts/
    │   │   ├── features/
    │   │   ├── persistence/
    │   │   └── signal_frame/
    │   └── inputs/
    ├── optimize/
    ├── provider/
    │   └── kis/
    ├── retention/
    ├── runtime/
    ├── safety/
    ├── shared/
    ├── slot/
    ├── trigger/
    └── universe/
```

- **파일/디렉터리 재배치**: 없음. 기존 레이아웃 유지, `Dockerfile`·`.dockerignore`만 추가.
- **런타임 디렉터리** (`data/`, `logs/`, `config/` 런타임 내용, `secrets/`)는 `.dockerignore`로 제외되며, 이미지 내부는 Dockerfile의 `RUN mkdir -p`로 빈 디렉터리만 생성.

---

## 3. `app/observer/Dockerfile` 전체 내용

```dockerfile
# Observer app-only image. Build context: app/observer (no parent COPY).
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . /app/

RUN mkdir -p /app/data/scalp /app/data/swing \
    && mkdir -p /app/logs/scalp /app/logs/swing /app/logs/system /app/logs/maintenance \
    && mkdir -p /app/config/scalp /app/config/swing /app/config/symbols /app/config/universe \
    && mkdir -p /app/secrets/.kis_cache

ENV OBSERVER_STANDALONE=1
ENV PYTHONPATH=/app/src:/app
ENV TZ=Asia/Seoul
ENV OBSERVER_DATA_DIR=/app/data
ENV OBSERVER_LOG_DIR=/app/logs
ENV OBSERVER_SYSTEM_LOG_DIR=/app/logs/system
ENV OBSERVER_MAINTENANCE_LOG_DIR=/app/logs/maintenance
ENV OBSERVER_CONFIG_DIR=/app/config
ENV KIS_TOKEN_CACHE_DIR=/app/secrets/.kis_cache
ENV OBSERVER_ENV_FILE=/app/secrets/.env

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN groupadd -r observer && useradd -r -g observer observer
RUN chown -R observer:observer /app

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=2 \
    CMD ["python","-c","import urllib.request,sys; r=urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=3); sys.exit(0 if r.getcode()==200 else 1)"]

EXPOSE 8000
USER observer

CMD ["python", "-m", "observer"]
```

---

## 4. `app/observer/.dockerignore` 전체 내용

```
# Build context root: app/observer. Exclude runtime and dev-only.

# Python
__pycache__
*.pyc
*.pyo
*.pyd
*.pyc
.pytest_cache
*.egg-info
.eggs
*.egg

# Runtime dirs (image uses empty dirs from Dockerfile)
logs/
data/
config/scalp/
config/swing/
config/universe/
config/symbols/
config/observer/
config/system/
config/backups/
secrets/

# Secrets and env (runtime-injected)
.env
.env.*

# Docs and tests (not needed in image)
*.md
test/
tests/
.git
.gitignore

# Build and IDE
.vscode
.venv
venv
*.log
*.sqlite3
*.db
*.tar
*.tar.gz
*.tar.bak

# OS
.DS_Store
Thumbs.db
```

---

## 5. 구조 설계 핵심 이유 요약

- **앱 단독 빌드**: 빌드 컨텍스트를 `app/observer`로 한정하고, 상위 디렉터리(`app/` 밖)를 참조하는 COPY를 제거해 observer만으로 이미지 빌드가 완결되도록 함.
- **런타임 디렉터리 분리**: `data/`, `logs/`, `config/` 런타임 내용, `secrets/`는 `.dockerignore`로 제외하고, 이미지 내부는 Dockerfile에서 `RUN mkdir -p`로 빈 디렉터리만 두어, 런타임 마운트로 덮어써도 동작하도록 함.
- **진입점·환경 고정**: `WORKDIR /app`, `PYTHONPATH=/app/src:/app`, `CMD ["python", "-m", "observer"]`를 Dockerfile에서만 정의해, 컨테이너 실행 시 엔트리포인트와 경로가 일정하게 유지되도록 함.
