# Docker 이미지 버전 관리 및 롤백 전략

이 문서는 QTS Ops 프로젝트의 Docker 이미지 버전 관리 및 롤백(복구) 전략을 정리합니다.

## 1. 현재 이미지 태깅 정책 (Design A)

### 1.1 태그 표준화
- 타임스탐프 git tag (yyyyMMdd-HHmmss 형식, 예: 20260123-173045) = GHCR 이미지 태그
- 로컬에서 `docker build -t ghcr.io/tawbury/observer:20260123-173045`으로 빌드
- GHCR에 push: `docker push ghcr.io/tawbury/observer:20260123-173045`

### 1.2 이미지 저장소
- Registry: GHCR (`ghcr.io/tawbury/observer`)
- 태그 기반 버전 관리 (타임스탐프: yyyyMMdd-HHmmss 형식)

## 2. 롤백 절차

### 2.1 자동 롤백 (권장)
```powershell
# Windows에서 이전 버전으로 자동 롤백
.\scripts\deploy\deploy.ps1 -ServerHost <IP> -Rollback

# 동작:
# 1. server_deploy.sh가 last_good_tag 파일에서 이전 버전 읽음
# 2. GHCR에서 해당 이미지 pull
# 3. docker-compose.server.yml로 배포
# 4. 성공 시 새 last_good_tag 파일 생성
```

### 2.2 수동 롤백
```bash
# 서버에서 직접 실행
cd /home/azureuser/observer-deploy
IMAGE_TAG=20260123-173045 bash scripts/deploy/server_deploy.sh . docker-compose.server.yml 20260123-173045 deploy

# 또는 GHCR에서 이미지 태그 확인 후 ImageTag 지정
.\scripts\deploy\deploy.ps1 -ServerHost <IP> -ImageTag 20260123-173045
```

## 3. 배포 히스토리 추적

### 3.1 last_good_tag 파일
```
/home/azureuser/observer-deploy/runtime/state/last_good_tag
```
- 마지막 성공 배포의 이미지 태그 저장
- 롤백 시 자동으로 읽힘

### 3.2 tar 백업 위치
```
/home/azureuser/observer-deploy/backups/archives/
observer-image_20260123-173045.tar  (최근 3개만 유지)
observer-image_20260122-154230.tar
observer-image_20260121-120015.tar
```

## 4. 참고 사항

⚠️ **변경사항:**
- 레거시 ACR 기반 배포 (`deploy.yml`) 제거
- Terraform 기반 인프라 자동화 제거
- 현재: GHCR 기반 타임스탐프 태그 (yyyyMMdd-HHmmss) + deploy-only Actions (준비 중)
