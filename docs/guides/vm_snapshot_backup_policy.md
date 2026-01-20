# VM 스냅샷 및 백업 정책

이 문서는 QTS Ops 프로젝트의 Azure VM 스냅샷 및 백업 정책을 정리합니다.

## 1. 스냅샷 정책
- 운영 VM(예: observer-vm-01)에 대해 주기적으로 디스크 스냅샷 생성
- 장애/실수 발생 시 스냅샷에서 신속 복구 가능
- Azure Portal 또는 az cli로 수동/자동 생성 가능

### az cli 예시
```sh
az vm snapshot create --resource-group RG-OBSERVER-TEST --vm-name observer-vm-01 --name observer-vm-01-snap-$(date +%Y%m%d)
```

## 2. 백업 정책
- Azure Backup 서비스 활용 시, VM 전체 백업 및 복구 지점 관리 가능
- 장기 보관, 자동 스케줄, 정책 기반 관리 지원
- Azure Portal에서 Recovery Services Vault 생성 및 VM 등록

## 3. 복구 절차
- 스냅샷/백업에서 VM 또는 디스크 복원
- Azure Portal 또는 az cli로 복구 가능

### az cli 예시 (디스크 복원)
```sh
az snapshot create --resource-group RG-OBSERVER-TEST --source <디스크ID> --name <복구스냅샷명>
az disk create --resource-group RG-OBSERVER-TEST --source <복구스냅샷명> --name <새디스크명>
```

## 4. 자동화
- Azure Automation, Logic Apps, GitHub Actions 등으로 스냅샷/백업 자동화 가능
- ops-automation.sh 등에서 스크립트화 가능

## 참고
- 스냅샷/백업 주기, 보존 기간 등은 서비스 중요도에 따라 정책 수립
- 복구 테스트를 정기적으로 수행하여 신뢰성 확보
