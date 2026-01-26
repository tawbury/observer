# Observer Repository 배포 자동화 현황 분석 보고서

**분석 기준일:** 2026-01-26  
**분석 범위:** 전체 저장소 배포 관련 파일  
**목적:** 기존 반자동화 배포 워크플로우의 오류 감소를 위한 현황 파악

---

## 1. 배포 관련 파일 인벤토리

### 📜 스크립트 파일
| 파일 경로 | 파일 타입 | 목적 | 실행 위치 | 실행 트리거 |
|-----------|-----------|------|-----------|-------------|
| `scripts/deploy/deploy.ps1` | PowerShell | Windows 로컬 배포 오케스트레이터 | 로컬 머신 | 수동 |
| `scripts/deploy/deploy_simple.ps1` | PowerShell | 간소화 배포 스크립트 | 로컬 머신 | 수동 |
| `scripts/deploy/server_deploy.sh` | Bash | 서버 배포/롤백/운영 스크립트 | 서버 | SSH/수동 |
| `scripts/deploy/sync_to_oracle.ps1` | PowerShell | Oracle 클라우드 동기화 | 로컬 머신 | 수동 |
| `scripts/deploy/oci_helpers.ps1` | PowerShell | OCI 헬퍼 함수 | 로컬 머신 | 수동 |
| `scripts/deploy/setup_env_secure.sh` | Bash | 서버 환경 설정 | 서버 | 수동 |
| `scripts/deploy/migrate.sh` | Bash | 데이터 마이그레이션 | 서버 | 수동 |
| `scripts/deploy/oracle_bootstrap.sh` | Bash | Oracle 부트스트랩 | 서버 | 수동 |

### 🐳 도커 파일
| 파일 경로 | 파일 타입 | 목적 | 실행 위치 | 실행 트리거 |
|-----------|-----------|------|-----------|-------------|
| `infra/docker/docker/Dockerfile` | Dockerfile | 컨테이너 이미지 빌드 | CI/Runner | 워크플로우 |
| `infra/docker/compose/docker-compose.yml` | Docker Compose | 로컬 개발 환경 | 로컬 머신 | 수동 |
| `infra/docker/compose/docker-compose.server.yml` | Docker Compose | 서버 배포 환경 | 서버 | server_deploy.sh |
| `infra/docker/compose/docker-compose.prod.yml` | Docker Compose | 프로덕션 환경 | 서버 | 수동 |

### 🔄 CI/CD 워크플로우
| 파일 경로 | 파일 타입 | 목적 | 실행 위치 | 실행 트리거 |
|-----------|-----------|------|-----------|-------------|
| `.github/workflows/build-push-tag.yml` | GitHub Actions | 이미지 빌드 & 푸시 | GitHub Runner | Git Tag |
| `.github/workflows/deploy-tag.yml` | GitHub Actions | 자동 배포 | GitHub Runner | 워크플로우 |

---

## 2. 현재 배포 흐름 (As-Is)

### 🔄 자동화된 흐름
1. **Git Tag Push** (20YYMMDD-HHMMSS 형식)
   - 트리거: `build-push-tag.yml` 워크플로우
   - 태그 형식 검증
   - Docker 이미지 빌드 (`infra/docker/docker/Dockerfile`)
   - GHCR 푸시 (`ghcr.io/tawbury/observer`)
   - IMAGE_TAG 아티팩트 저장

2. **자동 배포**
   - 트리거: `deploy-tag.yml` 워크플로우 (workflow_run)
   - IMAGE_TAG 아티팩트 다운로드
   - SSH 접속 (서버)
   - `docker-compose.server.yml` 업로드
   - `server_deploy.sh` 실행
   - Health Check (60초)

### 👤 수동 개입 지점
1. **로컬 개발 환경**
   - `docker-compose.yml` 직접 실행
   - 환경 변수 수동 설정

2. **서버 초기 설정**
   - `setup_env_secure.sh` 수동 실행
   - Docker 설치 및 설정
   - SSH 키 설정

3. **롤백**
   - `server_deploy.sh rollback` 수동 실행
   - Health Check 실패 시 수동 개입

---

## 3. 자동화 수준 평가

### ✅ 완전 자동화
- **이미지 빌드**: GitHub Actions 워크플로우
- **레지스트리 푸시**: GHCR 자동 푸시
- **태그 검증**: 20YYMMDD-HHMMSS 형식 자동 검증
- **Health Check**: 배포 후 자동 상태 확인

### 🔧 반자동화
- **서버 배포**: 워크플로우 트리거 + 서버 스크립트 실행
- **롤백**: 스크립트 제공 + 수동 실행 필요
- **환경 설정**: 스크립트 제공 + 수동 실행 필요

### 👤 완전 수동
- **로컬 개발**: `docker-compose.yml` 직접 관리
- **서버 초기화**: Docker, SSH, 환경 설정
- **Secrets 관리**: GitHub Secrets 수동 등록
- **데이터 마이그레이션**: `migrate.sh` 수동 실행

---

## 4. 코드에서 추출된 서버 가정

### 🐳 Docker 환경 가정
```bash
# server_deploy.sh 가정
- docker 명령어 존재
- docker-compose 명령어 존재
- /var/run/docker.sock 접근 가능
- 컨테이너 재시작 권한
```

### 📁 디렉토리 구조 가정
```bash
# 배포 디렉토리 구조
${DEPLOY_DIR}/
├── docker-compose.server.yml
├── runtime/state/
├── backups/archives/
└── logs/
```

### 🔑 SSH 및 권한 가정
```bash
# SSH 접속 가정
- SSH 키 기반 인증
- sudo 권한 (docker 실행)
- 포트 22 개방
- known_hosts 설정
```

### 🌐 네트워크 가정
```yaml
# docker-compose.server.yml 가정
- 포트 8000 외부 노출
- localhost:8000/health 접근 가능
- 외부 레지스트리 접근 (GHCR)
```

### 📦 패키지 가정
```bash
# server_deploy.sh 가정
- tar 명령어 (백업 생성)
- curl 명령어 (health check)
- jq 명령어 (JSON 처리)
```

---

## 5. 리스크 및 모호성 지점 (사실 기반)

### ⚠️ 환경 의존성 리스크
1. **Docker 버전 호환성**
   - `docker-compose` vs `docker compose` 명령어
   - 저장소 기준으로 특정 버전 명시 없음

2. **경로 가정**
   - `DEPLOY_DIR` 변수 값에 따라 동작 변경
   - 상대 경로 vs 절대 경로 혼용 가능성

3. **권한 가정**
   - sudo 권한 있는 사용자로 실행 가정
   - non-root 컨테이너 실행과의 권한 충돌 가능성

### 🔍 모호한 지점
1. **Secrets 관리**
   - GitHub Secrets와 서버 환경변수 동기화 불명확
   - KIS API 키 주입 방식 저장소 기준으로 판단 불가

2. **롤백 로직**
   - `last_good_tag` 파일 존재 가정
   - 이전 태그가 없는 경우 동작 불명확

3. **Health Check 기준**
   - HTTP 200 응답만으로 서비스 정상 상태 판단
   - 애플리케이션 레벨 헬스체크 구현 여부 불명확

### 🚨 인적 오류 가능성
1. **태그 형식**
   - 20YYMMDD-HHMMSS 형식 수준 입력 시 자동화 실패
   - 워크플로우 실패 후 수동 복구 필요

2. **환경 변수 설정**
   - `SERVER_DEPLOY_DIR` 등 필수 변수 누락 가능성
   - SSH 관련 Secrets 설정 누락 시 배포 실패

3. **수동 롤백 타이밍**
   - Health Check 실패 시 즉각적인 롤백 필요
   - 수동 개입 지연으로 서비스 장애 확대 가능성

### 📋 문서화 부족
1. **서버 요구사항**
   - 최소 사양, OS 버전, 필수 패키지 목록 부재
   - 방화벽 설정 요구사양 불명확

2. **장애 대응 절차**
   - 특정 오류 시나리오별 대응 가이드 부재
   - 로그 분석 방법론 부재

---

## 6. 분석 결론

### 📊 현재 상태 요약
- **자동화 수준**: 반자동화 (빌드/푸시 자동화, 배포 반자동화)
- **주요 리스크**: 환경 의존성, 인적 오류 가능성, 문서화 부족
- **안정성**: 워크플로우 기반 안정적이나 서버 설정 수동 의존성 높음

### 🎯 개선 방향성 (향후 고려)
1. **환경 표준화**: 서버 요구사양 명확화
2. **롤백 자동화**: Health Check 실패 시 자동 롤백
3. **문서화 강화**: 장애 대응 절차 구체화
4. **가정 제거**: 코드 내 명시적 검증 로직 추가

---

**보고서 완료: 저장소 기준 현재 상태 분석 종료**
