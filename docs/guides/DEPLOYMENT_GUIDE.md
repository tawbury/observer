# 배포 가이드 - 시간대 설정 포함

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
**파일**: `infra/oci_deploy/docker-compose.prod.yml`
- **모든 서비스**: KST 시간대 설정 포함
- **환경 변수**: `.env.prod` 파일에서 관리

## 🚀 배포 절차

### 1. 환경 설정
```bash
# 배포 환경 변수 파일 생성
cp infra/oci_deploy/.env.prod.example infra/oci_deploy/.env.prod

# 환경 변수 편집
nano infra/oci_deploy/.env.prod
```

### 2. 배포 실행
```bash
# 배포용 docker-compose 사용
cd infra/oci_deploy
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

### ✅ 사전 확인
- [ ] Dockerfile에 KST 시간대 설정 추가
- [ ] docker-compose.yml에 TZ 환경 변수 추가
- [ ] 배포용 docker-compose.prod.yml 생성
- [ ] .env.prod 파일 설정 완료

### ✅ 배포 후 확인
- [ ] 모든 컨테이너 KST 시간대로 실행
- [ ] Track B 거래 시간 내 정상 작동
- [ ] 스켈프 데이터 생성 확인
- [ ] 로그 시간대 KST로 표시

### ✅ 모니터링
- [ ] Grafana 대시보드 시간대 KST 설정
- [ ] Prometheus 메트릭 시간대 확인
- [ ] Alertmanager 알림 시간대 확인

## 🛠️ 문제 해결

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

### 수정된 파일
- `infra/docker/docker/Dockerfile` - 시간대 설정 추가
- `infra/docker/compose/docker-compose.yml` - TZ 환경 변수 추가

### 새로 생성된 파일
- `infra/oci_deploy/docker-compose.prod.yml` - 배포용 설정
- `infra/oci_deploy/.env.prod.example` - 환경 변수 예시
- `infra/oci_deploy/DEPLOYMENT_GUIDE.md` - 배포 가이드

## 🎯 중요 사항

1. **모든 컨테이너**: PostgreSQL, Observer, Grafana, Prometheus, Alertmanager 모두 KST 시간대로 설정
2. **환경 변수**: `.env.prod` 파일에서 중앙 관리
3. **검증**: 배포 후 반드시 시간대 설정 확인
4. **모니터링**: 시간대 관련 로그 지속적으로 모니터링

이 설정을 통해 배포 서버에서도 KST 시간대가 정확하게 적용되어 Track B가 정상적으로 작동합니다.
