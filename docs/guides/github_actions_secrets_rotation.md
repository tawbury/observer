# GitHub Actions Secrets 주기적 갱신 절차

이 문서는 QTS Ops 프로젝트의 GitHub Actions Secrets(인증 정보 등) 주기적 갱신 및 관리 절차를 정리합니다.

## 1. 갱신 대상
- Azure 인증 정보(ARM_CLIENT_ID, ARM_CLIENT_SECRET, ARM_TENANT_ID, ARM_SUBSCRIPTION_ID)
- ACR(컨테이너 레지스트리) 인증 정보(ACR_USERNAME, ACR_PASSWORD)
- 기타 외부 서비스 API Key, Webhook 등

## 2. 갱신 주기
- 보안 정책에 따라 3~6개월마다 주기적 갱신 권장
- 비밀번호/Key 만료 정책이 있는 경우 만료 전 갱신 필수

## 3. 갱신 절차
1. Azure Portal, ACR 등에서 새로운 인증 정보(Secret) 발급
2. GitHub 저장소(Repository) → Settings → Secrets and variables → Actions에서 기존 값 교체
3. Secrets 교체 후, 관련 워크플로우 정상 동작 여부 확인
4. 필요시 Secrets 변경 이력/일자 별도 기록(내부 문서 등)

## 4. 자동화/알림
- 만료 예정일 기준 Slack/Teams/이메일 등으로 갱신 알림 자동화 가능
- GitHub Actions에서 secrets 만료 체크 워크플로우 구현 가능

## 참고
- Secrets는 반드시 최소 권한 원칙으로 관리
- 만료/교체 후 기존 Key/Secret은 즉시 폐기
- 갱신 이력은 보안 정책에 따라 별도 관리
