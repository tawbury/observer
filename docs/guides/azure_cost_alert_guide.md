# Azure 비용 알림 임계값 설정 및 모니터링 가이드

이 문서는 QTS Ops 프로젝트의 Azure 비용 알림 임계값 설정 및 모니터링 방법을 정리합니다.

## 1. 비용 알림 임계값 설정
- Azure Portal에서 구독/리소스 그룹별로 예산(Budget) 생성
- 예산 초과 시 이메일, Teams, Webhook 등으로 알림 전송 가능

### 예산 생성 예시 (Portal)
1. Azure Portal → "Cost Management + Billing" → "Budgets" → "Add"
2. 예산 금액, 기간, 알림 조건(%) 설정
3. 알림 수신자(이메일 등) 지정

### az cli 예시
```sh
az consumption budget create --amount 1000000 --category cost --name ops-budget --resource-group rg-observer-test --time-grain monthly --start-date 2026-01-01 --end-date 2026-12-31 --notification key=OpsBudgetAlert threshold=80 contact-emails=admin@example.com enabled=true
```

## 2. 비용 모니터링
- Azure Portal의 "Cost analysis"에서 실시간 비용/예산 현황 확인
- Cost Management API, Power BI, Grafana 등 외부 연동 가능

## 3. 자동화/알림
- 예산 초과, 임계값 도달 시 자동 알림(이메일, Teams, Slack 등)
- Webhook 연동 시 외부 시스템(OpsBot 등)으로 자동 통보 가능

## 참고
- 예산/알림 정책은 서비스 중요도, 예산 규모에 따라 주기적 재점검
- 실제 비용 초과 시 원인 분석 및 리소스 최적화 권장
