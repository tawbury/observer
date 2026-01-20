# Terraform 배포 조건 검수 리포트

## 1. 필수 파일 및 폴더 구조
- [x] backend.tf: 원격 상태 저장 설정
- [x] main.tf: 리소스 정의
- [x] provider.tf: 프로바이더 및 인증 정보
- [x] variables.tf: 변수 정의
- [x] outputs.tf: 출력값 정의
- [x] terraform.tfvars: 환경별 변수 값 관리
- [x] terraform.tfvars.example: 예시 변수 파일
- [x] modules/resource_group: 모듈 구조(main.tf, variables.tf, outputs.tf)
- [x] scripts/deploy_to_infrastructure.sh: 배포 스크립트

## 2. 주요 내용 검토
- backend.tf: Azure Storage 원격 상태 저장 설정 완료
- provider.tf: azurerm 프로바이더 및 subscription/tenant 정보 명시
- main.tf: resource_group 모듈 사용, 변수 참조 정상
- variables.tf: 필수 변수(resource_group_name, location, admin_password) 정의
- terraform.tfvars(.example): 변수 값 예시 및 실제 값 분리
- outputs.tf: resource_group_id 출력값 정의
- modules/resource_group: main.tf(azurerm_resource_group 생성), variables.tf(모듈 변수 정의), outputs.tf(리소스 id 출력)

## 3. 배포 전 필수 조건
- [x] Terraform 설치
- [x] Azure 계정 및 권한
- [x] 원격 상태 저장용 Azure Storage, Resource Group, Container 사전 생성
- [x] 환경별 변수 파일(tfvars) 작성
- [x] provider.tf 내 인증 정보(구독/테넌트) 확인
- [x] 민감 정보(admin_password 등)는 별도 파일로 관리 권장

## 4. 배포 명령어
```sh
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars" -auto-approve
```

## 5. 추가 권장 사항
- .gitignore에 terraform.tfvars 등 민감 정보 파일 추가
- GitHub Actions 등 CI/CD 연동 시 Secrets 등록 필요
- README.md에 배포 방법 및 사전 조건 명확히 기술

---

**결론:**
현재 프로젝트 폴더는 Terraform을 통한 Azure 인프라 배포를 위한 기본 조건을 모두 충족하고 있습니다. 환경별 변수 및 인증 정보만 최신화하여 배포를 진행하면 됩니다.
