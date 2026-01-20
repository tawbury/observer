# 변수 정의 파일

variable "resource_group_name" {
  description = "리소스 그룹 이름"
  type        = string
  default     = "rg-observer-test"
}

variable "location" {
  description = "Azure 리전"
  type        = string
  default     = "Korea South"
}

# 예시: 민감 정보 변수 (실제 값은 tfvars에서 관리)
variable "admin_password" {
  description = "관리자 비밀번호 (민감 정보)"
  type        = string
  sensitive   = true
  default     = null
}
