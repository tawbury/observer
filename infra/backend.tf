# 원격 상태 저장 설정 예시 (Azure Storage)
terraform {
  backend "azurerm" {
    resource_group_name  = "rg-observer-test"        # 상태 파일을 저장할 리소스 그룹명
    storage_account_name = "observerstorage"         # 스토리지 계정명
    container_name       = "tfstate"                 # 컨테이너명
    key                  = "terraform.tfstate"       # 상태 파일명
  }
}

# 실제 값으로 변경 후 사용하세요.
# Azure Storage 계정 및 컨테이너는 미리 생성되어 있어야 합니다.
