
# Infra (Terraform) 사용법

이 폴더는 Azure 인프라를 코드로 관리하기 위한 Terraform 설정을 포함합니다.

## 폴더 구조
- `main.tf` : 리소스/모듈 정의 (예: resource_group)
- `modules/` : 재사용 가능한 인프라 모듈
- `variables.tf` : 변수 정의
- `terraform.tfvars.example` : 환경별 변수 예시 파일
- `outputs.tf` : 출력값 정의
- `provider.tf` : 프로바이더 및 인증 설정
- `scripts/` : 배포 스크립트 (deploy_to_infrastructure.sh 등)
- `.terraform/` : (루트) Terraform 상태 및 provider 캐시

## 배포 절차

### 1. 환경 변수 파일(tfvars) 준비
`terraform.tfvars.example`을 복사해 `terraform.tfvars`로 만들고 실제 값을 입력하세요.

예시:
```
resource_group_name = "rg-observer-test"
location           = "Korea South"
# admin_password = "<your_password>"
```

### 2. 인프라 배포
```sh
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars" -auto-approve
```

### 3. 자동화 (GitHub Actions)
- `.github/workflows/terraform.yml`에서 main 브랜치에 push 시 자동 배포
- Azure 인증 정보는 GitHub Secrets에 등록 필요

## 주요 파일/문서
- [../README.md](../README.md) : 전체 프로젝트 개요
- [../docs/development/obs_architecture.md](../docs/development/obs_architecture.md) : 시스템 아키텍처
- [../docs/todo/todo.md](../docs/todo/todo.md) : 최신 투두 리스트

## 참고 자료
- [Terraform Azure Provider Docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
