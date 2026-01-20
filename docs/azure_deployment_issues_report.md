# Azure 배포 관련 종합 보안 & 구성 문제 보고서

## 🔴 CRITICAL 보안 위험 (즉시 조치 필요)

### 1. 노출된 실거래 API 자격증명
**파일:** `.env`

**문제점:**
- 실거래 API Key 노출
- 실거래 Secret Key 노출  
- 실거래 계좌번호 노출
- 한국투자증권 OpenAPI 자격증명 노출

**위험도:** ⚠️ 극고위험 - 계정 탈취, 금융 거래 가능

**해결책:**

```bash
# 1. Git 히스토리에서 제거
git rm --cached .env
git commit --amend --no-edit
git push origin master --force

# 2. 새로운 자격증명 발급 필요
# 3. .gitignore에 .env 추가
echo ".env" >> .gitignore
```

### 2. Azure 자격증명 하드코딩
**파일:** `infra/provider.tf`

**문제점:**
```hcl
subscription_id = "632e6f30-269e-42d2-96a5-9c3618bd358e"
tenant_id       = "cbd7850b-7a48-4769-80f5-3b08ab27243f"
```

**위험도:** ⚠️ 극고위험 - Azure 구독 완전 장악 가능

**해결책:**

```bash
# 환경 변수로 변경
export ARM_SUBSCRIPTION_ID="..."
export ARM_TENANT_ID="..."
terraform apply
```

## 🟠 HIGH - 배포 차단 문제

### 3. Terraform 백엔드 미초기화
**파일:** `infra/backend.tf`

**문제점:**
```hcl
backend "azurerm" {
    resource_group_name  = "rg-observer-test"
    storage_account_name = "observerstorage"  # 존재하지 않음
    container_name       = "tfstate"
}
```

**해결책:**

```bash
# Azure Storage 계정 생성
az group create --name rg-observer-test --location eastasia
az storage account create \
  --name observerstorage \
  --resource-group rg-observer-test \
  --location eastasia

# 컨테이너 생성
az storage container create --name tfstate \
  --account-name observerstorage

# Terraform 초기화
terraform init
```

### 4. 경로 불일치 - Windows vs Docker vs Azure
**문제점:**
- 로컬 Windows: `D:\development\prj_ops\app\data`
- Docker Compose: `./app/data:/app/data/observer`
- Dockerfile: `/app/data/observer + /app/app/data` (중복)
- deployment_paths: `/app/data/observer`
- Azure VM: `/home/observer/app/data` ???

**해결책 - Dockerfile 정리:**

```dockerfile
# 현재 (잘못됨)
RUN mkdir -p /app/data/observer \
    && mkdir -p /app/logs \
    && mkdir -p /app/config \
    && mkdir -p /app/app/data \        # ← 제거
    && mkdir -p /app/app/logs \        # ← 제거
    && mkdir -p /app/app/config        # ← 제거

# 수정됨
RUN mkdir -p /app/data/observer \
    && mkdir -p /app/logs \
    && mkdir -p /app/config
```

### 5. 헬스 체크 - localhost 사용 불가
**문제점:**
- Dockerfile: `curl -f http://localhost:8000/health`
- Azure VM에서 작동 안함
- 컨테이너 내부에서만 localhost 접근 가능

**해결책:**

```dockerfile
# Dockerfile 수정
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health || exit 1
```

또는 배포 스크립트에서:

```bash
# deploy.sh 수정 (라인 포함)
HEALTH_CHECK_URL="http://${CONTAINER_IP}:8000/health"
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_CHECK_URL)

if [ "$HEALTH_STATUS" != "200" ]; then
    echo "Health check failed: $HEALTH_STATUS"
    exit 1
fi
```

## 🟡 MEDIUM - 구성 문제

### 6. Docker Volume Mount 경로 오류
**현재 (문제):**
```yaml
# docker-compose.yml
volumes:
  - ./app/data:/app/data/observer      # ← 잘못된 마운트
  - ./app/logs:/app/logs
  - ./app/config:/app/config
```

**문제:** `./app/data`를 `/app/data/observer`로 마운트하면 observer 폴더가 없음

**수정:**
```yaml
volumes:
  - ./app/data/observer:/app/data/observer
  - ./app/logs:/app/logs
  - ./app/config:/app/config
```

### 7. 배포 스크립트 - localhost 건강 상태 확인
**파일:** `infra/scripts/deploy.sh` (라인 약 90-100)

**문제:**
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health
```

**Azure VM에서 실패하는 이유:**
- localhost = 127.0.0.1 (로컬 루프백만)
- 컨테이너가 별도 네트워크 인터페이스 사용

**수정:**
```bash
# 컨테이너 IP 취득 후 확인
CONTAINER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' observer)
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" "http://${CONTAINER_IP}:8000/health")

if [ "$HEALTH_CHECK" = "200" ]; then
    echo "Health check passed"
else
    echo "Health check failed: $HEALTH_CHECK"
    exit 1
fi
```

### 8. 하드코딩된 Azure Container Registry
**문제:**
```bash
# deploy.sh에서
REGISTRY="observerregistry.azurecr.io"  # 모든 환경에서 동일
```

**환경별 분리 필요:**
```bash
case "$ENVIRONMENT" in
  dev)
    REGISTRY="observerregistry-dev.azurecr.io"
    RESOURCE_GROUP="rg-observer-dev"
    ;;
  staging)
    REGISTRY="observerregistry-staging.azurecr.io"
    RESOURCE_GROUP="rg-observer-staging"
    ;;
  prod)
    REGISTRY="observerregistry-prod.azurecr.io"
    RESOURCE_GROUP="rg-observer-prod"
    ;;
esac
```

## 📝 배포 구성 정리 사항

### 9. 환경 변수 표준화
**현재 설정된 환경 변수:**
- ✅ `OBSERVER_STANDALONE=1`
- ✅ `PYTHONPATH=/app/src:/app`
- ✅ `OBSERVER_DATA_DIR=/app/data/observer`
- ✅ `OBSERVER_LOG_DIR=/app/logs`
- ❌ `OBSERVER_CONFIG_DIR` (미사용)

**Azure 배포용 추가 필요 환경 변수:**
```bash
# Azure Key Vault 통합
AZURE_KEYVAULT_NAME="observer-kv"
AZURE_CLIENT_ID="..."
AZURE_CLIENT_SECRET="..."
AZURE_TENANT_ID="..."

# 데이터베이스 (향후)
DB_CONNECTION_STRING="..."
DB_USER="..."
DB_PASSWORD="..."

# 애플리케이션 로깅
LOG_LEVEL="INFO"
LOG_TO_APPINSIGHTS="true"
APPINSIGHTS_KEY="..."

# 배포 환경
ENVIRONMENT="prod"
REGION="eastasia"
```

### 10. Azure 리소스 그룹 명명 규칙
**현재 혼재:**
- Terraform: `rg-observer-dev`, `rg-observer-staging`, `rg-observer-prod`
- Backend: `rg-observer-test` ← 일관성 없음

**권장 표준화:**
```
dev:      rg-observer-dev
staging:  rg-observer-staging
prod:     rg-observer-prod
```

## 📊 Azure 배포 체크리스트

| # | 항목 | 현재 상태 | 필요 조치 |
|---|------|-----------|-----------|
| 1 | 민감 정보 제거 | ❌ 노출됨 | 즉시 제거 |
| 2 | 자격증명 관리 | ❌ 하드코딩됨 | Key Vault 이용 |
| 3 | Terraform 초기화 | ❌ 미초기화 | Backend 설정 |
| 4 | 경로 일관성 | ⚠️ 부분 일치 | Dockerfile 정리 |
| 5 | 헬스 체크 | ❌ localhost 사용 | 컨테이너 IP 사용 |
| 6 | 환경 변수 | ⚠️ 부분 완성 | 표준화 필요 |
| 7 | CI/CD 파이프라인 | ❌ 없음 | GitHub Actions 구성 |
| 8 | 로깅 | ⚠️ 로컬만 | Application Insights |
| 9 | 모니터링 | ❌ 없음 | Azure Monitor 설정 |
| 10 | RBAC | ❌ 없음 | Managed Identity 설정 |

## ✅ Azure 배포 전 필수 조치

### 1단계 - 보안 (NOW)
- `.env` 파일 git 히스토리에서 제거
- Azure 자격증명 환경 변수로 변경
- KIS API 새 자격증명 발급
- `.gitignore` 업데이트

### 2단계 - 인프라 (1~2시간)
- Azure Storage 계정 생성
- Terraform 백엔드 초기화
- Resource Group 생성
- Azure Container Registry 설정

### 3단계 - 구성 (30분)
- Dockerfile 경로 정리
- docker-compose.yml 볼륨 수정
- 배포 스크립트 업데이트
- 환경 변수 표준화

### 4단계 - 배포 (1시간)
- 테스트 환경 배포
- 헬스 체크 검증
- 로그 확인
- 엔드포인트 테스트

### 5단계 - CI/CD (2시간)
- GitHub Actions 워크플로우 생성
- Terraform 자동화
- 자동 배포 설정

## 🚀 즉시 실행 명령어

### 1. 현재 상태 확인
```bash
git log --all --oneline -- .env
git show HEAD:.env | head -5
```

### 2. .env 파일 제거 (git 히스토리에서)
```bash
git filter-branch --tree-filter 'rm -f .env' --prune-empty HEAD
```

### 3. gitignore 업데이트
```bash
echo ".env" >> .gitignore
echo "*.tfvars" >> .gitignore
echo "*.tfstate*" >> .gitignore
```

### 4. Azure CLI 로그인
```bash
az login
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

### 5. 배포 준비
```bash
cd infra
terraform validate
terraform plan -var-file="terraform.tfvars.dev"
```

## ⚠️ 결론

현재 상태에서 Azure 배포 불가능. 보안 문제와 구성 문제 해결 후 배포 진행 필수.

**추정 작업 시간:** 4~6시간 (보안, 인프라, 구성, CI/CD 포함)

---

*보고서 생성일시: 2026-01-20*  
*우선순위: 보안 > 인프라 > 구성 > 배포 > CI/CD*
