# GHCR 이미지 빌드 및 DB 마이그레이션 현황 보고서

**작성일:** 2026-01-30  
**목적:** 서버에 004 스키마가 없는 원인 및 GHCR 빌드 로직과의 관계 정리.

---

## 1. GHCR 이미지 빌드 로직 (현황에 맞게 동작 중)

- **워크플로우:** `.github/workflows/ghcr-build-image.yml`
  - 트리거: master PR 머지 또는 `workflow_dispatch`
  - 컨텍스트: 프로젝트 루트, `infra/docker/Dockerfile` 사용
  - 플랫폼: `linux/arm64` (oracle-obs-vm-01 대응)

- **Dockerfile (`infra/docker/Dockerfile`):**
  - **이미지에 포함되는 것:** `app/observer/` 전체 (코드, requirements, config 디렉터리 구조 등)
  - **이미지에 포함되지 않는 것:** `infra/_shared/migrations/` — **DB 스키마 파일은 이미지에 넣지 않음**

**결론:** GHCR 이미지는 앱 코드만 담고, 마이그레이션 SQL은 포함하지 않는 설계가 맞다. 빌드 로직은 현황에 맞게 동작하고 있음.

---

## 2. 서버의 DB 스키마(001~003만 있고 004 없음) 원인

- 서버(oracle-obs-vm-01)의 `migrations` 폴더는 **Docker 이미지에서 오는 것이 아님**.
- 배포 가이드(`infra/_shared/scripts/deploy/README.md`)에 따르면:
  - 서버의 `~/migrations`(또는 `observer-deploy/../migrations`)는 **레포의 `infra/_shared/migrations` 내용을 서버에 복사**해서 채움.
  - 복사 시점에 001~003만 있었거나, 004 추가 후 **서버 쪽 migrations를 다시 복사하지 않아서** 004가 없는 상태로 보임.

**레포 현황:**

| 위치 | 001 | 002 | 003 | 004 |
|------|-----|-----|-----|-----|
| `infra/_shared/migrations/` | ✅ | ✅ | ✅ | ✅ |
| `app/observer/src/db/schema/` | ✅ | ✅ | ✅ | ✅ |
| 서버 `migrations` (사용자 확인) | ✅ | ✅ | ✅ | ❌ |

---

## 3. 서버에 004 반영 방법

1. **레포의 migrations 전체를 서버로 다시 복사**
   - 로컬/CI에서: `infra/_shared/migrations/` 전체(001~004)를 서버의 `~/migrations`(또는 compose에서 마운트하는 경로)에 복사.
   - postgres가 `docker-entrypoint-initdb.d`로 **최초 1회만** 실행하는 구조라면, 이미 DB가 생성된 뒤에는 init 스크립트가 다시 실행되지 않음. 이 경우 004는 **수동으로 한 번 적용**해야 함.

2. **004만 수동 적용 (DB가 이미 떠 있는 경우)**
   ```bash
   # 서버에서 (또는 DB_HOST로 원격 접속)
   psql -h ${DB_HOST} -U ${DB_USER} -d ${DB_NAME} -f /path/to/004_create_analysis_tables.sql
   ```
   - `004_create_analysis_tables.sql` 파일을 서버에 올린 뒤, 위처럼 실행하면 됨.

3. **다음 배포부터 004 포함시키기**
   - 서버의 `migrations` 디렉터리를 **레포의 `infra/_shared/migrations`와 동기화**하도록 한 번 갱신해 두면, 이후에는 001~004가 모두 서버에 있게 됨.
   - 문서는 `infra/_shared/README.md`, `infra/_shared/scripts/migrate/README.md`에 004를 반영해 두었음.

---

## 4. 요약

| 항목 | 내용 |
|------|------|
| GHCR 이미지에 migrations 포함 여부 | **포함 안 함** (설계상 맞음) |
| 이미지 빌드가 현황에 맞는지 | **맞음** (app/observer만 빌드) |
| 서버에 004가 없는 이유 | migrations를 **레포에서 서버로 복사**하는데, 004 추가 후 재복사/적용이 안 됨 |
| 조치 | 서버에 `infra/_shared/migrations` 동기화 또는 004 수동 적용; 문서에 004 반영 완료 |
