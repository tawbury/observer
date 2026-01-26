# Observer 배포 자동화 스크립트 사용 설명서

## 개요

Observer 서비스를 로컬 환경에서 서버로 배포하는 자동화 스크립트입니다.

- **deploy.ps1**: 로컬 Windows PowerShell 오케스트레이터
- **server_deploy.sh**: 서버 Linux Bash 러너

## 전제 조건

### 로컬 (Windows)
- PowerShell 5.0 이상
- SSH 클라이언트 (OpenSSH)
- SCP 명령어
- 서버 SSH 키 (`~/.ssh/id_rsa`)

### 서버 (Linux/Azure VM)
- Docker & Docker Compose
- Bash 셸
- 배포 디렉토리: `/home/azureuser/observer-deploy` (기존)
- 포트 8000 (API), 5432 (PostgreSQL) 개방

## 필수 로컬 파일 및 위치

배포 전 다음 파일들이 `app/obs_deploy/` 디렉토리에 준비되어야 합니다:

```
app/obs_deploy/
├── .env.server                  # 서버 환경 변수 (KIS 자격증명 포함)
├── env.template                 # 환경 변수 템플릿 (검증용)
├── observer-image.tar           # Docker 이미지 (121MB)
├── docker-compose.server.yml    # 서버 Compose 정의
└── env.template                 # 검증 기준 파일
```

### .env.server 파일 준비

```bash
# 기본 템플릿에서 시작
cp app\obs_deploy\env.template app\obs_deploy\.env.server

# 실제 값 채우기 (필수)
# - KIS_APP_KEY
# - KIS_APP_SECRET
# - DB_PASSWORD (기본값: observer_db_pwd)
```

### 자격증명 마스킹 정책

스크립트 실행 중:
- **절대 출력 금지**: SECRET 값, 자격증명
- **로그에 기록**: KEY 이름만, 값은 마스킹 (****)
- **백업 파일**: 서버에만 보관 (`.env.bak-YYYYMMDD-HHMMSS`)

## 사용 방법

### 빌드 태그 생성

Docker 이미지 빌드 전에 타임스탬프 기반 태그를 생성합니다:

```powershell
# 기본 사용 (태그를 stdout으로 출력)
.\scripts\deploy\generate_build_tag.ps1

# 파일로 저장
.\scripts\deploy\generate_build_tag.ps1 -OutputFile "BUILD_TAG.txt"

# 변수로 캡처
$BUILD_TAG = .\scripts\deploy\generate_build_tag.ps1 | Select-Object -Last 1

# Linux/Bash 환경
./scripts/deploy/generate_build_tag.sh
./scripts/deploy/generate_build_tag.sh -o BUILD_TAG.txt
```

**태그 형식**: `20YYMMDD-HHMMSS` (예: 20260126-155945)

### 기본 실행

```powershell
cd d:\development\prj_obs

# 기본 설정 (서버 정보 사전 구성)
.\scripts\deploy\deploy.ps1

# 또는 서버 정보와 함께 실행
.\scripts\deploy\deploy.ps1 `
    -ServerHost "your.server.ip" `
    -SshUser "azureuser" `
    -SshKeyPath "$env:USERPROFILE\.ssh\id_rsa" `
    -DeployDir "/home/azureuser/observer-deploy" `
    -ComposeFile "docker-compose.server.yml"
```

### 매개변수 설명

| 매개변수 | 기본값 | 설명 |
|---------|-------|------|
| `-ServerHost` | `your_server_ip` | 서버 IP 또는 호스트명 |
| `-SshUser` | `azureuser` | SSH 로그인 사용자 |
| `-SshKeyPath` | `~/.ssh/id_rsa` | SSH 개인 키 경로 |
| `-DeployDir` | `/home/azureuser/observer-deploy` | 서버 배포 디렉토리 |
| `-ComposeFile` | `docker-compose.server.yml` | Compose 정의 파일명 |
| `-LocalEnvFile` | `app\obs_deploy\.env.server` | 로컬 환경 파일 |
| `-EnvTemplate` | `app\obs_deploy\env.template` | 환경 템플릿 파일 |
| `-ArtifactDir` | `app\obs_deploy` | 아티팩트 디렉토리 |

### 배포 단계 상세

#### 1️⃣ 로컬 환경 검증
- `env.template` 파일 존재 확인
- `.env.server` 파일 존재 확인
- 필수 KEY 존재 여부 확인
- KIS 자격증명 값 존재 여부 확인

실패 케이스:
```
❌ 필수 키 누락: KIS_APP_KEY, KIS_APP_SECRET
```

#### 2️⃣ 아티팩트 검증
- `observer-image.tar` 존재 및 크기 확인 (121MB)
- `docker-compose.server.yml` 존재 확인
- `.env.server` 존재 확인

#### 3️⃣ SSH 연결 테스트
- SSH 키 권한 확인
- SSH 서버 연결 테스트 (`ConnectTimeout=5s`)
- SSH 키 인증 방식 (암호 불필요)

#### 4️⃣ 서버 배포 디렉토리 검증
- `/home/azureuser/observer-deploy` 존재 확인

#### 5️⃣ 서버 .env 파일 백업
- 기존 `.env` → `.env.bak-YYYYMMDD-HHMMSS` 복사
- 롤백용 백업 (자동 생성)

#### 6️⃣ .env 파일 업로드
- 로컬 `.env.server` → 서버 `.env` (임시 파일로 먼저 업로드)
- 원자적 교체 (`.env.tmp` → `.env`)
- 권한 강제 설정: `chmod 600`

#### 7️⃣ 아티팩트 업로드
- `observer-image.tar`
- `docker-compose.server.yml`
- 기타 필요 파일

#### 8️⃣ 서버 배포 스크립트 실행
- `scripts/deploy/server_deploy.sh` 업로드
- 서버에서 실행:
  1. Docker 이미지 로드
  2. 필수 디렉토리 생성
  3. Docker Compose 시작
  4. 상태 확인 & 로그 확인

#### 9️⃣ Post-Deploy 헬스 체크
- `curl http://localhost:8000/health` (200 OK 확인)
- Docker Compose 상태 확인

## 로그 및 결과

### 로컬 로그
```
ops/run_records/deploy_YYYYMMDD-HHMMSS.log
```

내용:
- 각 단계별 성공/실패 여부
- 오류 메시지 (자격증명 제외)
- 최종 배포 요약

### 서버 로그
```bash
# 최근 로그 확인
docker logs observer --tail 100

# 실시간 모니터링
docker compose logs -f observer
```

### 권장 검증 명령어
```bash
# 1. Compose 상태
docker compose ps

# 2. Health endpoint
curl -v http://localhost:8000/health

# 3. Status 확인
curl http://localhost:8000/status

# 4. Database 연결 확인
docker compose logs postgres | tail 20

# 5. 환경 변수 로드 확인 (키 개수만)
docker exec observer env | grep KIS | wc -l
```

## 롤백 절차

### 수동 롤백 (권장)

#### 옵션 A: 환경 변수 복구
```bash
# 서버에서:
cd /home/azureuser/observer-deploy
cp .env.bak-YYYYMMDD-HHMMSS .env
docker compose restart observer
```

#### 옵션 B: 이미지 이전 버전 사용
```bash
# 이전 이미지 태그로 Compose 파일 수정 또는
docker tag obs_deploy-observer:previous-tag obs_deploy-observer:latest
docker compose up -d observer
```

#### 옵션 C: 전체 스택 재배포
```bash
# 로컬에서 재배포:
.\scripts\deploy\deploy.ps1 -ServerHost "..."
```

## 보안 규칙

### ✅ 필수 준수 사항

1. **비밀 값 보호**
   - 스크립트 실행 결과에 SECRET 값 절대 노출 금지
   - 로그 파일에도 값 기록 금지
   - KEY 이름만 로그에 기록

2. **권한 관리**
   - 서버 `.env` 파일: 항상 `chmod 600`
   - SSH 키 파일: `chmod 600` 유지
   - 배포 스크립트: `chmod +x` 자동 처리

3. **서버 코드 불변성**
   - 서버에서 소스 코드 수정 금지 (배포 전용)
   - 모든 코드 변경은 로컬에서만 수행
   - 이미지 재빌드 → 재배포 프로세스

4. **백업 유지**
   - 기존 `.env` 자동 백업 (덮어쓰기 전)
   - 백업 파일명에 타임스탐프 포함
   - 서버에 최소 3개월 보관 권장

### ❌ 금지 사항

- SSH 연결 시 비밀번호 방식 (키만 사용)
- .env 파일을 버전 관리에 커밋
- 스크립트 실행 로그에 자격증명 저장
- 서버 직접 코드 수정

## 자동화 스크립트 위치 구조

```
scripts/
└── deploy/
    ├── deploy.ps1                    # Windows PowerShell 배포 오케스트레이터
    ├── server_deploy.sh              # Linux Bash 서버 배포 러너
    ├── generate_build_tag.ps1        # PowerShell 빌드 태그 생성기
    ├── generate_build_tag.sh         # Bash 빌드 태그 생성기
    ├── sync_to_oracle.ps1            # Oracle Cloud 동기화 스크립트
    ├── oci_helpers.ps1               # OCI 헬퍼 함수
    ├── oci_launch_instance.ps1       # OCI 인스턴스 시작
    ├── setup_env_secure.sh           # 보안 환경 설정
    ├── migrate.sh                    # 마이그레이션 스크립트
    ├── oracle_bootstrap.sh           # Oracle 부트스트랩
    ├── cloud-init-docker.yaml        # Cloud-init 설정
    ├── QUICKSTART.md                 # 빠른 시작 가이드
    ├── IMPLEMENTATION_REPORT.md      # 구현 보고서
    └── README.md                     # 이 파일
```

## 확장 계획 (v2 이상)

### 선택적 기능
- YAML 기반 타겟 설정 (`.ai/runtime/targets.yml`)
- 자동 롤백 (이전 이미지 태그 유지)
- 배포 전 자동 이미지 재빌드
- ACR/Registry 기반 배포 (향후)

### 개선 예정
- Slack/이메일 알림 통합
- 배포 메트릭 수집 (시간, 데이터 크기)
- 다중 서버 병렬 배포
- Blue-Green 배포 패턴 지원

## 문제 해결

### SSH 연결 실패
```
❌ SSH 연결 실패 (exit code: 255)
```

원인 및 해결:
1. SSH 키 경로 확인: `Test-Path $env:USERPROFILE\.ssh\id_rsa`
2. SSH 키 권한 확인: Windows의 경우 ACL 확인 필요
3. 서버 IP/호스트명 확인
4. 방화벽 22번 포트 개방 확인

### .env 검증 실패
```
❌ 필수 키 누락: KIS_APP_KEY, KIS_APP_SECRET
```

해결:
1. `.env.server` 파일 존재 확인
2. 필수 KEY 모두 입력 확인 (값도 확인, 빈칸 금지)
3. 파일 인코딩 UTF-8 확인

### 서버 Compose 실행 실패
```
⚠️ 서버 배포 스크립트 종료 코드: 1
```

해결:
1. 서버 직접 접속: `ssh azureuser@server-ip`
2. 로그 확인: `docker compose logs observer`
3. 필수 디렉토리 확인: `ls -la /home/azureuser/observer-deploy/`
4. Docker daemon 상태: `docker ps`

## 예시: 전체 배포 시나리오

```powershell
# 1. 로컬에서 환경 준비
cd d:\development\prj_obs
cp app\obs_deploy\env.template app\obs_deploy\.env.server

# 2. 빌드 태그 생성
$BUILD_TAG = .\scripts\deploy\generate_build_tag.ps1 -OutputFile "BUILD_TAG.txt" | Select-Object -Last 1
Write-Host "Build Tag: $BUILD_TAG"

# 3. 실제 KIS 자격증명 입력 (텍스트 에디터로)
# notepad app\obs_deploy\.env.server

# 4. 배포 실행
.\scripts\deploy\deploy.ps1 -ServerHost "your.server.ip" -ImageTag $BUILD_TAG

# 5. 로그 확인
cat ops\run_records\deploy_*.log

# 6. 서버 로그 확인
# ssh azureuser@your.server.ip
# docker logs observer --tail 100
```

## 연락처 & 지원

배포 자동화 관련 문제:
- 로컬 로그: `ops/run_records/deploy_*.log`
- 서버 로그: `docker compose logs observer`
- 문서: `scripts/deploy/README.md`

---

**마지막 업데이트**: 2026-01-26  
**버전**: v1.1.0  
**최근 변경사항**: 
- 중복 스크립트 정리 (generate_build_tag_simple.ps1, deploy_simple.ps1 제거)
- generate_build_tag.ps1 인코딩 문제 해결 및 안정화
- 배포 스크립트 구조 최적화

**관련 문서**: `.ai/workflows/deploy_automation.workflow.md`
