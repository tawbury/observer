#!/bin/bash
# Azure Container Instances에 Observer 배포

RESOURCE_GROUP="rg-observer-prod"
CONTAINER_NAME="observer-prod"
REGISTRY_NAME="observercontainerreg"
IMAGE_NAME="observercontainerreg.azurecr.io/observer:latest"
DNS_NAME="observer-prod"

# ACR 로그인 정보
ACR_PASSWORD="+/qjzonXx+X59LqIdYFdkyL1XtCFpC5NVW++lf4BsJ+ACRBSNig9"

echo "🚀 Azure Container Instances에 Observer 배포 시작..."

# 컨테이너 생성
az container create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$CONTAINER_NAME" \
  --image "$IMAGE_NAME" \
  --cpu 1 \
  --memory 1.5 \
  --registry-login-server "${REGISTRY_NAME}.azurecr.io" \
  --registry-username "$REGISTRY_NAME" \
  --registry-password "$ACR_PASSWORD" \
  --ports 8000 \
  --os-type Linux \
  --environment-variables \
    OBSERVER_STANDALONE="1" \
    OBSERVER_DATA_DIR="/app/data/observer" \
    OBSERVER_LOG_DIR="/app/logs" \
    OBSERVER_CONFIG_DIR="/app/config" \
    PYTHONPATH="/app/src:/app" \
  --dns-name-label "$DNS_NAME" \
  --restart-policy Always

echo "✅ 배포 완료!"
echo ""
echo "📋 배포 정보:"
az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" --query "ipAddress.fqdn" -o tsv
