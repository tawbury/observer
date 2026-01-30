# 배포 가이드

## 📍 Oracle Cloud VM 서버 배포

### 1. 서버 초기화

서버에 처음 배포하거나 디렉토리 구조가 없는 경우 초기화 스크립트를 실행합니다.

```bash
# 초기화 스크립트 다운로드 및 실행
curl -O https://raw.githubusercontent.com/tawbury/observer/observer/infra/_shared/scripts/deploy/init_server_dirs.sh
chmod +x init_server_dirs.sh
./init_server_dirs.sh
```

또는 수동으로 디렉토리를 생성합니다:

```bash
# 디렉토리 구조 생성 (간소화된 구조)
mkdir -p ~/observer/config/{scalp,swing,symbols,universe}
mkdir -p ~/observer/logs/{scalp,swing,system,maintenance}
mkdir -p ~/observer/data/{scalp,swing}
mkdir -p ~/observer/secrets/.kis_cache

# 권한 설정
chmod -R 777 ~/observer/
```

### 2. Docker CMD 및 필수 환경 변수 (python -m observer)

컨테이너 기본 실행 명령은 `python -m observer`입니다. 이 진입점에서 API 서버(스레드)와 Observer Core, UniverseScheduler/Track A/B(비동기 asyncio 태스크)가 함께 동작합니다.

| 구분 | 환경 변수 | 필수 | 설명 |
|------|-----------|------|------|
| KIS | `KIS_APP_KEY` | Universe/Track A·B 사용 시 | KIS 앱 키 |
| KIS | `KIS_APP_SECRET` | Universe/Track A·B 사용 시 | KIS 앱 시크릿 |
| KIS | `KIS_IS_VIRTUAL` | 선택 | `true`/`false` (기본: false) |
| Track | `TRACK_A_ENABLED` | 선택 | `true`/`false` (기본: true) |
| Track | `TRACK_B_ENABLED` | 선택 | `true`/`false` (기본: false) |
| 경로 | `OBSERVER_DATA_DIR` | 선택 | 기본: `/app/data` |
| 경로 | `OBSERVER_LOG_DIR` | 선택 | 기본: `/app/logs` |
| 경로 | `OBSERVER_CONFIG_DIR` | 선택 | 기본: `/app/config` |

EventBus → JsonlFileSink 데이터 흐름 확인: 로그에 `EventBus dispatch count=N → sinks=[JsonlFileSink]` 가 주기적으로 출력됩니다.

### 3. KIS API 자격증명 설정 (Critical!)

**중요**: 이 설정이 없으면 Track A/B Collector가 비활성화됩니다.

```bash
# .env 파일 생성
cat > ~/observer/secrets/.env << 'EOF'
# KIS API Credentials (Real Account)
KIS_APP_KEY=your_app_key_here
KIS_APP_SECRET=your_app_secret_here
KIS_IS_VIRTUAL=false

# HTS ID (optional)
KIS_HTS_ID=your_hts_id

# Track A/B 활성화 설정
TRACK_A_ENABLED=true
TRACK_B_ENABLED=false

# Token cache (Docker 내부 경로)
KIS_TOKEN_CACHE_DIR=/app/secrets/.kis_cache
EOF

# 권한 설정 (보안)
chmod 600 ~/observer/secrets/.env
```

### 4. docker-compose.server.yml 배포

```bash
# observer-deploy 디렉토리로 이동
cd ~/observer-deploy

# 최신 docker-compose.server.yml 다운로드
curl -O https://raw.githubusercontent.com/tawbury/observer/observer/infra/_shared/compose/docker-compose.server.yml

# 이미지 태그 설정 및 배포
export IMAGE_TAG=build-YYYYMMDD-HHMMSS  # GHCR에서 확인한 태그
docker compose -f docker-compose.server.yml up -d
```

### 5. 배포 확인

```bash
# 컨테이너 상태 확인
docker ps

# KIS 자격증명 전달 확인 (Critical!)
docker exec observer env | grep KIS

# 로그 확인 - Track A/B 활성화 여부
docker logs observer --tail 30

# 예상 로그 (정상):
# INFO | Track A Collector started
# INFO | Track B Collector started (또는 disabled if TRACK_B_ENABLED=false)
```

### 6. 볼륨 마운트 확인

```bash
# 볼륨 마운트 확인
docker inspect observer --format '{{json .Mounts}}' | python3 -m json.tool

# 호스트-컨테이너 파일 동기화 테스트
docker exec observer touch /app/config/swing/test.txt
ls -la ~/observer/config/swing/
```

---

## 📍 시간대 설정 위치

### 1. Dockerfile 수정
**파일**: `infra/docker/docker/Dockerfile`
- **라인 35-37**: KST 시간대 설정 추가
```dockerfile
# 시간대 설정 (KST)
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
```

### 2. docker-compose.yml 수정
**파일**: `infra/docker/compose/docker-compose.yml`
- **라인 42-43**: KST 시간대 환경 변수 추가
```yaml
# 시간대 설정 (KST)
- TZ=Asia/Seoul
```

### 3. 배포용 docker-compose.prod.yml
**파일**: `infra/_shared/compose/docker-compose.prod.yml`
- **모든 서비스**: KST 시간대 설정 포함
- **환경 변수**: `.env.prod` 파일에서 관리

## 🚀 배포 절차

### 1. 환경 설정
```bash
# 배포 환경 변수 파일 생성
cp infra/_shared/secrets/env.prod.example infra/_shared/secrets/.env.prod

# 환경 변수 편집
nano infra/_shared/secrets/.env.prod
```

### 2. 배포 실행
```bash
# 배포용 docker-compose 사용
cd infra/_shared/compose
docker-compose -f docker-compose.prod.yml up -d --build
```

### 3. 시간대 확인
```bash
# 컨테이너 시간대 확인
docker exec observer date
docker exec observer timedatectl status

# 로그에서 시간대 확인
docker logs observer | grep -i "time\|timezone"
```

## 🔍 시간대 설정 검증

### 1. 컨테이너 내부 확인
```bash
# 시간대 파일 확인
docker exec observer cat /etc/timezone
docker exec observer ls -la /etc/localtime

# 파이썬 시간대 확인
docker exec observer python -c "import time; print(time.tzname)"
docker exec observer python -c "from datetime import datetime; print(datetime.now())"
```

### 2. 애플리케이션 로그 확인
```bash
# Track B 거래 시간 체크 로그
docker logs observer | grep -i "trading hours"

# 시간대 관련 로그
docker logs observer | grep -i "kst\|timezone\|time"
```

## 📋 배포 체크리스트

### ✅ 서버 초기화 (최초 1회)
- [ ] `init_server_dirs.sh` 스크립트 실행
- [ ] `~/observer/secrets/.env` 파일 생성
- [ ] KIS_APP_KEY, KIS_APP_SECRET 설정
- [ ] 디렉토리 권한 설정 (chmod -R 777)

### ✅ 사전 확인
- [ ] Dockerfile에 KST 시간대 설정 추가
- [ ] docker-compose.yml에 TZ 환경 변수 추가
- [ ] docker-compose.server.yml에 env_file 설정 확인
- [ ] GHCR 이미지 태그 확인

### ✅ 배포 후 확인
- [ ] `docker exec observer env | grep KIS` - 자격증명 전달 확인
- [ ] `docker inspect observer --format '{{json .Mounts}}'` - 볼륨 마운트 확인
- [ ] 모든 컨테이너 KST 시간대로 실행
- [ ] Track A Collector 활성화 로그 확인
- [ ] Track B Collector 상태 로그 확인
- [ ] `/app/config/observer/swing/YYYYMMDD.jsonl` 생성 확인
- [ ] `/app/logs/swing/YYYYMMDD.log` 생성 확인

### ✅ 모니터링
- [ ] Grafana 대시보드 시간대 KST 설정
- [ ] Prometheus 메트릭 시간대 확인
- [ ] Alertmanager 알림 시간대 확인

## 🛠️ 문제 해결

### KIS 자격증명이 전달되지 않을 경우

**증상:**
```
WARNING | KIS_APP_KEY/SECRET not found - Universe Scheduler disabled
INFO | Track A Collector disabled (KIS credentials missing)
```

**해결:**
```bash
# 1. .env 파일 확인
cat ~/observer/secrets/.env | grep KIS

# 2. 볼륨 마운트 확인
docker inspect observer --format '{{json .Mounts}}'
# 결과가 [] 이면 볼륨이 마운트되지 않음

# 3. docker-compose.server.yml에 env_file 설정 확인
grep -A2 "env_file" ~/observer-deploy/docker-compose.server.yml

# 4. 컨테이너 재시작
cd ~/observer-deploy
docker compose -f docker-compose.server.yml down observer
docker compose -f docker-compose.server.yml up -d observer
```

### 볼륨 마운트가 없을 경우

**증상:**
```bash
docker inspect observer --format '{{json .Mounts}}'
# 결과: []
```

**해결:**
```bash
# docker-compose로 재시작 (docker run 대신)
cd ~/observer-deploy
export IMAGE_TAG=build-YYYYMMDD-HHMMSS
docker compose -f docker-compose.server.yml down observer
docker compose -f docker-compose.server.yml up -d observer
```

### 시간대 설정이 적용되지 않을 경우
```bash
# 컨테이너 재시작
docker-compose restart observer

# 시간대 강제 설정
docker exec observer ln -snf /usr/share/zoneinfo/Asia/Seoul /etc/localtime
docker exec observer echo "Asia/Seoul" > /etc/timezone
```

### Track B가 거래 시간 외로 판단할 경우
```bash
# 파이썬 시간대 확인
docker exec observer python -c "
from datetime import datetime
from zoneinfo import ZoneInfo
print('UTC:', datetime.now())
print('KST:', datetime.now(ZoneInfo('Asia/Seoul')))
"

# 애플리케이션 재시작
docker-compose restart observer
```

## 📁 관련 파일

### 서버 배포 관련
- `infra/_shared/compose/docker-compose.server.yml` - 서버 배포용 설정
- `infra/_shared/scripts/deploy/init_server_dirs.sh` - 서버 초기화 스크립트

### 수정된 파일
- `infra/docker/docker/Dockerfile` - 시간대 설정 추가
- `infra/docker/compose/docker-compose.yml` - TZ 환경 변수 추가

### 새로 생성된 파일
- `infra/_shared/compose/docker-compose.prod.yml` - 배포용 설정
- `infra/_shared/secrets/env.prod.example` - 환경 변수 예시
- `docs/guides/DEPLOYMENT_GUIDE.md` - 배포 가이드

## 🎯 중요 사항

1. **모든 컨테이너**: PostgreSQL, Observer, Grafana, Prometheus, Alertmanager 모두 KST 시간대로 설정
2. **환경 변수**: `.env.prod` 파일에서 중앙 관리
3. **검증**: 배포 후 반드시 시간대 설정 확인
4. **모니터링**: 시간대 관련 로그 지속적으로 모니터링

이 설정을 통해 배포 서버에서도 KST 시간대가 정확하게 적용되어 Track B가 정상적으로 작동합니다.
