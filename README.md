# QTS Observer & Infra 프로젝트

이 저장소는 QTS Observer 애플리케이션과 Azure 인프라(IaC) 배포를 위한 전체 구성을 포함합니다.

## 폴더 구조
- `app/` : QTS Observer 애플리케이션 및 Docker 관련 파일
  - `ops_deploy/` : Dockerfile, docker-compose.yml, README 등 배포 패키지
- `infra/` : Terraform 기반 Azure 인프라 코드
  - `modules/` : 재사용 가능한 리소스 모듈
  - `scripts/` : 인프라 배포 스크립트
- `docs/` : 아키텍처 및 운영 문서
- `.github/workflows/` : GitHub Actions 자동화 워크플로우
- `.terraform/` : (루트) Terraform 상태 및 provider 캐시

## 주요 파일 및 문서
- `app/ops_deploy/README.md` : Observer 패키지 사용법
- `infra/README.md` : 인프라 IaC 사용법
- `docs/ops_Architecture.md` : 전체 시스템 아키텍처
- `docs/todo/todo.md` : 최신 투두 리스트

## 빠른 시작

### 1. 인프라 배포 (Terraform)
```sh
cd infra
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars" -auto-approve
```

### 2. Observer 앱 배포 (Docker)
```sh
cd app/ops_deploy
# 도커 이미지 빌드 및 컨테이너 실행
docker-compose up -d
```

### 3. 수동 배포
```sh
tar -xzf ops_deploy.tar.gz
cd ops_deploy
./start_ops.sh
```

## 자동화
- `.github/workflows/terraform.yml` : main 브랜치 push 시 인프라 자동 배포
- GitHub Secrets에 Azure 인증 정보 필요

## 참고
- [docs/ops_Architecture.md](docs/ops_Architecture.md) : 전체 시스템 아키텍처
- [docs/todo/todo.md](docs/todo/todo.md) : 최신 투두 리스트
- [infra/README.md](infra/README.md) : 인프라 상세 사용법
- [app/ops_deploy/README.md](app/ops_deploy/README.md) : Observer 앱 사용법

---

> 모든 배포/운영 절차 및 문서는 docs/ 폴더와 각 하위 README를 참고하세요.
