# oracle-obs-vm-01 서버 점검 결과 (2026-01-29)

## 점검 항목 및 결과

### 1. 아카이브 파일 생성 — ✅ 정상

| 항목 | 상태 |
|------|------|
| 디렉토리 | `backups/archives` 존재 |
| TAR 아카이브 | **2개** (최근 3개 유지 정책) |

```
observer-image_20260127-000738.tar   (~413 MB)  Jan 26 15:13
observer-image_20260127-154214.tar   (~409 MB)  Jan 27 15:49
```

- `server_deploy.sh` 배포 시 이미지 TAR 백업이 정상 생성됨.

---

### 2. DB 생성 / 마이그레이션 — ⚠️ 보완 필요

| 항목 | 상태 |
|------|------|
| PostgreSQL | ✅ 준비 완료 (`pg_isready`, `observer` DB) |
| `migration_log` | ❌ **없음** (마이그레이션 미실행) |
| 스키마(테이블) | ❌ scalp, swing, portfolio 등 **미생성** |

- DB와 `observer` DB는 있으나, **스키마 마이그레이션(001~003)이 한 번도 실행되지 않은 상태**입니다.

**권장 조치:** 서버에서 마이그레이션 실행

```bash
# SSH 접속 후
cd /home/ubuntu/observer-deploy

# 마이그레이션 SQL은 로컬 repo에 있음. 서버에 복사 후:
# (로컬에서) scp -i ... infra/_shared/migrations/*.sql ubuntu@134.185.117.22:/tmp/

# 서버에서 순서대로 실행
docker exec -i observer-postgres psql -U postgres -d observer < /tmp/001_create_scalp_tables.sql
docker exec -i observer-postgres psql -U postgres -d observer < /tmp/002_create_swing_tables.sql
docker exec -i observer-postgres psql -U postgres -d observer < /tmp/003_create_portfolio_tables.sql
```

또는 `infra/_shared/scripts/migrate/` 활용 시, `migrate.sh`가 **스키마 SQL**을 순서대로 실행하도록 구현되어 있다면 해당 스크립트 사용.

---

### 3. 실행 로그 생성 — ⚠️ 컨테이너 내부만 정상, 호스트 영속성 확인 필요

| 항목 | 상태 |
|------|------|
| **컨테이너 내부** (`/app/logs`) | ✅ 로그 생성됨 |
| **호스트** (`/home/ubuntu/observer-deploy/logs`) | ❌ `system/`, `maintenance/` **비어 있음** |

**컨테이너 내부 확인 결과:**

- `logs/system/observer.log` — ✅ 존재 (~2 KB)
- `logs/system/gap_20260122.jsonl` — ✅ 존재
- `logs/system/overflow_20260121.jsonl` — ✅ 존재
- `logs/maintenance/` — 비어 있음 (cleanup 미실행 시 정상)

**Docker 로그 (stdout):** ✅ 정상 (health check 등)

**원인 요약:**  
현재 구동 중인 `observer` 컨테이너에 **볼륨 마운트(`Binds`)가 없음**.  
즉, `./logs` → `/app/logs` 마운트가 적용된 compose로 띄운 게 아닐 가능성이 있습니다.  
그래서 로그는 **컨테이너 내부**에서만 쌓이고, 호스트 `observer-deploy/logs`에는 반영되지 않는 상태로 보입니다.

**권장 조치:**

1. `docker-compose.server.yml`에서 `./logs:/app/logs` 마운트가 정의되어 있는지 확인.
2. **동일 compose**로 `docker compose up -d` 실행해, 해당 마운트가 적용된 컨테이너로 서비스 구동.
3. 재배포 후 `logs/system/`, `logs/maintenance/`에 파일이 쌓이는지 다시 확인.

---

## 점검 스크립트

서버에서 다음 스크립트로 동일 항목을 재점검할 수 있습니다.

```bash
# 로컬 (PowerShell) — 스크립트 전달 후 실행
Get-Content "infra\_shared\scripts\deploy\check_server_health.sh" -Raw | ssh -i "C:\Users\tawbu\.ssh\oracle-obs-vm-01.key" ubuntu@134.185.117.22 "bash -s -- /home/ubuntu/observer-deploy"
```

- 스크립트는 **LF 줄바꿈**이어야 합니다. CRLF면 `sed 's/\r$//'` 등으로 변환 후 전달.

---

## 요약

| # | 항목 | 결과 |
|---|------|------|
| 1 | 아카이브 파일 생성 | ✅ 정상 |
| 2 | DB 생성 | ⚠️ PostgreSQL 동작 중, **마이그레이션 미실행** |
| 3 | 실행 로그 생성 | ⚠️ **컨테이너 내부**는 정상, **호스트** 로그 디렉토리 비어 있음 (마운트 미적용 가능성) |
