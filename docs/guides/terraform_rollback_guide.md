# Terraform 인프라 변경 롤백 절차

이 문서는 QTS Ops 프로젝트의 Terraform 기반 Azure 인프라 변경 시 롤백(복구) 절차를 정리합니다.

## 1. 상태 파일(tfstate) 복구
- Azure Storage(tfstate 컨테이너)에 백업해둔 terraform.tfstate 파일을 복원(업로드)
- 예시:
  ```sh
  az storage blob upload --account-name observerstorage --container-name tfstate --name terraform.tfstate --file backup/terraform.tfstate.YYYYMMDD --overwrite
  ```

## 2. 코드 롤백
- main.tf, variables.tf 등 IaC 코드의 이전 버전으로 복원 (예: git revert, git checkout)
- 예시:
  ```sh
  git checkout <복구할 커밋 해시> infra/
  ```

## 3. terraform plan/apply
- 복원된 코드와 상태 파일 기준으로 terraform plan/apply 실행
- 예시:
  ```sh
  terraform init
  terraform plan -var-file="terraform.tfvars"
  terraform apply -var-file="terraform.tfvars" -auto-approve
  ```

## 4. 변경 내역 검증
- terraform plan 결과로 실제 인프라 변경 내역을 확인 후 적용
- 적용 후 Azure Portal 등에서 리소스 상태를 직접 검증

## 참고
- 상태 파일 백업/복구 절차는 [Terraform state 백업 및 복구 절차](../docs/terraform_state_backup.md) 참고
- IaC 코드 변경 이력은 git log, PR 기록 등으로 추적
