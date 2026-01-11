#!/bin/bash
# QTS Observer 배포 스크립트 (개발/스테이징/프로덕션)
# 사용법: ./deploy.sh <environment> <action>
# 예: ./deploy.sh staging deploy

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT=${1:-staging}
ACTION=${2:-deploy}

# 환경 설정
case $ENVIRONMENT in
  dev)
    TF_VARS="terraform.tfvars.dev"
    DOCKER_REGISTRY="observerregistry.azurecr.io"
    ENVIRONMENT_NAME="development"
    ;;
  staging)
    TF_VARS="terraform.tfvars.staging"
    DOCKER_REGISTRY="observerregistry.azurecr.io"
    ENVIRONMENT_NAME="staging"
    ;;
  prod)
    TF_VARS="terraform.tfvars.prod"
    DOCKER_REGISTRY="observerregistry.azurecr.io"
    ENVIRONMENT_NAME="production"
    ;;
  *)
    echo "❌ 잘못된 환경: $ENVIRONMENT"
    echo "사용 가능: dev, staging, prod"
    exit 1
    ;;
esac

echo "🚀 QTS Observer 배포 시작 ($ENVIRONMENT_NAME)"

# 배포 함수
deploy() {
  echo "📦 Docker 이미지 빌드 중..."
  docker build -t "$DOCKER_REGISTRY/qts-observer:$ENVIRONMENT_NAME-latest" \
               -t "$DOCKER_REGISTRY/qts-observer:$ENVIRONMENT_NAME-$(date +%Y%m%d-%H%M%S)" \
               app/ops_deploy/
  
  echo "🐳 Docker 이미지 푸시 중..."
  docker push "$DOCKER_REGISTRY/qts-observer:$ENVIRONMENT_NAME-latest"
  
  echo "🔧 Terraform 배포 중..."
  cd "$PROJECT_ROOT/infra"
  terraform init
  terraform plan -var-file="$TF_VARS" -out=tfplan
  terraform apply -auto-approve tfplan
  
  echo "✅ 배포 완료!"
}

# 롤백 함수
rollback() {
  echo "⏮️  롤백 시작..."
  
  # 이전 Docker 이미지 확인
  PREVIOUS_IMAGE=$(docker images "$DOCKER_REGISTRY/qts-observer" | tail -2 | head -1 | awk '{print $3}')
  
  if [ -z "$PREVIOUS_IMAGE" ]; then
    echo "❌ 롤백할 이미지가 없습니다"
    exit 1
  fi
  
  echo "🐳 이전 이미지 실행 중: $PREVIOUS_IMAGE"
  docker tag "$PREVIOUS_IMAGE" "$DOCKER_REGISTRY/qts-observer:$ENVIRONMENT_NAME-rollback"
  docker push "$DOCKER_REGISTRY/qts-observer:$ENVIRONMENT_NAME-rollback"
  
  # Terraform 상태 복원
  cd "$PROJECT_ROOT/infra"
  terraform plan -var-file="$TF_VARS" -out=tfplan
  terraform apply -auto-approve tfplan
  
  echo "✅ 롤백 완료!"
}

# 배포 상태 확인 함수
validate() {
  echo "🔍 배포 검증 중..."
  
  # 컨테이너 상태 확인
  if docker ps | grep -q "qts-observer"; then
    echo "✅ 컨테이너 실행 중"
  else
    echo "❌ 컨테이너 실행 안 됨"
    exit 1
  fi
  
  # 헬스체크
  HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
  if [ "$HEALTH" = "200" ] || [ "$HEALTH" = "000" ]; then
    echo "✅ 헬스체크 통과"
  else
    echo "⚠️  헬스체크 상태: $HEALTH"
  fi
  
  # 로그 확인
  echo ""
  echo "📋 최근 로그:"
  docker logs qts-observer | tail -20
}

# 액션 실행
case $ACTION in
  deploy)
    deploy
    validate
    ;;
  rollback)
    rollback
    ;;
  validate)
    validate
    ;;
  *)
    echo "❌ 잘못된 액션: $ACTION"
    echo "사용 가능: deploy, rollback, validate"
    exit 1
    ;;
esac

echo ""
echo "🎉 작업 완료!"
