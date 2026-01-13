# Phase 2 서버 명령어 가이드

## 📋 서버 작업 순서

Azure VM에 접속하여 아래 명령어를 순차적으로 실행하세요.

---

## 1️⃣ 기존 컨테이너 확인 및 정리

### 동일 이름의 기존 컨테이너 존재 여부 확인
```bash
docker ps -a | grep observer
```

**예상 결과:**
- 기존 컨테이너가 없으면: 출력 없음
- 기존 컨테이너가 있으면: observer-prod 또는 유사한 이름 표시

### 기존 컨테이너 정리 (있는 경우)
```bash
# 실행 중인 컨테이너 중지
docker stop observer-prod

# 컨테이너 제거
docker rm observer-prod

# 확인
docker ps -a | grep observer
```

**체크리스트:**
- [x] 기존 컨테이너 확인 완료
- [ ] 기존 컨테이너 정리 완료 (있었다면)

---

## 2️⃣ 작업 디렉토리 준비

### app/obs_deploy 디렉토리로 이동
```bash
cd ~/app/obs_deploy
pwd
```

**예상 결과:**
```
/home/azureuser/app/obs_deploy
```

### 디렉토리 구조 확인
```bash
ls -la
```

**예상 파일:**
- Dockerfile
- docker-compose.yml
- requirements.txt
- env.template
- app/ (디렉토리)

---

## 3️⃣ 환경변수 설정

### env.template을 .env로 복사
```bash
cp env.template .env
```

### .env 파일 편집 (KIS API 키 입력)
```bash
nano .env
```

**입력할 내용:**
```bash
REAL_APP_KEY=실제_KIS_앱키
REAL_APP_SECRET=실제_KIS_시크릿
REAL_ACCOUNT_NO=실제_계좌번호
PHASE15_SOURCE_MODE=kis
PHASE15_SYMBOL=005930
```

**저장 방법:**
- `Ctrl + O` (저장)
- `Enter` (확인)
- `Ctrl + X` (종료)

### 환경변수 파일 확인
```bash
cat .env
```

**체크리스트:**
- [ ] .env 파일 생성 완료
- [ ] KIS API 키 입력 완료
- [ ] 환경변수 확인 완료

---

## 4️⃣ 필수 디렉토리 생성

### 데이터 및 로그 디렉토리 생성
```bash
mkdir -p data logs config/observer
```

### 디렉토리 확인
```bash
ls -la
```

**예상 결과:**
```
drwxr-xr-x  2 azureuser azureuser 4096 Jan 13 16:00 data
drwxr-xr-x  2 azureuser azureuser 4096 Jan 13 16:00 logs
drwxr-xr-x  3 azureuser azureuser 4096 Jan 13 16:00 config
```

**체크리스트:**
- [ ] data 디렉토리 생성 완료
- [ ] logs 디렉토리 생성 완료
- [ ] config/observer 디렉토리 생성 완료

---

## 5️⃣ Observer 컨테이너 빌드

### Docker 이미지 빌드
```bash
docker-compose build
```

**예상 출력:**
```
Building observer-prod
Step 1/X : FROM python:3.11-slim as builder
...
Successfully built xxxxx
Successfully tagged obs_deploy_observer-prod:latest
```

### 빌드된 이미지 확인
```bash
docker images | grep observer
```

**예상 결과:**
```
obs_deploy_observer-prod   latest   xxxxx   X minutes ago   XXX MB
```

**체크리스트:**
- [ ] Docker 이미지 빌드 성공
- [ ] 이미지 목록에서 확인 완료

---

## 6️⃣ Observer 컨테이너 실행 (수동 1회 실행)

### 컨테이너 실행
```bash
docker-compose up -d
```

**예상 출력:**
```
Creating observer-prod ... done
```

### 실행 대기 (3초)
```bash
sleep 3
```

**체크리스트:**
- [ ] 컨테이너 실행 명령 완료

---

## 7️⃣ 컨테이너 실행 상태 확인

### 실행 중인 컨테이너 확인
```bash
docker ps
```

**예상 결과:**
```
CONTAINER ID   IMAGE                        COMMAND              STATUS         NAMES
xxxxx          obs_deploy_observer-prod     "python observer.py" Up X seconds   observer-prod
```

### 컨테이너 상세 정보 확인
```bash
docker inspect observer-prod | grep -A 5 "State"
```

**예상 결과:**
```json
"State": {
    "Status": "running",
    "Running": true,
    ...
}
```

### 컨테이너 로그 확인
```bash
docker logs observer-prod
```

**예상 로그:**
```
Observer started | session_id=observer-xxxxx
Writing to data/observer/observer.jsonl
Logging to file: /app/logs/observer.log
Waiting for events... (Ctrl+C to stop)
```

**체크리스트:**
- [ ] 컨테이너가 실행 중 (docker ps에서 확인)
- [ ] 컨테이너 상태가 "running"
- [ ] 로그에 "Observer started" 메시지 확인

---

## 8️⃣ observer.jsonl 파일 생성 여부 확인

### config/observer 디렉토리 확인
```bash
ls -lh config/observer/
```

**예상 결과:**
```
-rw-r--r-- 1 qts qts 512 Jan 13 16:00 observer.jsonl
```

### observer.jsonl 파일 내용 확인
```bash
tail -f config/observer/observer.jsonl
```

**예상 내용:**
```json
{"timestamp": "2026-01-13T16:00:00", "event": "observer_started", ...}
```

**중지 방법:** `Ctrl + C`

**체크리스트:**
- [ ] observer.jsonl 파일 생성 확인
- [ ] 파일 크기가 0보다 큼
- [ ] JSON 형식 데이터 확인

---

## 9️⃣ 실제 KIS 데이터 로그 기록 확인

### 로그 파일 확인
```bash
tail -f logs/observer.log
```

**예상 로그:**
```
2026-01-13 16:00:00 | INFO | Observer started
2026-01-13 16:00:01 | INFO | KIS API connection established
2026-01-13 16:00:02 | INFO | Receiving market data for 005930
```

**중지 방법:** `Ctrl + C`

### KIS API 환경변수 확인
```bash
docker exec observer-prod env | grep KIS
```

**예상 결과:**
```
KIS_APP_KEY=실제_앱키
KIS_APP_SECRET=실제_시크릿
KIS_ACCOUNT_NO=실제_계좌번호
```

**체크리스트:**
- [ ] 로그 파일에 KIS 관련 메시지 확인
- [ ] KIS API 환경변수 정상 설정 확인
- [ ] 시장 데이터 수신 확인

---

## 🔟 컨테이너 중단 후 재실행 테스트

### 컨테이너 중지
```bash
docker-compose down
```

**예상 출력:**
```
Stopping observer-prod ... done
Removing observer-prod ... done
```

### 컨테이너 중지 확인
```bash
docker ps | grep observer
```

**예상 결과:** 출력 없음 (컨테이너가 중지됨)

### 컨테이너 재실행
```bash
docker-compose up -d
```

**예상 출력:**
```
Creating observer-prod ... done
```

### 재실행 확인
```bash
docker ps | grep observer
docker logs observer-prod
```

**체크리스트:**
- [ ] 컨테이너 정상 중지 확인
- [ ] 컨테이너 재실행 성공
- [ ] 재실행 후 로그 정상 기록 확인

---

## 1️⃣1️⃣ 컨테이너 중복 실행 방지 확인

### 동일 이름으로 중복 실행 시도
```bash
docker-compose up -d
```

**예상 출력:**
```
observer-prod is up-to-date
```

또는

```
Error: Conflict. The container name "/observer-prod" is already in use
```

### 실행 중인 컨테이너 개수 확인
```bash
docker ps | grep observer | wc -l
```

**예상 결과:** `1` (1개만 실행 중)

**체크리스트:**
- [ ] 중복 실행 방지 확인 (1개만 실행)
- [ ] docker-compose가 기존 컨테이너 재사용 확인

---

## 1️⃣2️⃣ 컨테이너 실행 실패 시 대응

### 로그 확인
```bash
docker logs observer-prod
```

### 컨테이너 내부 접속 (디버깅)
```bash
docker exec -it observer-prod /bin/bash
```

**내부에서 확인:**
```bash
ls -la /app/
ls -la /app/logs/
ls -la /app/config/
env | grep OBSERVER
env | grep KIS
```

**종료:** `exit`

### 수동 중단 원칙
```bash
# 문제 발생 시 즉시 중단
docker-compose down

# 로그 확인 후 원인 분석
docker logs observer-prod > observer_error.log
cat observer_error.log
```

**체크리스트:**
- [ ] 실패 시 로그 확인 방법 숙지
- [ ] 수동 중단 원칙 이해

---

## ✅ Phase 2 완료 체크리스트

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

## 🎯 Phase 2 완료 후

Phase 2가 성공적으로 완료되면:
1. `docs/todo_list.md`의 Phase 2 서버 체크리스트 모두 체크
2. Phase 3 (systemd 기반 자동 관리 설정) 진행 준비
3. 현재 상태 문서화

---

## 📞 문제 발생 시

1. **빌드 실패**: `docker-compose build --no-cache`로 재시도
2. **실행 실패**: `docker logs observer-prod`로 원인 확인
3. **로그 생성 안됨**: 볼륨 마운트 및 권한 확인
4. **KIS API 연동 실패**: 환경변수 및 네트워크 확인

**모든 문제는 로그 기반으로 분석하고 수동으로 중단 후 원인 파악**
