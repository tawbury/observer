# Phase 3 서버 명령어 가이드

## 📋 VM에서 실행할 명령어 (순서대로)

---

## 1️⃣ systemd 서비스 파일 생성

```bash
# root 권한으로 서비스 파일 생성
sudo tee /etc/systemd/system/observer.service > /dev/null << 'EOF'
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
```

**예상 결과**: 파일 생성 완료 (출력 없음)

**확인**:
```bash
cat /etc/systemd/system/observer.service
```

---

## 2️⃣ systemd daemon reload

```bash
sudo systemctl daemon-reload
```

**예상 결과**: 없음 (성공 시)

---

## 3️⃣ observer 서비스 enable 설정

```bash
sudo systemctl enable observer
```

**예상 결과**:
```
Created symlink /etc/systemd/system/multi-user.target.wants/observer.service → /etc/systemd/system/observer.service.
```

**확인**:
```bash
systemctl is-enabled observer
```
**출력**: `enabled`

---

## 4️⃣ observer 서비스 start 실행

```bash
sudo systemctl start observer
```

**예상 결과**: 없음 (성공 시)

---

## 5️⃣ 서비스 상태 확인

```bash
systemctl status observer
```

**예상 결과**:
```
● observer.service - Observer Container Service
     Loaded: loaded (/etc/systemd/system/observer.service; enabled; vendor preset: enabled)
     Active: active (exited) since Mon 2026-01-13 16:30:00 KST; 5s ago
    Process: 12345 ExecStart=/usr/bin/docker-compose up -d (code=exited, status=0/SUCCESS)
   Main PID: 12345 (code=exited, status=0/SUCCESS)
```

**체크포인트**:
- `Loaded: loaded` ✅
- `enabled` ✅
- `Active: active (exited)` ✅

---

## 6️⃣ 컨테이너 실행 확인

```bash
docker ps
```

**예상 결과**:
```
CONTAINER ID   IMAGE                        COMMAND              STATUS         NAMES
xxxxx          obs_deploy_observer-prod     "python observer.py" Up 10 seconds  observer-prod
```

---

## 7️⃣ systemd 서비스 로그 확인

```bash
journalctl -u observer -n 50
```

**예상 결과**:
```
Jan 13 16:30:00 observer-vm-01 systemd[1]: Starting Observer Container Service...
Jan 13 16:30:00 observer-vm-01 docker-compose[12345]: Creating observer-prod ... done
Jan 13 16:30:00 observer-vm-01 systemd[1]: Started Observer Container Service.
```

---

## 8️⃣ 재시작 루프 방지 확인

### 설정 확인
```bash
systemctl show observer | grep -E "Restart|StartLimit"
```

**예상 결과**:
```
Restart=on-failure
RestartSec=10s
StartLimitBurst=5
StartLimitIntervalSec=60000000
```

---

## 9️⃣ SIGTERM 정상 종료 확인

### 서비스 중지 테스트
```bash
# 서비스 중지
sudo systemctl stop observer

# 컨테이너 확인 (없어야 함)
docker ps -a | grep observer

# 로그 확인
journalctl -u observer -n 20
```

**예상 로그**:
```
Jan 13 16:35:00 observer-vm-01 systemd[1]: Stopping Observer Container Service...
Jan 13 16:35:00 observer-vm-01 docker-compose[12346]: Stopping observer-prod ... done
Jan 13 16:35:00 observer-vm-01 docker-compose[12346]: Removing observer-prod ... done
Jan 13 16:35:00 observer-vm-01 systemd[1]: Stopped Observer Container Service.
```

### 서비스 재시작
```bash
sudo systemctl start observer
docker ps | grep observer
```

---

## 🔟 서버 재부팅 테스트

### 재부팅 전 확인
```bash
# enable 상태 확인
systemctl is-enabled observer
# 출력: enabled

# 현재 상태 확인
systemctl status observer
docker ps | grep observer
```

### 재부팅 실행
```bash
sudo reboot
```

### 재부팅 후 확인 (SSH 재접속 후)
```bash
# 서비스 자동 시작 확인
systemctl status observer

# 컨테이너 자동 시작 확인
docker ps | grep observer

# 부팅 로그 확인
journalctl -b -u observer
```

**예상 결과**:
- 서비스: `active (exited)` ✅
- 컨테이너: `observer-prod running` ✅

---

## ✅ Phase 3 완료 체크리스트

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

## 🔧 추가 테스트 (선택)

### 컨테이너 강제 종료 후 자동 재시작
```bash
# 컨테이너 강제 종료
docker kill observer-prod

# 10초 대기
sleep 10

# 자동 재시작 확인
docker ps | grep observer

# systemd 로그 확인
journalctl -u observer -n 20
```

---

## 📊 모니터링 명령어

```bash
# 서비스 상태
systemctl status observer

# 실시간 로그
journalctl -u observer -f

# 컨테이너 상태
docker ps

# 컨테이너 로그
docker logs observer-prod

# Observer 로그 파일
tail -f ~/app/obs_deploy/logs/observer.log

# JSONL 데이터
tail -f ~/app/obs_deploy/config/observer/observer.jsonl
```

---

## 🎯 완료 후

Phase 3가 완료되면:
1. `docs/todo_list.md`의 Phase 3 체크리스트 모두 체크
2. Phase 4 (장애 & 복구 시나리오) 준비
