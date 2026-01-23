# Deployment Automation

**목적:** GitHub Actions & GHCR 기반 배포 자동화 정책 및 Secrets/Config 계약 정의  
**상태:** Design A 구현 중 (로컬 build/push, Actions deploy-only)  
**SSoT:** 배포 자동화 관련 단일 진실 소스

---

## 1. 배포 구조 (Design A)

### 1.1 배포 흐름
```
로컬 개발 환경
    ↓ (docker build → docker push GHCR)
    ↓ (git tag v1.2.3)
GitHub Repository
    ↓ (Tag push trigger)
GitHub Actions (Deploy-only)
    ├── 이미지 태그 추출
    ├── 서버 SSH 접근
    └── server_deploy.sh 실행
    ↓
Azure VM (Production)
    ↓ (server_deploy.sh)
    ├── GHCR 이미지 pull
    ├── docker-compose.server.yml 실행
    ├── last_good_tag 저장
    └── tar 백업
```

### 1.2 주요 변경사항
- ❌ 삭제: `deploy.yml` (ACR), `terraform.yml`, `scheduled-ops.yml`
- ❌ 삭제: `infra/` Terraform 디렉토리
- ✅ 유지: `scripts/deploy/` (로컬 배포 스크립트)
- ✅ 준비: GitHub Actions deploy-only 워크플로우 (추후 작성)

---

## 2. 로컬 배포 스크립트

### 2.1 배포 자동화 스크립트 위치
- `scripts/deploy/deploy.ps1` (v1.1.0) - Windows 배포 오케스트레이터
- `scripts/deploy/server_deploy.sh` (v1.1.0) - Linux 서버 실행기

### 2.2 GHCR 이미지 레퍼런스
- 레지스트리: `ghcr.io/tawbury/observer`
- 태그 패턴: git tag (예: v1.2.3)
- compose 파일: `app/obs_deploy/docker-compose.server.yml`
- 이미지 필수 옵션: `${IMAGE_TAG:?IMAGE_TAG required}`

### 2.2 컨테이너 배포 구성
```yaml
# docker-compose.yml 요약
services:
  qts-observer:
    image: observer:latest
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data/observer
      - ./logs:/app/logs
      - ./config:/app/config
    environment:
      - QTS_OBSERVER_STANDALONE=1
      - PYTHONPATH=/app/src:/app
```

### 2.3 리소스 제한
| 항목 | 제한 | 예약 |
|------|------|------|
| CPU | 1.0 | 0.5 |
| Memory | 512M | 256M |

---

## 3. Secrets & Config Contract

### 3.1 환경변수 이름 표준 (단일화)

| 표준 이름 | 비표준 이름 | 용도 | 우선순위 |
|-----------|------------|------|----------|
| `QTS_OBSERVER_STANDALONE` | `OBSERVER_STANDALONE` | Standalone 모드 | **1** |
| `PYTHONPATH` | - | 모듈 경로 | **2** |
| `OBSERVER_DATA_DIR` | - | 데이터 디렉터리 | 3 |
| `OBSERVER_LOG_DIR` | - | 로그 디렉터리 | 4 |

**계약:** `QTS_OBSERVER_STANDALONE`을 표준으로 고정, 다른 이름 사용 금지

### 3.2 설정 우선순위
1. **환경 변수** (최우선)
   - GitHub Secrets에서 주입
   - 컨테이너 실행 시 설정
2. **설정 파일** (deployment_config.json)
   - 빌드 시점에 참조
3. **기본값** (코드 내부)
   - 하위 호환성용

### 3.3 GitHub Secrets 저장 위치
| Secret 이름 | 용도 | 런타임 주입 위치 |
|-------------|------|------------------|
| `QTS_OBSERVER_STANDALONE` | Standalone 모드 | 컨테이너 환경변수 |
| `PYTHONPATH` | 모듈 경로 | 컨테이너 환경변수 |
| `KIS_API_KEY` | KIS API 인증 | 컨테이너 환경변수 |
| `KIS_API_SECRET` | KIS API 시크릿 | 컨테이너 환경변수 |

### 3.4 런타임 주입 방식
```yaml
# GitHub Actions 예시
env:
  QTS_OBSERVER_STANDALONE: ${{ secrets.QTS_OBSERVER_STANDALONE }}
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
docker exec qts-observer ls -la /app/config/

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
        "QTS_OBSERVER_STANDALONE": "1",
        "PYTHONPATH": "/app/src:/app",
        "OBSERVER_DATA_DIR": "/app/data/observer",
        "OBSERVER_LOG_DIR": "/app/logs"
    }
}
```

### 5.2 Dockerfile 환경변수
```dockerfile
ENV QTS_OBSERVER_STANDALONE=1
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
- **사용자:** `qts` (non-root)
- **권한:** 최소 권한 원칙

---

## 9. 운영 가이드

### 9.1 수동 배포
```bash
# 1. 이미지 빌드
docker build -t observer:latest .

# 2. 컨테이너 실행
docker-compose up -d

# 3. 상태 확인
docker ps
docker logs qts-observer
```

### 9.2 환경변수 점검
```bash
# 컨테이너 내부 환경변수 확인
docker exec qts-observer env | grep OBSERVER

# paths.py 경로 확인
docker exec qts-observer python -c "from paths import observer_asset_dir; print(observer_asset_dir())"
```

### 9.3 디버깅 명령어
```bash
# 실시간 로그
docker logs -f qts-observer

# 컨테이너 접속
docker exec -it qts-observer /bin/bash

# 파일 시스템 확인
docker exec qts-observer find /app -name "*.jsonl"
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
