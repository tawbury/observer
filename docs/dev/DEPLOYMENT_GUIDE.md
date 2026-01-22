# Observer 통합 배포 가이드 (모니터링 포함)

## 패키지 구성

이제 Observer 시스템은 다음을 모두 포함합니다:
- Observer 애플리케이션
- PostgreSQL 데이터베이스
- Prometheus 모니터링
- Grafana 대시보드
- Alertmanager 알림

## 디렉토리 구조

```
app/obs_deploy/
├── docker-compose.yml          # 통합 docker-compose (5개 서비스)
├── Dockerfile                  # Observer 이미지 빌드 파일
├── requirements.txt            # Python 의존성
├── monitoring/                 # 모니터링 설정
│   ├── prometheus.yml
│   ├── prometheus_alerting_rules.yaml
│   ├── alertmanager.yml
│   └── grafana_datasources.yml
├── app/                        # Observer 소스코드
├── config/                     # Observer 설정 (마운트)
├── data/                       # Observer 데이터 (마운트)
├── logs/                       # Observer 로그 (마운트)
└── secrets/                    # 인증 정보 (마운트)
```

## 로컬 테스트

```powershell
# 1. obs_deploy 디렉토리로 이동
cd app/obs_deploy

# 2. 필요한 디렉토리 생성
mkdir -p data, logs/system, config, secrets

# 3. .env 파일 생성 (secrets/.env)
# KIS API 키 등 설정

# 4. 전체 스택 시작
docker compose up -d

# 5. 상태 확인
docker compose ps

# 6. 로그 확인
docker compose logs -f observer
```

## 배포된 서비스

| 서비스 | 포트 | URL | 용도 |
|--------|------|-----|------|
| Observer API | 8000 | http://localhost:8000 | 메인 애플리케이션 |
| PostgreSQL | 5432 | localhost:5432 | 데이터베이스 |
| Prometheus | 9090 | http://localhost:9090 | 메트릭 수집 |
| Grafana | 3000 | http://localhost:3000 | 대시보드 (admin/admin) |
| Alertmanager | 9093 | http://localhost:9093 | 알림 관리 |

## Azure VM 배포

```powershell
# 1. obs_deploy 전체를 VM에 업로드
scp -r app/obs_deploy observer-vm:~/observer-deploy

# 2. VM 접속
ssh observer-vm

# 3. 배포 디렉토리로 이동
cd ~/observer-deploy

# 4. 필요한 디렉토리 생성
mkdir -p data logs/system config secrets

# 5. secrets/.env 파일 설정
nano secrets/.env

# 6. 전체 스택 시작
docker compose up -d

# 7. 상태 확인
docker compose ps

# 8. 로그 확인
docker compose logs -f observer
```

## 개별 서비스 관리

```bash
# 특정 서비스만 재시작
docker compose restart observer
docker compose restart grafana

# 특정 서비스 로그 확인
docker compose logs -f observer
docker compose logs -f prometheus

# 특정 서비스 중지
docker compose stop grafana

# 전체 중지
docker compose down

# 볼륨까지 삭제 (주의!)
docker compose down -v
```

## 모니터링 접속 정보

### Grafana
- URL: http://VM_IP:3000
- 초기 계정: admin / admin
- 첫 로그인 시 비밀번호 변경 권장

### Prometheus
- URL: http://VM_IP:9090
- Targets 확인: http://VM_IP:9090/targets
- Observer 메트릭이 수집되고 있는지 확인

### Observer API
- Health: http://VM_IP:8000/health
- Status: http://VM_IP:8000/status
- Metrics: http://VM_IP:8000/metrics

## 네트워크 설정

모든 서비스는 `observer-network`에 속해 있어서 서로 컨테이너 이름으로 통신 가능:
- Prometheus → `observer:8000/metrics` 로 메트릭 수집
- Grafana → `observer-prometheus:9090` 에서 데이터 조회
- Observer → `postgres:5432` 로 DB 연결

## 데이터 볼륨

영구 저장되는 데이터:
- `postgres_data`: PostgreSQL 데이터
- `prometheus_data`: Prometheus 메트릭 데이터
- `grafana_data`: Grafana 대시보드 설정
- `alertmanager_data`: Alertmanager 상태

호스트 마운트:
- `./data`: Observer 데이터 (Track A, B 파일)
- `./logs`: Observer 로그
- `./config`: Observer 설정
- `./secrets`: 인증 정보 (.env, KIS 토큰)

## 업데이트 방법

```bash
# 1. 최신 코드 업로드
scp -r app/obs_deploy observer-vm:~/observer-deploy-new

# 2. Observer 서비스만 재빌드
cd ~/observer-deploy
docker compose build observer
docker compose up -d observer

# 3. 또는 전체 재시작
docker compose down
cd ~/observer-deploy-new
docker compose up -d
```

## 문제 해결

### 컨테이너가 시작되지 않을 때
```bash
docker compose logs observer
docker compose ps -a
```

### 네트워크 문제
```bash
docker network inspect observer-network
```

### 포트 충돌
```bash
sudo netstat -tulpn | grep -E ':(3000|8000|9090)'
```

### 권한 문제
```bash
sudo chmod -R 777 ~/observer-deploy/logs
sudo chmod -R 777 ~/observer-deploy/data
```

## 백업

```bash
# 데이터 백업
docker compose exec postgres pg_dump -U postgres observer > backup.sql

# 볼륨 백업
docker run --rm -v observer_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

## 주요 변경사항

기존에는 Observer와 모니터링이 분리되어 있었지만, 이제 하나의 docker-compose로 통합:
- `docker-compose up -d` 한 번으로 전체 스택 배포
- 네트워크 통합으로 설정 간소화
- 모든 서비스가 동일한 라이프사이클 관리
