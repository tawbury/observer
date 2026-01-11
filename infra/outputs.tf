# 출력값 정의 파일

output "resource_group_id" {
  description = "생성된 리소스 그룹의 ID"
  value       = module.resource_group.id
}
