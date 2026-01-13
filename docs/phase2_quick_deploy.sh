#!/bin/bash
# Phase 2 Quick Deploy Script
# Azure VM에서 실행할 배포 스크립트

set -e

echo "🚀 Phase 2: Observer 컨테이너 배포 시작"

# 1. 기존 컨테이너 정리
echo "📦 기존 컨테이너 확인 및 정리..."
if docker ps -a | grep -q observer-prod; then
    echo "기존 observer-prod 컨테이너 중지 및 제거..."
    docker stop observer-prod || true
    docker rm observer-prod || true
fi

# 2. 환경변수 파일 확인
echo "🔍 환경변수 파일 확인..."
if [ ! -f .env ]; then
    echo "❌ .env 파일이 없습니다!"
    echo "env.template을 .env로 복사하고 실제 값을 입력하세요:"
    echo "  cp env.template .env"
    echo "  nano .env"
    exit 1
fi

# 3. 필수 디렉토리 생성
echo "📁 필수 디렉토리 생성..."
mkdir -p data logs config/observer

# 4. Docker 이미지 빌드
echo "🐳 Docker 이미지 빌드..."
docker-compose build

# 5. 컨테이너 실행
echo "▶️  컨테이너 실행..."
docker-compose up -d

# 6. 실행 상태 확인
echo "✅ 컨테이너 실행 상태 확인..."
sleep 3
docker ps | grep observer-prod

# 7. 로그 확인
echo "📋 초기 로그 확인..."
docker logs observer-prod

echo ""
echo "✅ Phase 2 배포 완료!"
echo ""
echo "📊 다음 명령어로 상태를 확인하세요:"
echo "  docker logs -f observer-prod          # 실시간 로그"
echo "  docker ps                             # 컨테이너 상태"
echo "  tail -f logs/observer.log             # 로그 파일"
echo "  tail -f config/observer/observer.jsonl # JSONL 파일"
echo ""
echo "🛑 컨테이너 중지:"
echo "  docker-compose down"
