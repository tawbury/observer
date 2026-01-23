# GHCR & GitHub Actions 현황 보고서

---

## 메타 정보

| 항목 | 내용 |
|------|------|
| 문서명 | GHCR & GitHub Actions 현황 보고서 |
| 작성일 | 2026-01-22 |
| 상태 | 현황 분석 완료 |
| 범위 | GitHub Actions 워크플로우, GHCR 레지스트리, 배포 스크립트 |
| 대상 시스템 | Observer (주식거래 분석 플랫폼) |
| 저자 | DevOps Auditor |
| 승인 필요 | N |

---

## 요약 (Executive Summary)

본 보고서는 현재 리포지토리의 GitHub Actions 워크플로우 및 GHCR(GitHub Container Registry) 배포 인프라의 현황을 분석한 결과입니다. 

**핵심 발견사항:**
- ✅ GHCR 레지스트리 통합 완료 (docker-compose.server.yml, server_deploy.sh)
- ✅ 배포 자동화 스크립트 v1.1.0 구현 (deploy.ps1, server_deploy.sh)
- ✅ 환경 변수 SSoT(Single Source of Truth) 정책 적용 (.env)
- ⚠️ 기존 GitHub Actions 워크플로우는 Azure Container Registry(ACR) 중심
- ⚠️ .env.server 레거시 참조가 구 문서에 남아있음 (위험 요소)
- 🔄 GitHub Actions deploy-only 워크플로우 설계 준비 완료

**다음 단계:** GitHub Actions에서 build/push는 로컬에서 수행하고, Actions는 배포(deploy)만 담당하는 Design A 구현 권장.

---

## 1. 리포지토리 현황

### 1.1 브랜치 구조

| 브랜치 | 용도 | 상태 | HEAD |
|--------|------|------|------|
| `master` | Release branch (프로덕션) | 활성 | bdbe6b5 |
| `observer` | Development branch | **활성 (현재)** | **7be36b6** |
| `origin/observer` | Remote dev branch | 활성 | 7be36b6 |
| `origin/master` | Remote release branch | 활성 | bdbe6b5 |

**분석:**
- observer (dev) 브랜치가 현재 HEAD
- master (release) 브랜치와 동기화 필요 (observer가 5개 커밋 앞서있음)
- 배포 워크플로우 자동화 최신 코드는 observer 브랜치에만 존재

### 1.2 최근 커밋 히스토리 (observer 브랜치)

| 커밋 | 메시지 | 날짜 |
|------|--------|------|
| 7be36b6 | Add env-only mode to deploy orchestration | 최신 |
| 5c1d6b9 | .env 배포 스크립트 추가 | - |
| 55b8bc7 | 배포 아티팩트를 .gitignore에 추가 | - |
| 8ee18fd | 배포 자동화 시스템 v1.0.0 구현 | - |
| 0363f7d | docs: add deploy automation workflow | - |

**핵심:** 최근 4개 커밋(0363f7d ~ 7be36b6)이 모두 배포 자동화와 관련된 변경사항 포함

---

## 2. GitHub Actions 워크플로우 현황

### 2.1 워크플로우 목록

master 브랜치에 4개의 GitHub Actions 워크플로우 파일이 존재합니다.

| 파일 | 이름 | 트리거 | 주요 작업 |
|------|------|--------|----------|
| `deploy.yml` | Observer CI/CD Pipeline | push (main/develop), PR, workflow_dispatch | Security scan, Test, Build, Terraform, Health check, Notify |
| `deploy-infrastructure.yml` | Deploy Observer to Infrastructure | push (main, app paths), workflow_dispatch | Test, Build-and-push (GHCR), Deploy staging, Deploy production |
| `terraform.yml` | Terraform CI | push (main), PR | Terraform init, plan, apply |
| `scheduled-ops.yml` | Scheduled Operations Automation | cron (daily/weekly), workflow_dispatch | Backup, Log rotate, Security update, Health check, Cost report |

### 2.2 워크플로우 상세 분석

#### 2.2.1 deploy.yml (Observer CI/CD Pipeline)

**작동 원리:**
```
push to main/develop → security-scan 
                     → test (병렬)
                     → build (registry: observerregistry.azurecr.io)
                     → terraform
                     → health-check
                     → notify (Slack)
```

**특징:**
- 레지스트리: Azure Container Registry (ACR) - `observerregistry.azurecr.io`
- 자동 태그: git branch/semver/sha 기반 (latest는 main 브랜치만)
- 보안: Trivy 취약점 스캔 포함
- 알림: Slack webhook 연동

**문제점:**
- ❌ GHCR이 아닌 ACR 사용 (현재 서버 배포는 GHCR 의존)
- ❌ 로컬 개발 환경과 CI/CD 레지스트리 불일치

#### 2.2.2 deploy-infrastructure.yml (Deploy Observer to Infrastructure)

**작동 원리:**
```
push to main (app paths) → test
                        → build-and-push (GHCR)
                        → deploy-staging
                        → deploy-production (main 브랜치만)
```

**특징:**
- 레지스트리: GHCR - `ghcr.io/tawbury/observer`
- 권한: GitHub Token 사용 (GITHUB_TOKEN)
- 태그: ref/sha/branch/latest (main만)
- 환경 변수: GHCR 레지스트리 명시

**중요:**
- ✅ **현재 서버 배포와 일치하는 레지스트리 사용**
- ✅ Staging/Production 환경 분리 배포 지원
- ⚠️ 전체 파이프라인 자동화 (build → push → deploy 모두 포함)

#### 2.2.3 terraform.yml (Terraform CI)

**작동 원리:**
```
push to main / PR → terraform init → terraform fmt check
                 → terraform validate
                 → terraform plan
                 → terraform apply (main push only)
```

**특징:**
- 독립 실행 워크플로우 (다른 job과 의존성 없음)
- main 브랜치 push 시 자동 apply

#### 2.2.4 scheduled-ops.yml (Scheduled Operations Automation)

**작동 원리:**
```
Daily (UTC 15:00 = KST 00:00):
  → backup, rotate_logs, cleanup

Weekly Mon (UTC 17:00 = KST 02:00):
  → security_update, health_check, cost_report
  → upload artifact
```

**특징:**
- cron 기반 스케줄 실행
- 수동 실행(workflow_dispatch) 지원
- 백업 및 보안 업데이트 자동화

---

## 3. 배포 인프라 현황

### 3.1 로컬 배포 스크립트 (Windows)

**파일:** `scripts/deploy/deploy.ps1` (v1.1.0)

**용도:**
```
로컬 환경 검증 → SSH 업로드 → 서버 배포 스크립트 실행 → 헬스 체크
```

**주요 파라미터:**
```powershell
-ServerHost          : 대상 서버 IP
-SshUser            : SSH 사용자 (기본값: azureuser)
-SshKeyPath         : SSH 프라이빗 키 경로
-DeployDir          : 서버 배포 디렉토리 (기본값: /home/azureuser/observer-deploy)
-ImageTag           : Docker 이미지 태그 (필수)
-Rollback           : 롤백 모드 (선택)
-EnvOnly            : .env만 배포 (아티팩트 제외)
```

**동작 모드:**

| 모드 | 용도 | 명령어 |
|------|------|--------|
| Deploy | 신규 배포/업데이트 | `.\deploy.ps1 -ImageTag 20260123-173045` |
| Rollback | 이전 버전으로 복구 | `.\deploy.ps1 -Rollback` |
| EnvOnly | 환경 변수만 업데이트 | `.\deploy.ps1 -EnvOnly` |

**주요 검증:**
- `.env` 파일 존재 확인
- 필수 환경 변수 확인 (env.template 기준)
- SSH 연결 테스트
- 아티팩트 존재 확인 (compose file 등)

### 3.2 서버 배포 스크립트 (Linux)

**파일:** `scripts/deploy/server_deploy.sh` (v1.1.0) - 서버 실행

**용도:**
```
GHCR 이미지 pull → Compose 실행 → last_good_tag 관리 → tar 백업
```

**핵심 함수:**

| 함수 | 목적 |
|------|------|
| `resolve_image_tag()` | Deploy 또는 Rollback 이미지 태그 결정 |
| `pull_docker_image()` | GHCR에서 이미지 pull |
| `update_last_good_tag()` | 성공 후 last_good_tag 파일 업데이트 |
| `save_image_tar()` | 배포된 이미지를 tar 아카이브로 저장 |
| `prune_old_tars()` | 최근 3개만 유지 (자동 cleanup) |

**배포 프로세스:**

```bash
# 배포 모드
server_deploy.sh /home/azureuser/observer-deploy docker-compose.server.yml 20260123-173045 deploy

# 롤백 모드 (last_good_tag 자동 읽음)
server_deploy.sh /home/azureuser/observer-deploy docker-compose.server.yml "" rollback
```

**생성 경로:**

| 경로 | 용도 |
|------|------|
| `$DEPLOY_DIR/runtime/state/last_good_tag` | 마지막 성공 배포 이미지 태그 (텍스트) |
| `$DEPLOY_DIR/backups/archives/observer-image_<TAG>.tar` | 배포된 이미지 아카이브 |

### 3.3 Docker Compose 파일

**파일:** `app/obs_deploy/docker-compose.server.yml`

**이미지 레퍼런스:**
```yaml
services:
  observer:
    image: ghcr.io/tawbury/observer:${IMAGE_TAG:?IMAGE_TAG required}
    # ↑ IMAGE_TAG 환경 변수 필수, "latest" 제거됨
```

**서비스:**
- `postgres:15-alpine` - 데이터베이스
- `ghcr.io/tawbury/observer` - Observer 애플리케이션

**환경 변수 주입:**
```bash
# compose 실행 시 IMAGE_TAG 필수 (타임스탬프 형식)
IMAGE_TAG=20260123-173045 docker compose -f docker-compose.server.yml up -d
```

### 3.4 환경 설정 정책 (SSoT)

**파일:** `.env` (Single Source of Truth)

**템플릿:** `app/obs_deploy/env.template`

**정책:**
- ✅ 새 코드: `.env` 파일만 사용
- ✅ compose: `${IMAGE_TAG:?IMAGE_TAG required}` 필수 검증
- ❌ **레거시 위험:** 구 문서에서 `.env.server` 참조 (20개 매치)

**env.template 구성:**
```plaintext
KIS_APP_KEY, KIS_APP_SECRET (KIS API 자격증명)
OBSERVER_* (Observer 설정 디렉토리)
TRACK_A_ENABLED, TRACK_B_ENABLED (기능 토글)
DB_* (데이터베이스 설정)
```

---

## 4. 배포 브리지 비교

### 4.1 현재 상태 분석

| 항목 | deploy.yml (ACR) | deploy-infrastructure.yml (GHCR) | 로컬 배포 (GHCR) |
|------|------------------|----------------------------------|------------------|
| **레지스트리** | ACR (observerregistry.azurecr.io) | GHCR (ghcr.io) | GHCR (ghcr.io) |
| **Build** | GitHub Actions | GitHub Actions | 로컬 (미구현) |
| **Push** | GitHub Actions | GitHub Actions | 로컬 (미구현) |
| **Deploy** | Terraform + 스크립트 | GitHub Actions 내장 | deploy.ps1 + server_deploy.sh |
| **이미지 태그 패턴** | branch/semver/sha | ref/sha/latest | 타임스탐프 git tag (yyyyMMdd-HHmmss, 예: 20260123-173045) |
| **서버 디렉토리** | - | - | /home/azureuser/observer-deploy |
| **상태** | ✅ 활성 | ✅ 활성 | ✅ 구현 완료 |

### 4.2 불일치 문제점

**문제 1: 레지스트리 불일치**
- `deploy.yml`: ACR에 push
- `deploy-infrastructure.yml`: GHCR에 push
- 로컬 배포: GHCR pull 기대
- **영향:** Actions 실행 시 서버는 GHCR 이미지 부재로 실패 가능

**문제 2: 이미지 태그 표준화 부재**
- deploy.yml: semver/branch/sha 조합
- deploy-infrastructure.yml: ref/sha/latest 조합
- 로컬 배포: 타임스탐프 git tag (yyyyMMdd-HHmmss 형식)
- **영향:** 버전 추적 및 롤백 불명확성

**문제 3: Deploy 책임 분산**
- deploy.yml: Terraform apply 포함
- deploy-infrastructure.yml: Actions 내 deploy script
- 로컬: deploy.ps1 + server_deploy.sh
- **영향:** 배포 로직이 3개 경로에서 관리됨

---

## 5. GitHub Actions Design A 제안

### 5.1 Design A: Build/Push 로컬, Deploy Actions 전용

**목표:**
```
로컬 빌드/푸시 → GitHub Tag → Actions는 배포만 수행
```

**워크플로우:**

```yaml
name: Deploy Observer (Actions Deploy-Only)

on:
  push:
    tags:
      - '20*'  # 타임스탐프 형식의 태그 (yyyyMMdd-HHmmss, 예: 20260123-173045)

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: tawbury/observer

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    if: github.ref_type == 'tag'
    environment: staging
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Extract tag version
        id: tag
        run: echo "version=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT

      - name: Deploy to Staging
        run: |
          # PowerShell 스크립트 실행 또는 SSH 배포
          ssh -i ${{ secrets.DEPLOY_KEY }} azureuser@${{ secrets.STAGING_HOST }} \
            "cd /home/azureuser/observer-deploy && \
             bash scripts/deploy/server_deploy.sh . docker-compose.server.yml ${{ steps.tag.outputs.version }} deploy"

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    if: github.ref_type == 'tag'
    environment: production
    steps:
      - name: Deploy to Production
        run: |
          ssh -i ${{ secrets.DEPLOY_KEY }} azureuser@${{ secrets.PROD_HOST }} \
            "cd /home/azureuser/observer-deploy && \
             bash scripts/deploy/server_deploy.sh . docker-compose.server.yml ${{ steps.tag.outputs.version }} deploy"
```

**장점:**
- ✅ 로컬에서 Docker 이미지 빌드/테스트 완전 통제
- ✅ 단일 진실 공급원: git tag = image tag = deployment tag
- ✅ 배포 책임 명확: Actions = 배포만
- ✅ 빠른 배포 사이클 (build 스킵)
- ✅ 로컬 환경과 프로덕션 일관성

**구현 전제:**
1. 로컬에서 `docker build → docker push` 자동화 필요
2. GHCR token 액세스 권한 설정 필요
3. 서버 SSH 키 관리 필요 (`DEPLOY_KEY` secret)
4. 이미지 태그 표준화: 타임스탐프 git tag (yyyyMMdd-HHmmss 형식)

---

## 6. 서버 환경 현황

### 6.1 Azure VM 상태

| 항목 | 값 |
|------|-----|
| VM 크기 | Standard_B2ms |
| CPU | 2 vCPU |
| RAM | **8 GB (7.7 Gi 활성)** |
| 상태 | 실행 중 |
| 메모리 사용 | ~721 Mi / 7.7 Gi |
| 부팅 | ~3분 전 (최근 재시작) |

**분석:** VM 리소스 충분함

### 6.2 Docker Compose 상태

**컨테이너:**
```
observer-postgres    → healthy (healthcheck 통과)
observer             → unhealthy (PerformanceMetrics .items() 버그 - 기존 이슈)
```

**결론:** 배포 인프라 정상, 애플리케이션 버그는 별도 이슈

### 6.3 배포 디렉토리 구조

```
/home/azureuser/observer-deploy/
├── docker-compose.server.yml      (compose 파일)
├── .env                           (환경 변수, SSoT)
├── runtime/
│   └── state/
│       └── last_good_tag          (마지막 성공 이미지 태그)
├── backups/
│   └── archives/
│       ├── observer-image_20260123-173045.tar
│       ├── observer-image_20260122-154230.tar
│       └── observer-image_20260121-120015.tar  (최근 3개)
└── data/, logs/, config/          (애플리케이션 데이터)
```

---

## 7. 위험 요소 및 개선 항목

### 7.1 레거시 .env.server 참조

**현황:**
- 구 문서에서 `.env.server` 참조 (20개 매치)
- 신규 코드: `.env` 사용 (정책 준수)
- **위험:** Actions 디자인 시 문서와 실제 불일치 가능

**권장 조치:**
```bash
grep -r "\.env\.server" docs/
# 결과: README.md, QUICKSTART.md, IMPLEMENTATION_REPORT.md 등에서 .env로 수정 필요
```

**우선순위:** 낮음 (신규 코드 준수함, 문서 정리 권장)

### 7.2 GitHub Actions 워크플로우 중복

**현황:**
- `deploy.yml`: ACR 기반 전체 파이프라인
- `deploy-infrastructure.yml`: GHCR 기반 전체 파이프라인
- **문제:** 중복 유지 비용, 불명확한 트리거

**권장 조치:**
```yaml
# Design A 적용 시:
1. deploy.yml (ACR) → 폐기 또는 보존 (필요시)
2. deploy-infrastructure.yml (GHCR) → 통합
3. 신규: deploy-tag.yml (Deploy-Only Actions)
```

### 7.3 이미지 태그 표준화 부재

**현황:**
- 각 워크플로우마다 서로 다른 태그 패턴
- 로컬 배포: 타임스탐프 git tag (yyyyMMdd-HHmmss 형식)

**권장 조치:**
**표준화 규칙:**
```yaml
표준화 규칙:
- Git tag: {YYYYMMDD-HHmmss}  (타임스탐프, 예: 20260123-173045)
- Image tag: {git-tag}        (예: 20260123-173045)
- last_good_tag: {image-tag}  (예: 20260123-173045 저장)
```

### 7.4 배포 자동화 테스트 부족

**현황:**
- `deploy.ps1`, `server_deploy.sh` 수동 테스트만 수행
- CI/CD에 배포 스크립트 통합 테스트 없음

**권장 조치:**
```bash
# 테스트 케이스:
1. Deploy 모드: 신규 이미지 배포 성공 확인
2. Rollback 모드: last_good_tag 자동 읽음 및 복구
3. EnvOnly 모드: .env 업데이트만 수행
4. 헬스 체크: 배포 후 /health 엔드포인트 확인
```

---

## 8. 현황 체크리스트

### 8.1 GHCR 통합 준비도

- [x] docker-compose.server.yml: GHCR 레지스트리 설정
- [x] server_deploy.sh: GHCR pull 로직 구현
- [x] IMAGE_TAG 환경 변수 필수화
- [x] last_good_tag 자동 관리
- [x] tar 백업 및 프루닝 정책
- [ ] **로컬 build/push 자동화 (미구현)**
- [ ] GitHub Actions deploy-only 워크플로우 (미구현)

### 8.2 배포 자동화 준비도

- [x] deploy.ps1 v1.1.0 (Windows 배포 오케스트레이터)
- [x] server_deploy.sh v1.1.0 (Linux 서버 실행)
- [x] Rollback 모드 지원
- [x] EnvOnly 모드 지원
- [x] 헬스 체크 (curl /health)
- [ ] **자동화된 배포 테스트 (미구현)**

### 8.3 GitHub Actions 준비도

- [x] deploy.yml (CI/CD 전체 - ACR)
- [x] deploy-infrastructure.yml (전체 - GHCR)
- [x] terraform.yml (Terraform CI)
- [x] scheduled-ops.yml (스케줄 작업)
- [ ] **Deploy-Only 워크플로우 (미구현)**
- [ ] **레지스트리 통일 (미완료)**
- [ ] **이미지 태그 표준화 (미완료)**

---

## 9. 결론 및 권장사항

### 9.1 현황 평가

**긍정적 측면:**
- ✅ GHCR 통합 기본 구조 완성
- ✅ 배포 자동화 스크립트 v1.1.0 구현
- ✅ 환경 변수 SSoT 정책 준수 (신규 코드)
- ✅ last_good_tag 및 tar 백업 메커니즘
- ✅ 서버 VM 리소스 충분
- ✅ Docker Compose 정상 구동

**부정적 측면:**
- ❌ GitHub Actions: ACR vs GHCR 이중화
- ❌ 이미지 태그 표준화 부재
- ❌ 로컬 build/push 자동화 미흡
- ❌ 레거시 문서에 .env.server 참조 잔존
- ❌ 배포 자동화 통합 테스트 부족

### 9.2 즉시 조치 항목

| 우선순위 | 항목 | 설명 | 영향도 |
|---------|------|------|--------|
| P0 | 레지스트리 통일 | deploy.yml을 GHCR로 전환 또는 통합 | 높음 |
| P1 | Design A 구현 | Deploy-Only Actions 워크플로우 추가 | 높음 |
| P2 | 이미지 태그 표준화 | git tag = image tag = deployment tag | 중간 |
| P3 | 문서 정리 | .env.server 참조 제거 | 낮음 |
| P4 | 배포 테스트 자동화 | CI/CD에 deploy script 검증 추가 | 중간 |

### 9.3 Design A 구현 로드맵

```
Phase 1: 준비 (현재)
  - 로컬 docker build/push 자동화 개발
  - GHCR 액세스 토큰 설정
  - Secrets 관리 (DEPLOY_KEY 등)

Phase 2: 구현
  - deploy-tag.yml (Deploy-Only Actions) 작성
  - 테스트 배포 수행
  - 롤백 테스트

Phase 3: 검증
  - Staging 환경 배포 테스트
  - Production 준비
  - 문서 정리

Phase 4: 전환
  - 이전 워크플로우 폐기 또는 보존
  - 모니터링 강화
  - 배포 프로세스 정책 업데이트
```

---

## 10. 부록

### 10.1 워크플로우 파일 체크섬

| 파일 | Blob Hash | 라인 수 |
|------|-----------|--------|
| deploy.yml | 0102dc314647bdcaa75d6728ba8f2a1ab75b6c99 | ~240 |
| deploy-infrastructure.yml | a655661d6cf018055c46056842022b441edb93e4 | ~200+ |
| terraform.yml | 479e07d9d2cb7bf127f1e245edd3df1e0d3e5abd | ~35 |
| scheduled-ops.yml | fbe790f67ce5c6cbf489dd2e88dcfcae03a87d08 | ~80 |

### 10.2 배포 스크립트 버전

| 스크립트 | 버전 | 마지막 커밋 |
|---------|------|-----------|
| deploy.ps1 | v1.1.0 | 7be36b6 |
| server_deploy.sh | v1.1.0 | 7be36b6 |
| docker-compose.server.yml | - | 7be36b6 |

### 10.3 관련 문서

- 배포 자동화 워크플로우: `docs/dev/phase_03_archive_runner.md`
- 동적 폴링 엔진 설계: `docs/dev/Dynamic_Polling_Engine_Design.md`
- 복구 코드 요약: `docs/RECOVERY_CODE_SUMMARY.md`

### 10.4 참고 명령어

**로컬 배포 (Design A 전전단계):**
```powershell
# Windows에서 수행 (타임스탬프 형식)
cd d:\development\prj_obs
.\scripts\deploy\deploy.ps1 -ServerHost <IP> -ImageTag 20260123-173045

# Rollback
.\scripts\deploy\deploy.ps1 -ServerHost <IP> -Rollback

# Env-only
.\scripts\deploy\deploy.ps1 -ServerHost <IP> -EnvOnly
```

**로컬 이미지 빌드/푸시 (Design A 선행 작업):**
```bash
# 아직 자동화되지 않음 - 수동 수행 필요 (타임스탬프 git tag 형식: yyyyMMdd-HHmmss)
docker build -t ghcr.io/tawbury/observer:20260123-173045 ./app/obs_deploy
docker push ghcr.io/tawbury/observer:20260123-173045
git tag 20260123-173045
git push origin 20260123-173045  # → Actions 자동 배포 트리거
```

---

## 11. 승인 및 서명

| 역할 | 이름 | 서명 | 날짜 |
|------|------|------|------|
| DevOps Auditor | - | - | 2026-01-22 |
| Engineering Manager | - | - | - |
| Platform Lead | - | - | - |

---

**문서 버전:** 1.0 (초판)  
**마지막 수정:** 2026-01-22 13:50 KST  
**상태:** 현황 분석 완료 (Design A 준비 중)
