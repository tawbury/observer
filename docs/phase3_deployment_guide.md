# Phase 3: systemd 배포 가이드

## 📋 개요

Phase 3에서는 Observer 컨테이너를 systemd를 통해 자동으로 관리합니다.

---

## 🎯 Phase 3 목표

1. ✅ 서버 재부팅 시 Observer 자동 시작
2. ✅ 컨테이너 비정상 종료 시 자동 재시작
3. ✅ systemd를 통한 중앙 집중식 관리
4. ✅ 로그 통합 관리

---

## 📦 준비된 파일

### 1. systemd 서비스 파일
- **위치**: `infra/systemd/observer.service`
- **내용**: Observer 컨테이너 자동 관리 설정

### 2. 설계 문서
- **위치**: `docs/phase3_systemd_design.md`
- **내용**: systemd 설계 원칙 및 동작 방식

---

## 🚀 VM에서 실행할 명령어

### Step 1: systemd 서비스 파일 생성

```bash
# root 권한으로 전환
sudo -i

# 서비스 파일 생성
cat > /etc/systemd/system/observer.service << 'EOF'
[Unit]
Description=Observer Container Service
Documentation=https://github.com/your-repo/prj_ops
After=docker.service network-online.target
Requires=docker.service
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/azureuser/app/obs_deploy
EnvironmentFile=-/home/azureuser/app/obs_deploy/.env

# 컨테이너 시작
ExecStart=/usr/bin/docker-compose up -d

# 컨테이너 중지
ExecStop=/usr/bin/docker-compose down

# 재시작 설정
Restart=on-failure
RestartSec=10s

# 재시작 루프 방지
StartLimitBurst=5
StartLimitIntervalSec=60s

# 타임아웃 설정
TimeoutStartSec=300s
TimeoutStopSec=60s

# 사용자 설정
User=azureuser
Group=azureuser

[Install]
WantedBy=multi-user.target
EOF

# root 권한 종료
exit
```

### Step 2: systemd daemon reload

```bash
sudo systemctl daemon-reload
```

**예상 출력**: 없음 (성공 시)

### Step 3: observer 서비스 enable 설정

```bash
sudo systemctl enable observer
```

**예상 출력**:
```
Created symlink /etc/systemd/system/multi-user.target.wants/observer.service → /etc/systemd/system/observer.service.
```

### Step 4: observer 서비스 start 실행

```bash
sudo systemctl start observer
```

**예상 출력**: 없음 (성공 시)

### Step 5: 서비스 상태 확인

```bash
systemctl status observer
```

**예상 출력**:
```
● observer.service - Observer Container Service
     Loaded: loaded (/etc/systemd/system/observer.service; enabled; vendor preset: enabled)
     Active: active (exited) since Mon 2026-01-13 16:30:00 KST; 5s ago
    Process: 12345 ExecStart=/usr/bin/docker-compose up -d (code=exited, status=0/SUCCESS)
   Main PID: 12345 (code=exited, status=0/SUCCESS)
```

### Step 6: 컨테이너 실행 확인

```bash
docker ps
```

**예상 출력**:
```
CONTAINER ID   IMAGE                        COMMAND              STATUS         NAMES
xxxxx          obs_deploy_observer-prod     "python observer.py" Up 10 seconds  observer-prod
```

### Step 7: systemd 서비스 로그 확인

```bash
journalctl -u observer -n 50
```

**예상 출력**:
```
Jan 13 16:30:00 observer-vm-01 systemd[1]: Starting Observer Container Service...
Jan 13 16:30:00 observer-vm-01 docker-compose[12345]: Creating observer-prod ... done
Jan 13 16:30:00 observer-vm-01 systemd[1]: Started Observer Container Service.
```

### Step 8: 실시간 로그 모니터링

```bash
journalctl -u observer -f
```

**중지**: `Ctrl + C`

---

## ✅ Phase 3 체크리스트

### 서버에서 할 일

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

## 🧪 테스트 시나리오

### 테스트 1: 서비스 시작/중지

```bash
# 서비스 중지
sudo systemctl stop observer

# 상태 확인
systemctl status observer
# Output: inactive (dead)

docker ps | grep observer
# Output: 없음

# 서비스 시작
sudo systemctl start observer

# 상태 확인
systemctl status observer
# Output: active (exited)

docker ps | grep observer
# Output: observer-prod running
```

### 테스트 2: 컨테이너 강제 종료 (자동 재시작)

```bash
# 컨테이너 강제 종료
docker kill observer-prod

# 컨테이너 상태 확인
docker ps -a | grep observer
# Output: observer-prod (Exited)

# 10초 대기
sleep 10

# 자동 재시작 확인
docker ps | grep observer
# Output: observer-prod running (새로 시작됨)

# systemd 로그 확인
journalctl -u observer -n 20
# Output: 재시작 로그 확인
```

### 테스트 3: 서버 재부팅

```bash
# 재부팅 전 상태 확인
systemctl is-enabled observer
# Output: enabled

docker ps | grep observer
# Output: observer-prod running

# 재부팅
sudo reboot

# --- 재부팅 후 SSH 재접속 ---

# 서비스 자동 시작 확인
systemctl status observer
# Output: active (exited)

docker ps | grep observer
# Output: observer-prod running

# 부팅 로그 확인
journalctl -b -u observer
# Output: 부팅 시 자동 시작 로그
```

### 테스트 4: 재시작 루프 방지

```bash
# 의도적으로 실패하는 설정으로 변경
# (예: docker-compose.yml 경로 오류)

sudo systemctl restart observer

# 5회 연속 실패 후 중단 확인
systemctl status observer
# Output: failed (start request repeated too quickly)

# 로그 확인
journalctl -u observer -n 50
# Output: StartLimitBurst 초과 메시지
```

---

## 🔧 트러블슈팅

### 문제 1: 서비스 시작 실패

```bash
# 상세 로그 확인
journalctl -u observer -xe

# docker-compose 수동 실행 테스트
cd /home/azureuser/app/obs_deploy
docker-compose up -d

# 권한 확인
ls -la /etc/systemd/system/observer.service
# Output: -rw-r--r-- root root
```

### 문제 2: 컨테이너 자동 재시작 안됨

```bash
# systemd 설정 확인
systemctl show observer | grep Restart
# Output: Restart=on-failure

# 컨테이너 종료 코드 확인
docker inspect observer-prod | grep ExitCode
# Output: "ExitCode": 0 (정상 종료는 재시작 안됨)
```

### 문제 3: 재부팅 후 자동 시작 안됨

```bash
# enable 상태 확인
systemctl is-enabled observer
# Output: enabled

# 의존성 확인
systemctl list-dependencies observer
# Output: docker.service 포함 확인

# Docker 서비스 상태 확인
systemctl status docker
# Output: active (running)
```

---

## 📊 모니터링 명령어

### 서비스 상태
```bash
systemctl status observer          # 서비스 상태
systemctl is-active observer       # active/inactive
systemctl is-enabled observer      # enabled/disabled
systemctl is-failed observer       # failed 여부
```

### 로그 확인
```bash
journalctl -u observer             # 전체 로그
journalctl -u observer -n 50       # 최근 50줄
journalctl -u observer -f          # 실시간 로그
journalctl -u observer --since today  # 오늘 로그
journalctl -b -u observer          # 부팅 후 로그
```

### 컨테이너 상태
```bash
docker ps                          # 실행 중인 컨테이너
docker ps -a                       # 모든 컨테이너
docker logs observer-prod          # 컨테이너 로그
docker inspect observer-prod       # 상세 정보
```

---

## 🎯 Phase 3 완료 조건

1. ✅ systemd 서비스 파일 생성 완료
2. ✅ 서비스 활성화 (enabled) 완료
3. ✅ 서비스 정상 실행 (active) 확인
4. ✅ 컨테이너 자동 재시작 테스트 성공
5. ✅ 서버 재부팅 후 자동 시작 확인
6. ✅ 재시작 루프 방지 동작 확인
7. ✅ 로그 정상 기록 확인

---

## 🚀 다음 단계 (Phase 4)

Phase 3 완료 후:
1. Phase 4: 장애 & 복구 시나리오 검증
2. 디스크 사용량 모니터링
3. 로그 로테이션 설정 (선택)
4. 알림 설정 (선택)
