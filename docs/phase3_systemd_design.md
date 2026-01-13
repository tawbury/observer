# Phase 3: systemd 기반 자동 관리 설계

## 🎯 설계 목표

Observer 컨테이너를 systemd를 통해 자동으로 관리하여:
1. **서버 재부팅 시 자동 시작**
2. **컨테이너 종료 시 자동 재시작**
3. **로그 관리 및 모니터링**
4. **안정적인 운영 환경 구축**

---

## 🔑 핵심 설계 원칙

### 1. 컨테이너 재사용 구조
- **새로 만들지 않고, 기존 것을 재사용**
- `docker-compose up -d`는 기존 컨테이너가 있으면 재시작만 수행
- `docker-compose down`으로 중지 시 컨테이너 제거
- `docker start observer-prod`로 기존 컨테이너 재시작

### 2. Observer는 재시작 대상
- Observer는 **상태를 서버에 저장하지 않는 stateless 구조**
- 재시작 시 새로운 session_id로 시작
- 로그는 파일에 누적 저장 (중단 없음)
- 데이터는 볼륨 마운트로 영구 보존

### 3. 시그널 처리 방식
- **SIGTERM**: 정상 종료 시그널 (systemd stop)
- **SIGINT**: Ctrl+C 종료 시그널 (KeyboardInterrupt)
- Docker는 SIGTERM을 컨테이너에 전달
- Observer는 KeyboardInterrupt로 정상 종료

---

## 📋 systemd 서비스 설계

### 서비스 파일 구조
```ini
[Unit]
Description=Observer Container Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/azureuser/app/obs_deploy
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

### 설계 설명

#### [Unit] 섹션
- **Description**: 서비스 설명
- **After=docker.service**: Docker 서비스가 시작된 후 실행
- **Requires=docker.service**: Docker 서비스 의존성 명시

#### [Service] 섹션
- **Type=oneshot**: 한 번 실행 후 종료되는 타입
- **RemainAfterExit=yes**: 프로세스 종료 후에도 active 상태 유지
- **WorkingDirectory**: docker-compose.yml 위치
- **ExecStart**: 컨테이너 시작 명령
- **ExecStop**: 컨테이너 중지 명령
- **Restart=on-failure**: 실패 시에만 재시작
- **RestartSec=10s**: 재시작 대기 시간

#### [Install] 섹션
- **WantedBy=multi-user.target**: 멀티유저 모드에서 자동 시작

---

## 🔄 재시작 동작 방식

### 1. 서버 재부팅 시
```
1. 시스템 부팅
2. docker.service 시작
3. observer.service 시작
4. docker-compose up -d 실행
5. observer-prod 컨테이너 시작
```

### 2. 컨테이너 종료 시
```
1. 컨테이너 비정상 종료 감지
2. systemd가 Restart=on-failure 확인
3. 10초 대기 (RestartSec)
4. ExecStart 재실행
5. 컨테이너 재시작
```

### 3. 수동 중지 시
```
1. systemctl stop observer
2. ExecStop 실행 (docker-compose down)
3. 컨테이너 중지 및 제거
4. 서비스 inactive 상태
```

---

## 🛡️ 안전 장치

### 1. 재시작 루프 방지
- **Restart=on-failure**: 정상 종료 시에는 재시작 안 함
- **RestartSec=10s**: 빠른 재시작 루프 방지
- **StartLimitBurst=5**: 5회 연속 실패 시 중단
- **StartLimitIntervalSec=60s**: 60초 내 5회 실패 제한

### 2. 로그 관리
- **systemd 로그**: `journalctl -u observer`
- **Docker 로그**: `docker logs observer-prod`
- **Observer 로그**: `/app/logs/observer.log`
- **JSONL 데이터**: `/app/config/observer/observer.jsonl`

### 3. 모니터링
- **서비스 상태**: `systemctl status observer`
- **컨테이너 상태**: `docker ps`
- **로그 실시간**: `journalctl -u observer -f`

---

## 🔍 시그널 처리 흐름

### SIGTERM 처리
```
1. systemctl stop observer
2. systemd가 SIGTERM 전송
3. docker-compose down 실행
4. Docker가 컨테이너에 SIGTERM 전송
5. Python이 SIGTERM 수신
6. KeyboardInterrupt 발생
7. Observer 정상 종료
8. 로그 flush 완료
```

### 로그 Flush 확인
- Python logging 모듈은 자동으로 flush
- 파일 핸들러는 종료 시 자동 flush
- JSONL 파일은 각 줄마다 즉시 기록
- 데이터 손실 없음

---

## 📊 동작 시나리오

### 시나리오 1: 정상 운영
```bash
# 서비스 시작
sudo systemctl start observer

# 상태 확인
systemctl status observer
# Output: active (exited)

docker ps
# Output: observer-prod running

# 로그 확인
docker logs observer-prod
# Output: Observer started...
```

### 시나리오 2: 서버 재부팅
```bash
# 재부팅
sudo reboot

# 재부팅 후 자동 확인
systemctl status observer
# Output: active (exited)

docker ps
# Output: observer-prod running
```

### 시나리오 3: 컨테이너 비정상 종료
```bash
# 컨테이너 강제 종료
docker kill observer-prod

# 10초 후 자동 재시작
sleep 10
docker ps
# Output: observer-prod running (새로 시작됨)
```

### 시나리오 4: 수동 중지
```bash
# 서비스 중지
sudo systemctl stop observer

# 확인
systemctl status observer
# Output: inactive (dead)

docker ps
# Output: 컨테이너 없음
```

---

## ✅ Phase 3 체크리스트

### 로컬/IDE 작업
- [x] systemd 서비스 설계 내용 이해
- [x] Observer 재시작 대상 명확히 인식
- [x] 컨테이너 재사용 구조 이해
- [x] 시그널 처리 방식 확인 (SIGTERM, SIGINT)
- [x] 로그 flush 정상 동작 확인
- [ ] systemd 서비스 파일 생성
- [ ] 배포 스크립트 작성

### 서버 작업
- [ ] systemd 서비스 파일 생성 (/etc/systemd/system/observer.service)
- [ ] Docker 서비스 의존성 설정 (After=docker.service)
- [ ] systemd daemon reload 실행
- [ ] observer 서비스 enable 설정
- [ ] observer 서비스 start 실행
- [ ] 서비스 상태 확인 (systemctl status observer - active)
- [ ] systemd 서비스 로그 확인 (journalctl -u observer)
- [ ] systemd 재시작 루프 발생 여부 확인
- [ ] systemd 서비스 중지 시 Observer SIGTERM 정상 종료 확인
- [ ] systemd 설정 변경 후 서버 재부팅 테스트

---

## 🎯 다음 단계

1. systemd 서비스 파일 생성
2. VM에 배포
3. 서비스 활성화 및 테스트
4. 재부팅 테스트
5. Phase 4 (장애 & 복구 시나리오) 준비
