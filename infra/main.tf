# 주요 리소스 정의 파일
# 예시: Azure Resource Group

module "resource_group" {
  source   = "./modules/resource_group"
  name     = var.resource_group_name
  location = var.location
}
