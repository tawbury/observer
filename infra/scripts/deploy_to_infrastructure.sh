#!/bin/bash

# QTS Observer 배포 스크립트
# Terraform 인프라에 Docker 패키지 배포

set -e

# 설정 변수
TERRAFORM_DIR="${TERRAFORM_DIR:-./terraform}"
PACKAGE_NAME="${PACKAGE_NAME:-ops_deploy.tar.gz}"
DEPLOYMENT_DIR="${DEPLOYMENT_DIR:-./ops_deploy}"

echo "🚀 QTS Observer 인프라 배포 시작..."

# 1. 사전 확인
echo "📋 사전 확인..."
if [ ! -f "$PACKAGE_NAME" ]; then
    echo "❌ 패키지 파일을 찾을 수 없습니다: $PACKAGE_NAME"
    exit 1
fi

if [ ! -d "$TERRAFORM_DIR" ]; then
    echo "❌ Terraform 디렉토리를 찾을 수 없습니다: $TERRAFORM_DIR"
    exit 1
fi

# 2. 기존 배포 정리
echo "🧹 기존 배포 정리..."
if [ -d "$DEPLOYMENT_DIR" ]; then
    rm -rf "$DEPLOYMENT_DIR"
fi

# 3. 패키지 압축 해제
echo "📦 패키지 압축 해제..."
tar -xzf "$PACKAGE_NAME"
echo "✅ 패키지 해제 완료: $DEPLOYMENT_DIR"

# 4. Terraform 상태 확인
echo "🔍 Terraform 상태 확인..."
cd "$TERRAFORM_DIR"
terraform plan -detailed-exitcode
PLAN_EXIT_CODE=$?

if [ $PLAN_EXIT_CODE -eq 1 ]; then
    echo "❌ Terraform plan 실패"
    exit 1
elif [ $PLAN_EXIT_CODE -eq 2 ]; then
    echo "🔄 변경 사항 적용 중..."
    terraform apply -auto-approve
else
    echo "✅ 인프라 상태 정상"
fi

# 5. Docker 이미지 빌드
echo "🐳 Docker 이미지 빌드..."
cd "../$DEPLOYMENT_DIR"
docker build -t qts-observer:$(date +%Y%m%d-%H%M%S) .
docker tag qts-observer:$(date +%Y%m%d-%H%M%S) qts-observer:latest

# 6. 컨테이너 배포
echo "🚢 컨테이너 배포..."
docker-compose down
docker-compose up -d

# 7. 상태 확인
echo "🔍 배포 상태 확인..."
sleep 10

# 컨테이너 상태
if docker ps | grep -q "qts-observer"; then
    echo "✅ 컨테이너 실행 중"
else
    echo "❌ 컨테이너 실행 실패"
    docker logs qts-observer
    exit 1
fi

# 헬스체크
echo "🏥 헬스체크..."
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
if [ "$HEALTH_CHECK" = "200" ] || [ "$HEALTH_CHECK" = "000" ]; then
    echo "✅ 헬스체크 통과"
else
    echo "⚠️ 헬스체크 상태 코드: $HEALTH_CHECK"
fi

# 8. 정보 출력
echo ""
echo "🎉 배포 완료!"
echo ""
echo "📋 배포 정보:"
echo "   - 패키지: $PACKAGE_NAME"
echo "   - 배포 디렉토리: $DEPLOYMENT_DIR"
echo "   - 컨테이너: qts-observer"
echo "   - 포트: 8000"
echo ""
echo "🔍 유용한 명령어:"
echo "   - 컨테이너 상태: docker ps"
echo "   - 로그 확인: docker logs qts-observer"
echo "   - 재시작: docker-compose restart"
echo "   - 정지: docker-compose down"
echo ""
echo "📊 모니터링:"
echo "   - 실시간 로그: docker logs -f qts-observer"
echo "   - 리소스 사용: docker stats qts-observer"
echo "   - 헬스체크: curl http://localhost:8000/health"

echo ""
echo "✅ QTS Observer 배포 성공!"
