# Deployment Automation

**목적:** GitHub Actions & GHCR 기반 배포 자동화 정책 및 Secrets/Config 계약 정의  
**상태:** Design A 구현 중 (로컬 build/push, Actions deploy-only)  
**SSoT:** 배포 자동화 관련 단일 진실 소스

---

## 1. 배포 아키텍처

### 1.1 전체 배포 흐름
```
Git Tag Push (20YYMMDD-HHMMSS)
    ↓ (GitHub Actions trigger)
Build & Push Workflow (build-push-tag.yml)
    ├── 이미지 빌드 (Dockerfile)
    ├── 태그 검증 (20YYMMDD-HHMMSS)
    ├── GHCR 푸시 (ghcr.io/tawbury/observer)
    └── IMAGE_TAG 아티팩트 저장
    ↓ (workflow_run trigger)
Deploy Workflow (deploy-tag.yml)
    ├── IMAGE_TAG 다운로드
    ├── SSH 접속 (Azure VM/OCI)
    ├── docker-compose.server.yml 업로드
    ├── server_deploy.sh 실행
    └── Health Check (60초)
    ↓
Production Server (Azure VM/OCI)
    ├── GHCR 이미지 pull
    ├── docker-compose.server.yml 실행
    ├── last_good_tag 저장
    └── tar 백업
```

### 1.2 주요 변경사항
- ✅ 추가: `build-push-tag.yml` (빌드 & 푸시)
- ✅ 추가: `deploy-tag.yml` (배포 전용)
- ✅ 유지: `scripts/deploy/` (로컬 배포 스크립트)
- ✅ 유지: `server_deploy.sh` (서버 실행기)
- ❌ 삭제: `deploy.yml` (ACR), `terraform.yml`, `scheduled-ops.yml`
- ❌ 삭제: `infra/` Terraform 디렉토리

---

## 2. 로컬 배포 스크립트

### 2.1 배포 자동화 스크립트 위치
- `scripts/deploy/deploy.ps1` (v1.1.0) - Windows 배포 오케스트레이터
- `scripts/deploy/server_deploy.sh` (v1.1.0) - Linux 서버 실행기

### 2.2 GHCR 이미지 레퍼런스
- 레지스트리: `ghcr.io/tawbury/observer`
- 태그 패턴: 20YYMMDD-HHMMSS (예: 20250125-112345)
- compose 파일: `infra/docker/compose/docker-compose.server.yml`
- 이미지 필수 옵션: `${IMAGE_TAG:?IMAGE_TAG required}`

### 2.3 GitHub Actions 워크플로우

#### 2.3.1 Build & Push (build-push-tag.yml)
```yaml
# 트리거: Git tag push (20YYMMDD-HHMMSS 형식)
on:
  push:
    tags:
      - '20[0-9][0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9][0-9][0-9]'

# 주요 기능:
- 태그 형식 검증 (20YYMMDD-HHMMSS)
- Docker 이미지 빌드 (context: .)
- GHCR 푸시 (ghcr.io/tawbury/observer)
- IMAGE_TAG 아티팩트 저장
```

#### 2.3.2 Deploy (deploy-tag.yml)
```yaml
# 트리거: build-push-tag 완료 후 자동 실행
on:
  workflow_run:
    workflows: ["Build & Push Observer Image (Tag)"]
    types: [completed]

# 주요 기능:
- IMAGE_TAG 아티팩트 다운로드
- SSH 접속 (Azure VM/OCI)
- docker-compose.server.yml 업로드
- server_deploy.sh 실행
- Health Check (60초, 5초 간격)
- 자동 롤백 안내
```

### 2.4 컨테이너 배포 구성
```yaml
# docker-compose.yml 요약
services:
  observer:
    image: observer:latest
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data/observer
      - ./logs:/app/logs
      - ./config:/app/config
    environment:
      - OBSERVER_STANDALONE=1
      - PYTHONPATH=/app/src:/app
```

### 2.5 Server Deploy Script (server_deploy.sh)
```bash
# 용도: 서버에서 GHCR 이미지 배포/롤백, Compose 실행, 운영 체크
# 버전: v1.1.0
# 위치: scripts/deploy/server_deploy.sh

# 주요 기능:
- GHCR 이미지 pull 및 실행
- docker-compose.server.yml 관리
- last_good_tag 저장/복원
- tar 백업 생성
- Health Check (localhost:8000/health)
- 자동 롤백 지원

# 사용법:
./server_deploy.sh <DEPLOY_DIR> <COMPOSE_FILE> <IMAGE_TAG> <MODE>
```

### 2.6 리소스 제한
| 항목 | 제한 | 예약 |
|------|------|------|
| CPU | 1.0 | 0.5 |
| Memory | 512M | 256M |

---

## 3. Secrets & Config Contract

### 3.1 환경변수 이름 표준 (단일화)

| 표준 이름 | 비표준 이름 | 용도 | 우선순위 |
|-----------|------------|------|----------|
| `OBSERVER_STANDALONE` | `OBSERVER_STANDALONE` | Standalone 모드 | **1** |
| `PYTHONPATH` | - | 모듈 경로 | **2** |
| `OBSERVER_DATA_DIR` | - | 데이터 디렉터리 | 3 |
| `OBSERVER_LOG_DIR` | - | 로그 디렉터리 | 4 |

**계약:** `OBSERVER_STANDALONE`을 표준으로 고정, 다른 이름 사용 금지

### 3.2 설정 우선순위
1. **환경 변수** (최우선)
   - GitHub Secrets에서 주입
   - 컨테이너 실행 시 설정
2. **설정 파일** (deployment_config.json)
   - 빌드 시점에 참조
3. **기본값** (코드 내부)
   - 하위 호환성용

### 3.3 GitHub Secrets 저장 위치
| Secret 이름 | 용도 | 런타임 주입 위치 | 워크플로우 |
|-------------|------|------------------|-----------|
| `OBSERVER_STANDALONE` | Standalone 모드 | 컨테이너 환경변수 | build-push, deploy |
| `PYTHONPATH` | 모듈 경로 | 컨테이너 환경변수 | build-push, deploy |
| `KIS_API_KEY` | KIS API 인증 | 컨테이너 환경변수 | deploy |
| `KIS_API_SECRET` | KIS API 시크릿 | 컨테이너 환경변수 | deploy |
| `SSH_HOST` | 배포 서버 주소 | SSH 접속 | deploy |
| `SSH_USER` | SSH 사용자명 | SSH 접속 | deploy |
| `SSH_PRIVATE_KEY` | SSH 개인키 | SSH 인증 | deploy |
| `SSH_KNOWN_HOSTS` | SSH 호스트 키 | 보안 검증 | deploy |
| `SERVER_DEPLOY_DIR` | 배포 디렉토리 | 서버 경로 | deploy |
| `SSH_PORT` | SSH 포트 | 연결 설정 | deploy |

### 3.4 런타임 주입 방식
```yaml
# GitHub Actions 예시
env:
  OBSERVER_STANDALONE: ${{ secrets.OBSERVER_STANDALONE }}
  PYTHONPATH: ${{ secrets.PYTHONPATH }}
```

---

## 4. Path Contract (경로 계약)

### 4.1 컨테이너 내부 경로
| 경로 | 용도 | 마운트 여부 |
|------|------|------------|
| `/app` | 애플리케이션 루트 | No |
| `/app/src` | 소스 코드 | No |
| `/app/data/observer` | 데이터 저장 | Yes |
| `/app/logs` | 로그 저장 | Yes |
| `/app/config` | 설정 파일 | Yes |

### 4.2 호스트-컨테이너 매핑
| 호스트 경로 | 컨테이너 경로 | 실제 사용 |
|-------------|----------------|-----------|
| `./data` | `/app/data/observer` | **(미사용)** |
| `./logs` | `/app/logs` | 로그 저장 |
| `./config` | `/app/config` | **아카이브 저장** |

### 4.3 경로 정합성 검증
```bash
# 컨테이너 내부 확인
docker exec observer ls -la /app/config/

# 호스트 확인
ls -la ./config/observer/

# 실제 아카이브 경로
# config/observer/observer.jsonl (정상)
# data/observer/observer.jsonl (오류)
```

---

## 5. 배포 설정 파일

### 5.1 deployment_config.json 구조
```json
{
    "deployment": {
        "version": "1.0.0",
        "structure": "/app",
        "mode": "standalone"
    },
    "paths": {
        "data_dir": "/app/data/observer",
        "log_dir": "/app/logs",
        "config_dir": "/app/config"
    },
    "environment": {
        "OBSERVER_STANDALONE": "1",
        "PYTHONPATH": "/app/src:/app",
        "OBSERVER_DATA_DIR": "/app/data/observer",
        "OBSERVER_LOG_DIR": "/app/logs"
    }
}
```

### 5.2 Dockerfile 환경변수
```dockerfile
ENV OBSERVER_STANDALONE=1
ENV PYTHONPATH=/app/src:/app
ENV OBSERVER_DATA_DIR=/app/data/observer
ENV OBSERVER_LOG_DIR=/app/logs
```

---

## 6. 헬스체크 및 모니터링

### 6.1 컨테이너 헬스체크
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import sys; sys.exit(0)" || exit 1
```

### 6.2 포트 8000 상태
- **현재 상태:** EXPOSE 선언만, 실제 서비스 미구현
- **향후 계획:** 헬스체크/메트릭 엔드포인트

### 6.3 배포 성공 기준
- [ ] 컨테이너 실행 상태 healthy
- [ ] `config/observer/` 디렉터리 생성
- [ ] Observer 프로세스 시작 로그 확인
- [ ] 환경변수 정상 주입 확인

---

## 7. 롤백 및 장애 대응

### 7.1 롤백 절차
1. 이전 Docker 이미지로 퇴출
2. Terraform state 복원
3. 데이터 볼륨 확인
4. 헬스체크 통과 확인

### 7.2 장애 대응 체크리스트
- [ ] 컨테이너 재시작 여부 확인
- [ ] 볼륨 마운트 상태 확인
- [ ] 환경변수 주입 상태 확인
- [ ] 디스크 공간 확인
- [ ] 네트워크 연결 확인

---

## 8. 보안 정책

### 8.1 Secrets 관리
- **저장:** GitHub Secrets
- **주입:** 런타임 환경변수
- **금지:** 로그에 시크릿 기록 금지
- **순환:** 위반 시 즉시 폐기/재생성

### 8.2 이미지 보안
- **베이스:** `python:3.11-slim` (공식)
- **사용자:** `observer` (non-root)
- **권한:** 최소 권한 원칙

---

## 10. GitHub Actions 워크플로우 상세

### 10.1 Build & Push (build-push-tag.yml)
- **트리거**: Git tag (20YYMMDD-HHMMSS)
- **기능**: 태그 검증, 이미지 빌드, GHCR 푸시, 아티팩트 저장
- **Dockerfile**: infra/docker/docker/Dockerfile
- **Registry**: ghcr.io/tawbury/observer

### 10.2 Deploy (deploy-tag.yml)
- **트리거**: build-push-tag 완료 후 자동
- **기능**: IMAGE_TAG 수신, SSH 배포, Health Check
- **Health Check**: 60초, 5초 간격
- **롤백**: 실패 시 자동 안내

### 10.3 필수 Secrets
- `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY`
- `SERVER_DEPLOY_DIR`, `SSH_PORT`
- `SSH_KNOWN_HOSTS` (보안)

---

## 11. 배포 테스트

### 11.1 로컬 테스트
```bash
# 이미지 빌드 테스트
docker build -f infra/docker/docker/Dockerfile -t test:latest .

# Compose 테스트
docker-compose -f infra/docker/compose/docker-compose.server.yml config
```

### 11.2 배포 검증 체크리스트
- [ ] 태그 형식: 20YYMMDD-HHMMSS
- [ ] 이미지 빌드 성공
- [ ] GHCR 푸시 성공
- [ ] SSH 접속 가능
- [ ] Health Check 통과
- [ ] 로그 정상 생성

---

## 12. 운영 가이드

### 12.1 수동 배포
```bash
# 1. 이미지 빌드
docker build -t observer:latest .

# 2. 컨테이너 실행
docker-compose up -d

# 3. 상태 확인
docker ps
docker logs observer
```

### 12.2 환경변수 점검
```bash
# 컨테이너 내부 환경변수 확인
docker exec observer env | grep OBSERVER

# paths.py 경로 확인
docker exec observer python -c "from paths import observer_asset_dir; print(observer_asset_dir())"
```

### 12.3 디버깅 명령어
```bash
# 실시간 로그
docker logs -f observer

# 컨테이너 접속
docker exec -it observer /bin/bash

# 파일 시스템 확인
docker exec observer find /app -name "*.jsonl"
```

---

## 10. 개선 필요사항

### 10.1 즉시 개선
1. 환경변수 이름 표준화 적용
2. Path Contract 문서화 강화
3. 헬스체크 엔드포인트 구현

### 10.2 중기 개선
1. Prometheus/Grafana 모니터링
2. 자동 롤백 파이프라인
3. Blue-Green 배포 전환

---

**SSoT 선언:** 이 문서는 Observer 배포 자동화의 단일 진실 소스입니다. 모든 환경변수, 경로, 배포 절차는 이 문서를 기준으로 합니다.
