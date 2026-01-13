#!/bin/bash
# Phase 2 VM 초기 설정 스크립트
# Azure VM에서 실행하여 배포 환경 준비

set -e

echo "🚀 Phase 2 VM 초기 설정 시작"

# 1. 작업 디렉토리 생성
echo "📁 작업 디렉토리 생성..."
mkdir -p ~/app/obs_deploy
cd ~/app/obs_deploy

# 2. 필수 디렉토리 생성
echo "📁 필수 디렉토리 생성..."
mkdir -p app/src app/config app/data app/logs

# 3. Dockerfile 생성
echo "🐳 Dockerfile 생성..."
cat > Dockerfile << 'EOF'
FROM python:3.11-slim as builder

# 빌드 스테이지: 의존성 설치
WORKDIR /build

# requirements.txt 복사 및 의존성 설치 (캐시 최적화)
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt || true

# 런타임 스테이지: 최소 이미지
FROM python:3.11-slim

WORKDIR /app

# 빌더 스테이지에서 의존성 복사
COPY --from=builder /root/.local /root/.local

# 애플리케이션 파일 복사
COPY app/observer.py /app/
COPY app/paths.py /app/
COPY app/src/ /app/src/

# 필수 디렉토리 생성
RUN mkdir -p /app/data/observer \
    && mkdir -p /app/logs \
    && mkdir -p /app/config

# 환경 변수 설정 (Standalone 모드)
ENV QTS_OBSERVER_STANDALONE=1
ENV PYTHONPATH=/app/src:/app
ENV OBSERVER_DATA_DIR=/app/data/observer
ENV OBSERVER_LOG_DIR=/app/logs
ENV PATH=/root/.local/bin:$PATH

# 보안: 비-root 사용자로 실행
RUN groupadd -r qts && useradd -r -g qts qts
RUN chown -R qts:qts /app
USER qts

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# 기본 명령
CMD ["python", "observer.py"]
EOF

# 4. requirements.txt 생성
echo "📦 requirements.txt 생성..."
cat > requirements.txt << 'EOF'
# requirements.txt
# Observer deployment dependencies

# Core
pandas>=1.5.0
numpy>=1.24.0

# Logging
python-json-logger>=2.0.0

# KIS API
requests>=2.31.0
python-dotenv>=1.0.0
EOF

# 5. docker-compose.yml 생성
echo "🐳 docker-compose.yml 생성..."
cat > docker-compose.yml << 'EOF'
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
      # KIS API 연동 환경변수
      - KIS_APP_KEY=${REAL_APP_KEY}
      - KIS_APP_SECRET=${REAL_APP_SECRET}
      - KIS_ACCOUNT_NO=${REAL_ACCOUNT_NO}
      - PHASE15_SOURCE_MODE=kis
      - PHASE15_SYMBOL=005930
    volumes:
      - ./data:/app/data/observer
      - ./logs:/app/logs
      - ./config:/app/config
    # 배포 최적화: 리소스 제한
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    # 배포 최적화: 로그 로테이션
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
EOF

# 6. env.template 생성
echo "⚙️ env.template 생성..."
cat > env.template << 'EOF'
# KIS API 환경변수 템플릿
# 실제 사용 시 이 파일을 .env로 복사하고 실제 값을 입력하세요
# cp env.template .env

# KIS API 실전투자 계정 정보
REAL_APP_KEY=your_real_app_key_here
REAL_APP_SECRET=your_real_app_secret_here
REAL_ACCOUNT_NO=your_account_number_here

# Observer 설정
PHASE15_SOURCE_MODE=kis
PHASE15_SYMBOL=005930
EOF

# 7. 디렉토리 구조 확인
echo "📊 디렉토리 구조 확인..."
tree -L 2 . || ls -la

echo ""
echo "✅ Phase 2 VM 초기 설정 완료!"
echo ""
echo "📋 다음 단계:"
echo "  1. app/observer.py 및 app/paths.py 파일 업로드 필요"
echo "  2. app/src/ 디렉토리 업로드 필요"
echo "  3. env.template을 .env로 복사하고 KIS API 키 입력"
echo "  4. docker-compose build 실행"
echo "  5. docker-compose up -d 실행"
