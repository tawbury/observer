# Terraform 인프라 변경 롤백 절차

⚠️ **주의: 본 문서는 deprecated되었습니다.**

Terraform/infra 자동화가 Design A 정책(로컬 build/push, Actions deploy-only)에 따라 제거되었습니다:
- `infra/` 디렉토리 전체 삭제
- `terraform.yml` GitHub Actions 워크플로우 삭제
- Terraform 기반 인프라 자동화 중단

현재 배포는 다음 구성을 따릅니다:
- 로컬: `docker build → docker push` (GHCR)
- 서버: `scripts/deploy/server_deploy.sh` (GHCR pull + compose)
- 롤백: `server_deploy.sh` (last_good_tag 기반 자동 복구)

---

## ⛔️ 레거시 Terraform 절차 (더이상 사용 안함)

이하는 아카이빙 목적의 레거시 문서입니다:

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
