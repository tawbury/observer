# Azure VM Observer 배포 파일 전송 문제 진단 보고서

## 📋 진단 개요

- **진단일시**: 2026-01-13 16:42 KST
- **VM 정보**: observer-vm-01 (RG-OBSERVER-TEST)
- **VM IP**: 20.200.145.7
- **문제**: VM의 observer.py, paths.py, requirements.txt가 0바이트, src 폴더가 비어있음

---

## 🔍 1. 로컬 파일 상태 확인

### 주요 파일 크기 확인
```
Name               Length FullName
----               ------ --------
observer.py          7669 D:\development\prj_ops\app\obs_deploy\app\src\observer\observer.py
observer.py          2895 D:\development\prj_ops\app\obs_deploy\app\observer.py
paths.py             6808 D:\development\prj_ops\app\obs_deploy\app\paths.py
docker-compose.yml   1225 D:\development\prj_ops\app\obs_deploy\docker-compose.yml
Dockerfile           1238 D:\development\prj_ops\app\obs_deploy\Dockerfile
env.template          528 D:\development\prj_ops\app\obs_deploy\env.template
requirements.txt      189 D:\development\prj_ops\app\obs_deploy\requirements.txt
```

### src 폴더 통계
```
파일 개수: 111개
총 크기: 300.73 KB
```

### 로컬 파일 상태 요약
✅ **정상**: 모든 파일이 정상 크기로 존재
✅ **정상**: src 폴더에 111개 파일, 300.73 KB 데이터 존재
✅ **정상**: app/observer.py (2,895 바이트), app/paths.py (6,808 바이트)

---

## 🖥️ 2. VM 파일 상태 확인

### VM 디렉토리 구조
```
/home/azureuser/observer-deploy/
├── Dockerfile (79 bytes) ✅
├── Dockerfile.simple (0 bytes) ⚠️
├── a.out (416 bytes) ⚠️
├── docker-compose.yml (698 bytes) ✅
├── observer.py (0 bytes) ❌
├── paths.py (0 bytes) ❌
├── requirements.txt (0 bytes) ❌
├── config/ (디렉토리) ✅
├── data/ (디렉토리) ✅
├── logs/ (디렉토리) ✅
└── src/ (디렉토리) ❌
```

### 문제 파일 상세
```
-rw-r--r-- 1 root root      0 Jan 13 06:30 observer.py
-rw-r--r-- 1 root root      0 Jan 13 06:31 paths.py
-rw-r--r-- 1 azureuser azureuser 0 Jan 13 06:33 requirements.txt
```

### src 폴더 상태
```
src/
└── __init__.py (0 bytes)
```

### VM 파일 상태 요약
❌ **심각**: observer.py, paths.py, requirements.txt가 0바이트
❌ **심각**: src 폴더에 __init__.py만 존재 (111개 → 1개)
❌ **권한 문제**: 일부 파일 소유자가 root로 설정됨

---

## 🔍 3. 이전 전송 시도 기록

### 발견된 문제점
1. **파일 전송 불완전**: 내용이 전송되지 않고 빈 파일만 생성
2. **권한 문제**: 일부 파일 소유자가 root로 설정
3. **디렉토리 구조 불완전**: src 폴더 구조가 제대로 전송되지 않음

### 시간 기록 분석
```
observer.py: Jan 13 06:30 (root 소유, 0 bytes)
paths.py: Jan 13 06:31 (root 소유, 0 bytes)
requirements.txt: Jan 13 06:33 (azureuser 소유, 0 bytes)
src/__init__.py: Jan 13 06:31 (root 소유, 0 bytes)
```

---

## 🌐 4. 네트워크 및 SSH 연결 확인

### Azure VM IP 확인
```
VirtualMachine    PublicIPAddresses    PrivateIPAddresses
----------------  -------------------  --------------------
observer-vm-01    20.200.145.7         10.0.0.4
```

### 연결 상태
✅ **정상**: Azure Run Command로 VM 접속 가능
✅ **정상**: VM 디렉토리 접근 가능
✅ **정상**: 명령어 실행 가능

---

## 🚨 발견된 문제점

### 1. 파일 내용 손실 (Critical)
- **현상**: observer.py, paths.py, requirements.txt가 0바이트
- **영향**: Observer 실행 불가
- **원인**: 파일 전송 중 내용이 누락

### 2. src 폴더 구조 손실 (Critical)
- **현상**: 111개 파일 → 1개 파일 (__init__.py만)
- **영향**: Observer 소스 코드 누락
- **원인**: 재귀적 디렉토리 전송 실패

### 3. 권한 문제 (Medium)
- **현상**: 일부 파일 소유자가 root
- **영향**: azureuser가 파일 수정 불가
- **원인**: root 권한으로 파일 생성

---

## 🔍 예상 원인

### 1. Azure Run Command 제한 (가능성 높음)
- Azure Run Command는 스크립트 길이 제한 있음
- 대용량 파일 전송에 적합하지 않음
- 파일 내용이 잘려서 0바이트가 될 수 있음

### 2. 파일 전송 방식 문제 (가능성 높음)
- `echo "내용" > 파일` 방식 사용 시 길이 제한
- `cat`으로 파일 생성 시 내용이 잘릴 수 있음
- 재귀적 디렉토리 복사 실패

### 3. 권한 설정 문제 (가능성 중간)
- 스크립트 실행 권한 문제
- root/azureuser 권한 충돌

---

## 💡 해결 방안

### 1. 즉각적 해결 (권장)
```bash
# 방법 1: SCP 사용
cd d:\development\prj_ops
tar -czf obs_deploy.tar.gz app/obs_deploy/
scp obs_deploy.tar.gz azureuser@20.200.145.7:~/

# VM에서
ssh azureuser@20.200.145.7
cd ~
tar -xzf obs_deploy.tar.gz
cd app/obs_deploy
```

### 2. Azure Bastion 사용 (대안)
- Azure Portal → VM → Bastion 접속
- 파일 업로드 기능 사용
- 직접 파일 전송

### 3. GitHub 사용 (장기적)
```bash
# 로컬에서
git add .
git commit -m "Observer deployment ready"
git push origin main

# VM에서
git clone <repo-url>
cd prj_ops/app/obs_deploy
```

---

## 📋 다음 단계

### 1. 파일 재전송 (즉시)
- SCP 방법으로 obs_deploy.tar.gz 전송
- 압축 해제 후 파일 상태 확인

### 2. 권한 수정
```bash
# VM에서 실행
sudo chown -R azureuser:azureuser /home/azureuser/observer-deploy/
chmod +x /home/azureuser/observer-deploy/*.sh
```

### 3. 배포 재시도
```bash
cd /home/azureuser/observer-deploy
cp env.template .env
nano .env  # KIS API 키 입력
docker-compose build
docker-compose up -d
```

---

## 🎯 검증 체크리스트

- [ ] observer.py 파일 크기 > 2,000 bytes
- [ ] paths.py 파일 크기 > 6,000 bytes  
- [ ] requirements.txt 파일 크기 > 100 bytes
- [ ] src 폴더 파일 개수 > 100개
- [ ] 모든 파일 소유자: azureuser
- [ ] docker-compose build 성공
- [ ] docker-compose up -d 성공

---

## 📞 연락처

문제 해결 시 참고:
- **Azure VM IP**: 20.200.145.7
- **VM 경로**: /home/azureuser/observer-deploy/
- **로컬 경로**: d:\development\prj_ops\app\obs_deploy\
