# Docker 이미지 버전 관리 및 롤백 전략

이 문서는 QTS Ops 프로젝트의 Docker 이미지 버전 관리 및 롤백(복구) 전략을 정리합니다.

## 1. 이미지 태깅 정책
- GitHub Actions에서 빌드 시, 다음과 같이 여러 태그를 자동 부여
  - 커밋 SHA, 브랜치명, latest, 버전(semver) 등
- 예시: qts-observer:20260111-120000, qts-observer:main-<sha>, qts-observer:latest

## 2. 이미지 저장소 관리
- Azure Container Registry(ACR)에 모든 빌드 이미지를 푸시 및 보관
- 불필요한 오래된 이미지는 주기적으로 정리(보존 정책 적용)

## 3. 롤백 절차
1. 롤백 대상 이미지 태그 확인 (ACR 또는 git 커밋 기록)
2. docker-compose.yml 또는 배포 스크립트에서 해당 태그로 이미지 지정
   - 예시:
     ```yaml
     image: observerregistry.azurecr.io/qts-observer:20260111-120000
     ```
3. 컨테이너 재배포
   - 예시:
     ```sh
     docker-compose pull
     docker-compose up -d
     ```

## 4. 자동화
- GitHub Actions에서 이미지 태깅/푸시 자동화 (deploy.yml 참고)
- 롤백 스크립트/명령어는 운영 가이드에 포함

## 참고
- 이미지 태그/이력은 ACR 포털 또는 az acr repository show-tags 명령으로 확인
- 롤백 시 반드시 배포 후 정상 동작 여부를 검증
