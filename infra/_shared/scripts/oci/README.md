# OCI (Oracle Cloud Infrastructure) 스크립트

Oracle Cloud VM 프로비저닝 및 초기화 스크립트 모음입니다.

## 파일 목록

| 파일 | 설명 |
|------|------|
| `oci_launch_instance.ps1` | OCI Compute 인스턴스 생성 (PowerShell) |
| `oci_helpers.ps1` | OCI 헬퍼 함수 (인스턴스 조회/삭제) |
| `oracle_bootstrap.sh` | Oracle VM Docker + Compose 설치 |
| `cloud-init-docker.yaml` | cloud-init 설정 (Docker 자동 설치) |

## 사용법

### 1. OCI 인스턴스 생성

```powershell
# OCI CLI 설치 필요
.\oci_launch_instance.ps1 `
    -CompartmentId "ocid1.compartment.oc1..xxxx" `
    -SubnetId "ocid1.subnet.oc1..yyyy" `
    -ImageId "ocid1.image.oc1..zzzz" `
    -DisplayName "observer-vm" `
    -Shape "VM.Standard.A1.Flex" `
    -Ocpus 2 `
    -MemoryInGBs 4
```

### 2. 수동 Docker 설치 (SSH 접속 후)

```bash
# oracle_bootstrap.sh 실행
bash oracle_bootstrap.sh
```

### 3. 인스턴스 관리

```powershell
# 인스턴스 조회
. .\oci_helpers.ps1
Get-OciInstanceByName -CompartmentId $compartmentId -DisplayName "observer-vm"

# 인스턴스 삭제
Remove-OciInstanceByName -CompartmentId $compartmentId -DisplayName "observer-vm" -Force
```

## 참고

- OCI CLI 설치: https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm
- ARM 인스턴스 (A1.Flex)는 Always Free Tier에서 사용 가능
