# Phase 2 완전 배포 가이드

## 🎯 현재 상황

- **로컬**: `app/obs_deploy/` 디렉토리에 모든 파일 준비 완료
- **VM**: `observer-vm-01` (RG-OBSERVER-TEST, koreasouth)
- **Docker**: VM에 설치 완료 (Docker 29.1.4, Compose v5.0.1)

---

## 📦 방법 1: SCP를 사용한 파일 전송 (권장)

### 1. 로컬에서 압축 파일 생성
```powershell
# PowerShell에서 실행
cd d:\development\prj_ops
tar -czf obs_deploy.tar.gz -C app obs_deploy
```

### 2. Azure VM 공개 IP 확인
```powershell
az vm list-ip-addresses --resource-group RG-OBSERVER-TEST --name observer-vm-01 --output table
```

### 3. SCP로 파일 전송
```powershell
# SSH 키 경로 확인 필요
scp obs_deploy.tar.gz azureuser@<VM_PUBLIC_IP>:~/
```

### 4. VM에서 압축 해제
```bash
ssh azureuser@<VM_PUBLIC_IP>
tar -xzf obs_deploy.tar.gz
cd obs_deploy
```

---

## 📦 방법 2: Azure Bastion/Portal을 통한 수동 설정

VM에 직접 접속하여 아래 스크립트를 실행하세요.

### Step 1: 디렉토리 구조 생성
```bash
mkdir -p ~/app/obs_deploy/app/{src,config,data,logs}
cd ~/app/obs_deploy
```

### Step 2: Dockerfile 생성
```bash
cat > Dockerfile << 'DOCKERFILE_EOF'
FROM python:3.11-slim as builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt || true

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY app/observer.py /app/
COPY app/paths.py /app/
COPY app/src/ /app/src/

RUN mkdir -p /app/data/observer /app/logs /app/config

ENV QTS_OBSERVER_STANDALONE=1
ENV PYTHONPATH=/app/src:/app
ENV OBSERVER_DATA_DIR=/app/data/observer
ENV OBSERVER_LOG_DIR=/app/logs
ENV PATH=/root/.local/bin:$PATH

RUN groupadd -r qts && useradd -r -g qts qts
RUN chown -R qts:qts /app
USER qts

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

EXPOSE 8000
CMD ["python", "observer.py"]
DOCKERFILE_EOF
```

### Step 3: requirements.txt 생성
```bash
cat > requirements.txt << 'REQ_EOF'
pandas>=1.5.0
numpy>=1.24.0
python-json-logger>=2.0.0
requests>=2.31.0
python-dotenv>=1.0.0
REQ_EOF
```

### Step 4: docker-compose.yml 생성
```bash
cat > docker-compose.yml << 'COMPOSE_EOF'
version: '3.8'

services:
  observer-prod:
    build: .
    container_name: observer-prod
    restart: unless-stopped
    environment:
      - QTS_OBSERVER_STANDALONE=1
      - PYTHONPATH=/app/src:/app
      - OBSERVER_DATA_DIR=/app/data/observer
      - OBSERVER_LOG_DIR=/app/logs
      - KIS_APP_KEY=${REAL_APP_KEY}
      - KIS_APP_SECRET=${REAL_APP_SECRET}
      - KIS_ACCOUNT_NO=${REAL_ACCOUNT_NO}
      - PHASE15_SOURCE_MODE=kis
      - PHASE15_SYMBOL=005930
    volumes:
      - ./data:/app/data/observer
      - ./logs:/app/logs
      - ./config:/app/config
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
COMPOSE_EOF
```

### Step 5: env.template 생성
```bash
cat > env.template << 'ENV_EOF'
REAL_APP_KEY=your_real_app_key_here
REAL_APP_SECRET=your_real_app_secret_here
REAL_ACCOUNT_NO=your_account_number_here
PHASE15_SOURCE_MODE=kis
PHASE15_SYMBOL=005930
ENV_EOF
```

### Step 6: 소스 파일 복사 필요
**⚠️ 중요: 다음 파일들을 VM에 업로드해야 합니다:**
- `app/observer.py`
- `app/paths.py`
- `app/src/` (전체 디렉토리)

---

## 📦 방법 3: GitHub를 통한 배포 (가장 간단)

### 1. 로컬에서 Git 커밋 및 푸시
```powershell
cd d:\development\prj_ops
git add app/obs_deploy/
git commit -m "Phase 2: Observer deployment files ready"
git push origin main
```

### 2. VM에서 Git Clone
```bash
ssh azureuser@<VM_IP>
cd ~
git clone https://github.com/<your-repo>/prj_ops.git
cd prj_ops/app/obs_deploy
```

### 3. 환경변수 설정
```bash
cp env.template .env
nano .env  # KIS API 키 입력
```

### 4. 배포 실행
```bash
mkdir -p data logs config/observer
docker-compose build
docker-compose up -d
```

---

## ✅ Phase 2 서버 작업 체크리스트

파일 업로드 후 VM에서 실행:

### 1. 기존 컨테이너 확인
```bash
docker ps -a | grep observer
# 결과: 없음 (확인 완료)
```

### 2. 환경변수 설정
```bash
cd ~/app/obs_deploy  # 또는 ~/prj_ops/app/obs_deploy
cp env.template .env
nano .env
```

### 3. 필수 디렉토리 생성
```bash
mkdir -p data logs config/observer
ls -la
```

### 4. Docker 이미지 빌드
```bash
docker-compose build
```

### 5. 컨테이너 실행
```bash
docker-compose up -d
```

### 6. 실행 상태 확인
```bash
docker ps
docker logs observer-prod
```

### 7. 로그 파일 확인
```bash
tail -f logs/observer.log
tail -f config/observer/observer.jsonl
```

### 8. 재시작 테스트
```bash
docker-compose down
docker-compose up -d
docker ps
```

---

## 🔧 현재 진행 가능한 작업

VM에 파일을 업로드하는 방법:

1. **Azure Portal** → VM → Bastion 연결 → 파일 업로드
2. **SCP** 사용 (SSH 키 필요)
3. **GitHub** 사용 (가장 권장)
4. **Azure File Share** 마운트

---

## 📊 다음 단계

1. 위 방법 중 하나를 선택하여 파일 업로드
2. VM에서 Phase 2 서버 체크리스트 실행
3. 모든 체크리스트 완료 시 Phase 3 진행

---

## 💡 권장 방법

**GitHub를 사용한 배포**가 가장 간단하고 안전합니다:
- 버전 관리 가능
- 롤백 용이
- 재배포 간편
- 파일 전송 문제 없음
