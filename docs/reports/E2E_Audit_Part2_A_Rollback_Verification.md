# GHCR 배포 체인 E2E 감사 보고서 - Part 2-A: 롤백 검증 (BLOCKED)

**생성 일시**: 2026-01-23 17:15 KST  
**담당자**: DevOps E2E Executor + Auditor  
**상태**: ⚠️ **BLOCKED** - GHCR 인증 문제로 진행 불가

---

## 📋 요약

Part 2-A 롤백 E2E 검증을 시작했으나, **중대한 인프라 문제**를 발견했습니다:

### 발견된 문제
1. ❌ **Part 1-F "성공"은 가짜 성공이었음**
   - 워크플로는 GHCR 태그 배포를 호출했다고 보고
   - 실제로는 서버의 구버전 스크립트가 로컬 이미지만 재시작
   - GHCR에서 이미지를 pull한 적 없음

2. ❌ **서버의 `server_deploy.sh`가 구버전 (v1.0.0)**
   - IMAGE_TAG 파라미터를 지원하지 않음
   - GHCR pull 로직 없음
   - 로컬 .tar 파일만 처리

3. ❌ **GHCR 인증 만료/권한 부족**
   - 서버에서 `docker pull ghcr.io/tawbury/observer:TAG` 시도 시 403 Forbidden
   - 기존 인증 토큰이 만료되었거나 권한 부족

---

## 🔍 상세 분석

### 1. 베이스라인 검증 결과

#### 현재 실행 중인 컨테이너
```bash
$ ssh azureuser@20.200.145.7 "docker ps --filter 'name=observer'"

NAMES                IMAGE                        STATUS
observer             obs_deploy-observer:latest   Up 8 minutes (unhealthy)
observer-postgres    postgres:15-alpine           Up 8 minutes (healthy)
```

**문제점**:
- 이미지가 `obs_deploy-observer:latest` (로컬 빌드)
- GHCR 태그(`ghcr.io/tawbury/observer:20260123-170510`)가 아님
- Docker는 "unhealthy"로 표시 (하지만 API는 200 OK 응답)

#### Health Check 결과
```bash
$ curl http://localhost:8000/health
{"status":"healthy","timestamp":"2026-01-23T08:14:34.399934","uptime_seconds":530.58}
✅ Health check: 200 OK
```
→ API는 정상 작동하지만 Docker health check와 불일치

---

### 2. 서버 스크립트 버전 불일치

#### 서버의 구버전 스크립트 (v1.0.0)
```bash
# 인자 구조
DEPLOY_DIR="${1:-.}"
COMPOSE_FILE="${2:-docker-compose.server.yml}"
IMAGE_TAR="${3:-observer-image.tar}"    # ← TAR 파일 경로 (태그 아님)
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
```

**문제**:
- 3번 인자가 IMAGE_TAR (로컬 .tar 파일 경로)
- IMAGE_TAG 개념이 없음
- GHCR pull 로직 없음

#### 로컬의 신버전 스크립트 (v1.1.0)
```bash
# 인자 구조
DEPLOY_DIR="${1:-.}"
COMPOSE_FILE="${2:-docker-compose.server.yml}"
IMAGE_TAG_INPUT="${3:-}"                 # ← GHCR 이미지 태그
MODE="${4:-deploy}"                      # ← deploy/rollback 모드
IMAGE_NAME="ghcr.io/tawbury/observer"
```

**차이**:
- GHCR 이미지 pull 지원
- 롤백 모드 지원 (last_good_tag 기반)
- 환경 변수 기반 이미지 태그 설정

---

### 3. Part 1-F "성공"의 실체

#### Part 1-F 워크플로 호출 (Run #21279087323)
```yaml
script: |
  cd "$DEPLOY_DIR"
  ./server_deploy.sh "$DEPLOY_DIR" docker-compose.server.yml "$IMAGE_TAG" deploy
```
→ `IMAGE_TAG="20260123-170510"`을 3번 인자로 전달

#### 서버 스크립트가 실제로 한 일
```bash
IMAGE_TAR="${3:-observer-image.tar}"  # 3번 인자를 IMAGE_TAR로 해석
# IMAGE_TAR="20260123-170510"

if [ ! -f "$DEPLOY_DIR/$IMAGE_TAR" ]; then
    log_warn "이미지 TAR 파일 없음: $DEPLOY_DIR/$IMAGE_TAR (기존 이미지 사용)"
    return 0  # ← 여기서 리턴 (새 이미지 pull 없이 스킵)
fi
```

**결과**:
1. 스크립트는 "20260123-170510"을 파일명으로 해석
2. 해당 파일이 없으므로 경고만 출력하고 스킵
3. 기존 이미지 `obs_deploy-observer:latest` 그대로 재시작
4. 워크플로는 "배포 완료 ✅" 메시지를 보고 성공으로 판단

**증거**:
- Part 1-F 로그에 "[WARN] 이미지 TAR 파일 없음" 경고가 있었을 것
- `docker ps` 결과가 여전히 `obs_deploy-observer:latest`

---

### 4. GHCR 인증 문제

#### 시도한 배포
```bash
$ ssh azureuser@20.200.145.7 "cd /home/azureuser/observer-deploy && \
  ./server_deploy.sh /home/azureuser/observer-deploy docker-compose.server.yml 20260123-170510 deploy"

[INFO] === Docker 이미지 Pull 중 ===
Error response from daemon: unknown: failed to resolve reference 
"ghcr.io/tawbury/observer:20260123-170510": unexpected status 
from HEAD request to https://ghcr.io/v2/tawbury/observer/manifests/20260123-170510: 
403 Forbidden

[ERROR] 이미지 Pull 실패: ghcr.io/tawbury/observer:20260123-170510
```

#### 현재 서버 인증 상태
```bash
$ ssh azureuser@20.200.145.7 "cat ~/.docker/config.json"
{
  "auths": {
    "ghcr.io": {
      "auth": "dGF3YnVyeTpnaG9fdXZzRjh2UzFwTHl2R1BkdmRnbzZBSHhmNjN0dk1kMG9FTG1W"
    }
  }
}
```
→ 인증 정보는 있지만 403 Forbidden 발생

**원인 후보**:
1. PAT(Personal Access Token)가 만료됨
2. PAT 권한이 `read:packages` 없음
3. GHCR 이미지가 private이고 토큰이 접근 권한 없음
4. 토큰 소유자와 리포지토리 소유자 불일치

---

## 🛠 수정 조치 (진행 중)

### 조치 1: 서버 스크립트 업데이트 ✅
```bash
$ scp scripts/deploy/server_deploy.sh azureuser@20.200.145.7:/home/azureuser/observer-deploy/
$ ssh azureuser@20.200.145.7 "chmod +x /home/azureuser/observer-deploy/server_deploy.sh"
```
→ v1.1.0 (GHCR 지원 버전) 배포 완료

### 조치 2: docker-compose.server.yml 수정 ✅
```bash
$ ssh azureuser@20.200.145.7 \
  "sed -i 's|image: obs_deploy-observer:latest|image: ghcr.io/tawbury/observer:\${IMAGE_TAG:-latest}|' \
   /home/azureuser/observer-deploy/docker-compose.server.yml"
```
→ GHCR 이미지 사용하도록 수정

### 조치 3: GHCR 인증 해결 ❌ BLOCKED
**현재 상태**: 403 Forbidden으로 이미지 pull 불가

**필요한 조치**:
1. GitHub에서 새 PAT 생성 (`read:packages` 권한 포함)
2. 서버에서 재인증:
   ```bash
   echo $NEW_PAT | docker login ghcr.io -u tawbury --password-stdin
   ```
3. 또는 GHCR 이미지를 public으로 변경

---

## ⚠️ 블로커 (BLOCKED)

### 블로커 1: GHCR 인증 실패
**증상**: `docker pull ghcr.io/tawbury/observer:TAG` 시 403 Forbidden  
**영향**: 롤백 테스트 진행 불가 (이미지 pull 필수)  
**필수 조치**:
- 옵션 A: 새 GitHub PAT 생성 후 서버 재인증
- 옵션 B: GHCR 이미지를 public으로 변경
- 옵션 C: GitHub Actions에서만 배포 (runner가 GHCR 접근 가능)

### 블로커 2: Part 1-F 재검증 필요
**증상**: Part 1-F "성공"이 실제로는 로컬 이미지 재시작이었음  
**영향**: 전체 E2E 체인이 아직 검증되지 않음  
**필수 조치**:
- GHCR 인증 해결 후 Part 1-F 재실행
- 실제 GHCR 이미지 pull 및 배포 검증

---

## 📊 현재 상태 요약

| 항목 | 상태 | 비고 |
|------|------|------|
| 서버 스크립트 버전 | ✅ v1.1.0 | GHCR 지원 버전 업데이트 완료 |
| docker-compose.yml | ✅ 수정됨 | GHCR 이미지 사용하도록 변경 |
| GHCR 인증 | ❌ 실패 | 403 Forbidden (토큰 만료/권한 부족) |
| 현재 실행 이미지 | ⚠️ 로컬 빌드 | `obs_deploy-observer:latest` (GHCR 아님) |
| API Health Check | ✅ 200 OK | 서비스는 정상 작동 중 |
| Docker Health Status | ❌ unhealthy | Health check 설정 문제 가능성 |

---

## 🎯 다음 단계 (Required Actions)

### 우선순위 1: GHCR 인증 해결
1. GitHub 설정 확인:
   - https://github.com/settings/tokens
   - 새 PAT 생성 (`read:packages`, `write:packages` 권한)
   - 만료일 최소 90일 설정

2. 서버 재인증:
   ```bash
   ssh azureuser@20.200.145.7
   echo $NEW_PAT | docker login ghcr.io -u tawbury --password-stdin
   docker logout ghcr.io  # 기존 만료 토큰 제거
   echo $NEW_PAT | docker login ghcr.io -u tawbury --password-stdin
   ```

3. Pull 테스트:
   ```bash
   docker pull ghcr.io/tawbury/observer:20260123-170510
   ```

### 우선순위 2: Part 1-F 재검증
GHCR 인증 해결 후:
1. 새 태그 생성 (예: `20260123-173000`)
2. GitHub Actions 워크플로 실행
3. 서버에서 실제 GHCR 이미지가 pull되었는지 확인:
   ```bash
   docker images | grep ghcr.io/tawbury/observer
   docker ps --format "{{.Image}}"
   ```

### 우선순위 3: 롤백 E2E 테스트
인증 및 배포 검증 후:
1. 최신 태그 배포 (`20260123-173000`)
2. 이전 태그로 롤백 (`20260123-170510`)
3. Health check 검증
4. 컨테이너 이미지 태그 확인

---

## 📝 교훈 (Lessons Learned)

### 1. 가짜 성공 (False Positive)
- **문제**: 워크플로 로그에 "배포 완료 ✅"가 있어도 실제 검증 필요
- **원인**: 스크립트 버전 불일치로 인한 silent failure
- **해결**: 배포 후 반드시 `docker ps --format "{{.Image}}"` 확인

### 2. 인터페이스 계약 불일치
- **문제**: 워크플로는 새 인터페이스 호출, 서버는 구 인터페이스 실행
- **원인**: 스크립트 배포 누락 (CI/CD에 포함되지 않음)
- **해결**: 스크립트도 버전 관리 및 자동 배포 필요

### 3. 인증 상태 모니터링 부족
- **문제**: 서버 Docker 인증이 만료되었는데 알람 없음
- **원인**: GHCR pull이 실제로 실행되지 않아서 문제 발견 지연
- **해결**: 정기적인 `docker pull` 테스트 또는 토큰 만료 알람

---

## 🔗 관련 문서

- [Part 1-F: 워크플로 수정 검증](./E2E_Audit_Part1_F_Workflow_Hotfix_Verification.md) ← 재검증 필요
- [GitHub GHCR 문서](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker Login 문서](https://docs.docker.com/engine/reference/commandline/login/)

---

## ⏸️ 일시 중단 (PAUSED)

**중단 사유**: GHCR 인증 문제로 롤백 테스트 진행 불가  
**재개 조건**: GitHub PAT 생성 및 서버 재인증 완료  
**예상 소요 시간**: 인증 해결 후 30분 (재배포 + 롤백 테스트)

**다음 작업 시작 시 필요한 정보**:
- 새 GitHub PAT (read:packages 권한)
- 최신 배포된 GHCR 태그 (재검증용)
- 롤백 대상 태그 (이전 버전)

---

**보고서 끝**

*Generated by DevOps E2E Audit System - Part 2-A (Rollback Verification - BLOCKED)*  
*블로커 해결 후 Part 2-A를 재개하거나 Part 2-B (인증 해결)로 분기 예정*
