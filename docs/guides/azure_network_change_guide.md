# Azure 네트워크(NSG, VNet) 변경 관리 가이드

이 문서는 QTS Ops 프로젝트의 Azure 네트워크(NSG, VNet) 변경 관리 및 운영 가이드를 정리합니다.

## 1. 변경 전 점검
- 변경 목적, 영향 범위(연결된 VM, 서비스 등) 사전 파악
- 기존 NSG/VNet 설정 백업 (terraform.tfstate, 코드, Azure Portal export 등)

## 2. 변경 절차
- IaC(Terraform) 코드로 NSG, VNet 등 네트워크 리소스 관리 권장
- 변경 시 terraform plan으로 영향도(추가/삭제/수정) 사전 확인
- 주요 변경(포트 오픈/차단, 서브넷 추가 등)은 PR 리뷰 및 승인 후 적용

## 3. 변경 적용
- terraform apply 또는 Azure Portal에서 변경 적용
- 적용 후 네트워크 연결성(SSH, HTTP, DB 등) 직접 점검
- 로그/모니터링(Azure Monitor, NSG Flow Logs 등)으로 이상 여부 확인

## 4. 변경 이력 관리
- 모든 변경은 git commit, PR, 변경 이력 문서로 추적
- 긴급 변경 시 사후 문서화 및 영향 분석 필수

## 5. 복구/롤백
- 문제 발생 시 이전 terraform.tfstate, 코드, Portal export본으로 복구
- Azure Portal에서 NSG/VNet 설정을 수동 복원 가능

## 참고
- NSG Flow Logs, Network Watcher 등 네트워크 진단 도구 적극 활용
- 보안 정책(최소 권한, 불필요 포트 차단 등) 준수
- 변경 전/후 영향도 및 서비스 정상 동작 반드시 검증
