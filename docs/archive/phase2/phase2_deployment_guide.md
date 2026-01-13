# Phase 2 배포 가이드

## 📋 배포 준비 완료 상태

### ✅ 완료된 작업
1. **배포 디렉토리**: `app/obs_deploy/` 준비 완료
2. **Dockerfile**: 멀티스테이지 빌드 구성 완료
3. **docker-compose.yml**: KIS API 환경변수 포함
4. **requirements.txt**: 필수 패키지 명시 (pandas, numpy, requests, python-dotenv)
5. **env.template**: KIS API 환경변수 템플릿 생성

### 📂 배포 파일 구조
```
app/obs_deploy/
├── Dockerfile              # 멀티스테이지 빌드
├── docker-compose.yml      # KIS API 환경변수 포함
├── requirements.txt        # 의존성 패키지
├── env.template           # 환경변수 템플릿
├── app/
│   ├── observer.py        # Observer 실행 파일
│   ├── paths.py           # 경로 설정
│   ├── src/               # 소스 코드 (111 items)
│   ├── config/            # 설정 디렉토리
│   ├── data/              # 데이터 디렉토리
│   └── deployment_config.json
```

---

## 🚀 Azure VM 배포 절차

### 1. 배포 패키지 생성
```bash
# 로컬에서 실행
cd d:\development\prj_ops
tar -czf obs_deploy.tar.gz app/obs_deploy/
```

### 2. Azure VM에 파일 전송
```bash
# SCP를 사용하여 전송
scp obs_deploy.tar.gz azureuser@<VM_IP>:~/
```

### 3. Azure VM에서 압축 해제
```bash
# VM에 SSH 접속
ssh azureuser@<VM_IP>

# 압축 해제
tar -xzf obs_deploy.tar.gz
cd app/obs_deploy
```

### 4. 환경변수 설정
```bash
# env.template을 .env로 복사
cp env.template .env

# .env 파일 편집 (실제 KIS API 키 입력)
nano .env
```

**.env 파일 내용:**
```bash
REAL_APP_KEY=실제_앱키
REAL_APP_SECRET=실제_시크릿
REAL_ACCOUNT_NO=실제_계좌번호
PHASE15_SOURCE_MODE=kis
PHASE15_SYMBOL=005930
```

### 5. Docker 이미지 빌드
```bash
# 이미지 빌드
docker-compose build

# 빌드 확인
docker images | grep observer
```

### 6. 컨테이너 실행
```bash
# 백그라운드 실행
docker-compose up -d

# 실행 확인
docker ps
```

### 7. 로그 확인
```bash
# 실시간 로그 확인
docker logs -f observer-prod

# 로그 파일 확인
tail -f logs/observer.log

# observer.jsonl 확인
tail -f config/observer/observer.jsonl
```

---

## 🔍 Phase 2 체크리스트

### 로컬 / IDE형 AI에서 할 일
- [x] Observer Docker 실행 명령 확정 (환경변수, 볼륨 포함)
- [x] 컨테이너 이름 규칙 확정 (observer-prod)
- [x] 로그 파일명/위치가 고정되는지 재확인 (/app/config/observer/observer.jsonl)
- [x] KIS API 연동 환경변수 추가 (실전투자만 사용)
- [x] 포트/네트워크 제거 (아웃바운드 통신만 하므로 불필요)
- [ ] 컨테이너 실행 실패 시 `docker logs <container_name>`로 즉시 원인 확인

### 서버에서 할 일
- [ ] Observer 컨테이너 **수동 1회 실행** (KIS API 연동 모드)
- [ ] 컨테이너 실행 상태 확인
- [ ] observer.jsonl 파일 생성 여부 확인 (/app/config/observer/)
- [ ] 실제 KIS 데이터 로그 기록 확인
- [ ] 컨테이너 중단 후 재실행 테스트
- [ ] 동일 이름의 기존 컨테이너 존재 여부 확인
- [ ] 컨테이너 중복 실행 방지 확인 (1개만 실행되는지)
- [ ] 컨테이너 실행 실패 시 `docker logs` 확인 후 수동 중단 원칙 적용

---

## 🐛 트러블슈팅

### 컨테이너 빌드 실패
```bash
# 빌드 로그 확인
docker-compose build --no-cache

# Dockerfile 문법 확인
docker build -t observer-test .
```

### 컨테이너 실행 실패
```bash
# 로그 확인
docker logs observer-prod

# 환경변수 확인
docker exec observer-prod env | grep KIS

# 컨테이너 내부 접속
docker exec -it observer-prod /bin/bash
```

### 로그 파일 생성 안됨
```bash
# 디렉토리 권한 확인
ls -la logs/
ls -la config/

# 볼륨 마운트 확인
docker inspect observer-prod | grep Mounts -A 20
```

---

## 📊 예상 결과

### 정상 실행 시
```
Observer started | session_id=observer-xxxxx
Writing to data/observer/observer.jsonl
Logging to file: /app/logs/observer.log
Waiting for events... (Ctrl+C to stop)
```

### 파일 생성 확인
```bash
# 로그 파일
ls -lh logs/observer.log

# JSONL 파일
ls -lh config/observer/observer.jsonl

# 실시간 모니터링
watch -n 1 'ls -lh logs/ config/observer/'
```

---

## 🎯 다음 단계 (Phase 3)

Phase 2가 성공적으로 완료되면:
1. systemd 서비스 파일 생성
2. 자동 시작 설정
3. 재부팅 테스트
4. 장애 복구 시나리오 검증

---

## 📝 참고사항

- **배포 위치**: `app/obs_deploy/` 사용 (완전히 준비됨)
- **KIS API 모드**: 실전투자 계정만 사용
- **로그 위치**: `/app/logs/observer.log`
- **데이터 위치**: `/app/config/observer/observer.jsonl`
- **컨테이너 이름**: `observer-prod`
- **재시작 정책**: `unless-stopped`
