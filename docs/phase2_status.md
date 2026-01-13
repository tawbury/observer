# Phase 2 현재 상태 및 다음 단계

## ✅ 완료된 작업 (로컬/IDE)

### 1. 배포 파일 준비
- **위치**: `app/obs_deploy/`
- **Dockerfile**: 멀티스테이지 빌드, 보안 설정 완료
- **docker-compose.yml**: KIS API 환경변수, 리소스 제한 설정
- **requirements.txt**: 필수 패키지 추가 (pandas, numpy, requests, python-dotenv)
- **env.template**: KIS API 환경변수 템플릿 생성

### 2. 문서화
- **phase2_deployment_guide.md**: 상세 배포 가이드
- **phase2_quick_deploy.sh**: 자동화 배포 스크립트
- **todo_list.md**: Phase 2 체크리스트 업데이트

### 3. 배포 준비 완료
```
app/obs_deploy/
├── Dockerfile              ✅
├── docker-compose.yml      ✅
├── requirements.txt        ✅
├── env.template           ✅
├── app/
│   ├── observer.py        ✅
│   ├── paths.py           ✅
│   └── src/               ✅ (111 items)
```

---

## 🎯 다음 단계 (Azure VM에서 실행)

### 1. 배포 패키지 전송
```bash
# 로컬에서 실행
cd d:\development\prj_ops
tar -czf obs_deploy.tar.gz app/obs_deploy/
scp obs_deploy.tar.gz azureuser@<VM_IP>:~/
```

### 2. Azure VM에서 배포
```bash
# VM에 SSH 접속
ssh azureuser@<VM_IP>

# 압축 해제
tar -xzf obs_deploy.tar.gz
cd app/obs_deploy

# 환경변수 설정
cp env.template .env
nano .env  # 실제 KIS API 키 입력

# 빠른 배포 스크립트 실행
chmod +x ../../docs/phase2_quick_deploy.sh
../../docs/phase2_quick_deploy.sh
```

### 3. 수동 배포 (단계별)
```bash
# 1. 기존 컨테이너 정리
docker stop observer-prod || true
docker rm observer-prod || true

# 2. 디렉토리 생성
mkdir -p data logs config/observer

# 3. 이미지 빌드
docker-compose build

# 4. 컨테이너 실행
docker-compose up -d

# 5. 상태 확인
docker ps
docker logs -f observer-prod
```

---

## 📋 Phase 2 서버 체크리스트

- [ ] Observer 컨테이너 **수동 1회 실행** (KIS API 연동 모드)
- [ ] 컨테이너 실행 상태 확인 (`docker ps`)
- [ ] observer.jsonl 파일 생성 여부 확인 (`ls -lh config/observer/`)
- [ ] 실제 KIS 데이터 로그 기록 확인 (`tail -f config/observer/observer.jsonl`)
- [ ] 컨테이너 중단 후 재실행 테스트
- [ ] 동일 이름의 기존 컨테이너 존재 여부 확인
- [ ] 컨테이너 중복 실행 방지 확인 (1개만 실행되는지)
- [ ] 컨테이너 실행 실패 시 `docker logs` 확인 후 수동 중단 원칙 적용

---

## 🔍 확인 명령어

### 컨테이너 상태
```bash
docker ps                           # 실행 중인 컨테이너
docker logs observer-prod           # 컨테이너 로그
docker logs -f observer-prod        # 실시간 로그
docker inspect observer-prod        # 상세 정보
```

### 로그 파일
```bash
tail -f logs/observer.log                    # Observer 로그
tail -f config/observer/observer.jsonl       # JSONL 데이터
ls -lh logs/ config/observer/                # 파일 크기 확인
```

### 환경변수
```bash
docker exec observer-prod env | grep KIS     # KIS API 환경변수 확인
docker exec observer-prod env | grep OBSERVER # Observer 환경변수 확인
```

---

## 🐛 트러블슈팅

### 빌드 실패
```bash
docker-compose build --no-cache              # 캐시 없이 재빌드
docker build -t observer-test .              # 직접 빌드 테스트
```

### 실행 실패
```bash
docker logs observer-prod                    # 에러 로그 확인
docker exec -it observer-prod /bin/bash      # 컨테이너 내부 접속
ls -la /app/logs /app/config                 # 디렉토리 권한 확인
```

### 로그 생성 안됨
```bash
docker inspect observer-prod | grep Mounts   # 볼륨 마운트 확인
ls -la data/ logs/ config/                   # 호스트 디렉토리 확인
```

---

## 📊 예상 결과

### 정상 실행 시 로그
```
Observer started | session_id=observer-xxxxx
Writing to data/observer/observer.jsonl
Logging to file: /app/logs/observer.log
Waiting for events... (Ctrl+C to stop)
```

### 파일 생성 확인
```bash
$ ls -lh logs/
-rw-r--r-- 1 qts qts 1.2K Jan 13 16:00 observer.log

$ ls -lh config/observer/
-rw-r--r-- 1 qts qts 512 Jan 13 16:00 observer.jsonl
```

---

## 🎯 Phase 2 완료 조건

1. ✅ 컨테이너가 정상적으로 실행됨 (`docker ps`에서 확인)
2. ✅ observer.log 파일이 생성되고 로그가 기록됨
3. ✅ observer.jsonl 파일이 생성되고 데이터가 기록됨
4. ✅ KIS API 연동이 정상적으로 작동함
5. ✅ 컨테이너 재시작이 정상적으로 작동함

**Phase 2가 완료되면 Phase 3 (systemd 자동 관리)로 진행합니다.**
