
# ✅ Observer 서버 운영 & 배포 전체 TODO
_(Phase 0 ~ Phase 3, 기준 문서용)_

# 🧭 Phase 0. 프로젝트 현황 점검 (가장 먼저)

## 🔍 로컬 / IDE형 AI에서 할 일

- [x] Observer 실행 진입점(observer.py)이 **단일 진입점**인지 확인
- [x] 서버 배포에 불필요한 코드(실험용, 로컬 전용)가 포함되어 있지 않은지 점검
- [x] 현재 Observer가 **상태를 서버에 저장하지 않는 구조(stateless)**인지 확인
- [x] 로그 외에 서버에 남겨야 할 데이터가 없는지 확인

> 목적: 
> **“지금 배포하는 게 정확히 무엇인지”를 명확히 고정**


## 🧱 서버에서 할 일

- [x] 테스트용 잔여 컨테이너/프로세스 정리
- [x] 서버 리소스 기준값 확인 (CPU > 1코어, Memory > 512MB, Disk > 1GB)
- [x] Azure CLI 로그인 상태 확인 (az account show)
- [x] Terraform backend 연결 상태 확인 (storage account 접근)
- [x] 기존 Azure 리소스 정리 (VM 재활용, 불필요 확장만 정리)

> 목적: 
> **Observer 하나만 안정적으로 돌릴 수 있는 환경인지 확인**

---

# 🧱 Phase 1. 배포 전 기술 준비 (기반 다지기)

## 🔍 로컬 / IDE형 AI에서 할 일

- [x] Observer Docker 이미지 빌드 스크립트 점검
- [x] Docker 이미지가 **코드 변경 없이 재사용 가능**한지 확인
- [x] 로그 경로가 환경변수로 제어되는지 확인 (이미 완료 ⭕)
- [x] Observer 실행 시 필수 환경변수 목록 정리 (OBSERVER_LOG_DIR 등)
- [x] Observer 실행 실패 조건 명시 (환경변수 부재, 디렉토리 권한 등)
- [x] 서버 시간대 변경 시 Observer 재시작 필요 여부 테스트
- [x] Terraform 변수 파일(.tfvars) 민감 정보 확인 및 관리 방식 정리
- [x] Azure 리소스 명명 규칙 확정 (VM, Storage, Network 등)


## 🧱 서버에서 할 일

- [x] Docker 설치 여부 확인(안되어있음 초기화 상태)
- [x] Docker 설치 진행 (Docker 29.1.4, Compose v5.0.1)
- [x] Docker 서비스 자동 시작 여부 확인
- [x] Observer용 로그 디렉토리 생성
- [x] 로그 디렉토리 권한 확인 (non-root 기준)
- [x] 서버 재부팅 테스트 (Docker 자동 실행 확인)
- [x] 서버 시간대(timezone) 확인 및 고정
- [x] 서버 시간 동기화(NTP) 상태 확인
- [x] 서버 디스크 여유 공간 확인

---

# 🐳 Phase 2. Observer 실행 & 상시 운영 구조 구축

## 🔍 로컬 / IDE형 AI에서 할 일

- [x] Observer Docker 실행 명령 확정 (환경변수, 볼륨 포함)
- [x] 컨테이너 이름 규칙 확정 (observer-prod)
- [x] 로그 파일명/위치가 고정되는지 재확인 (/app/config/observer/observer.jsonl)
- [x] KIS API 연동 환경변수 추가 (실전투자만 사용)
- [x] 포트/네트워크 제거 (아웃바운드 통신만 하므로 불필요)
- [x] requirements.txt에 KIS API 패키지 추가 (requests, python-dotenv)
- [x] env.template 파일 생성 (KIS API 환경변수 템플릿)
- [x] Phase 2 배포 가이드 문서 작성 (docs/phase2_deployment_guide.md)
- [x] Phase 2 빠른 배포 스크립트 작성 (docs/phase2_quick_deploy.sh)
- [ ] 컨테이너 실행 실패 시 `docker logs <container_name>`로 즉시 원인 확인


## 🧱 서버에서 할 일

- [x] 배포 파일 준비 완료 (obs_deploy.tar.gz)
- [x] VM 상태 확인 (Docker 설치 확인, 기존 컨테이너 없음)
- [x] 배포 스크립트 및 가이드 문서 작성 완료
- [ ] VM에 파일 업로드 (수동: SCP/Portal/Bastion)
- [ ] Observer 컨테이너 **수동 1회 실행** (KIS API 연동 모드)
- [ ] 컨테이너 실행 상태 확인
- [ ] observer.jsonl 파일 생성 여부 확인 (/app/config/observer/)
- [ ] 실제 KIS 데이터 로그 기록 확인
- [ ] 컨테이너 중단 후 재실행 테스트
- [ ] 동일 이름의 기존 컨테이너 존재 여부 확인
- [ ] 컨테이너 중복 실행 방지 확인 (1개만 실행되는지)
- [ ] 컨테이너 실행 실패 시 `docker logs` 확인 후 수동 중단 원칙 적용

> **참고**: 배포 가이드는 `docs/phase2_complete_guide.md` 참조
> **배포 스크립트**: `deploy_to_vm.ps1` 실행 후 수동 업로드 필요

---

# ⚙️ Phase 3. systemd 기반 자동 관리 설정

## 🔍 로컬 / IDE형 AI에서 할 일

- [x] systemd 서비스 설계 내용 이해 (파일 하나)
- [x] Observer는 **재시작 대상**임을 명확히 인식
- [x] "컨테이너를 새로 만들지 않고, 기존 것을 재사용" 구조 이해
- [x] Observer 종료 시 시그널 처리 방식 확인 (SIGTERM, SIGINT)
- [x] 컨테이너 종료 시 로그 flush가 정상적으로 되는지 확인
- [x] systemd 서비스 파일 생성 (infra/systemd/observer.service)
- [x] Phase 3 배포 가이드 문서 작성 (docs/phase3_deployment_guide.md)
- [x] Phase 3 서버 명령어 가이드 작성 (docs/phase3_server_commands.md)
- [x] Phase 3 설계 문서 작성 (docs/phase3_systemd_design.md)

## 🧱 서버에서 할 일

- [ ] systemd 서비스 파일 생성 (/etc/systemd/system/observer.service)
- [ ] Docker 서비스 의존성 설정 (After=docker.service)
- [ ] systemd daemon reload 실행
- [ ] observer 서비스 enable 설정
- [ ] observer 서비스 start 실행
- [ ] 서비스 상태 확인 (systemctl status observer - active)
- [ ] systemd 서비스 로그 확인 (journalctl -u observer)
- [ ] systemd 재시작 루프 발생 여부 확인 (Restart=always 설정 검토)
- [ ] systemd 서비스 중지 시 Observer SIGTERM 정상 종료 확인
- [ ] systemd 설정 변경 후 서버 재부팅 테스트

---

# 🔁 Phase 4. 장애 & 복구 시나리오 검증

## 🔍 로컬 / IDE형 AI에서 할 일

- [ ] Observer 장애 판단 기준 정의 (프로세스 다운, 로그 중단, CPU 90% 이상)
- [ ] 장애 시 조치 원칙 수립 (즉시 중단 후 원인 분석)
- [ ] 로그 파일을 운영 상태 판단의 유일한 기준으로 명시
- [ ] 장애 발생 시 금지 작업 명시 (컨테이너 강제 삭제, 로그 수동 수정)


## 🧱 서버에서 할 일

- [ ] 컨테이너 강제 종료 테스트 (docker kill)
- [ ] systemd 자동 재시작 여부 확인 (systemctl status)
- [ ] 서버 재부팅 테스트 (reboot)
- [ ] 재부팅 후 Observer 자동 실행 확인 (docker ps)
- [ ] 재부팅 후 로그 파일 이어서 쌓이는지 확인
- [ ] 디스크 사용량 임계치 설정 (70% 경고, 85% 중단)
- [ ] 임계치 초과 시 수동 개입 원칙 정의
- [ ] 장애 발생 시 로그 확인 후 추가 조치 없이 중단 여부 판단

---

# 📦 Phase 5. 배포 이후 운영 (지금은 “작성만”)

## 🔍 로컬 / IDE형 AI에서 할 일

- [ ] docs/ 내 문서는 서버에 직접 복사하지 않는다
- [ ] Observer Docker 이미지 태그 버전 관리 규칙 정의 (v1.0.0, v1.0.1 등)
- [ ] 배포 변경 시 체크리스트 작성 (이미지 빌드 → 컨테이너 재시작)
- [ ] 배포 vs 운영 책임 분리 문서화 (배포: 이미지, 운영: 컨테이너)
- [ ] GitHub Actions 자동화 조건 정의 (수동 배포 안정화 후)
- [ ] 단일 운영 컨테이너 원칙 문서화 (observer 컨테이너만 유지)

## 🧱 서버에서 할 일

- [ ] 로그 디스크 사용량 주기적 확인 (df -h /app/logs)
- [ ] Observer 프로세스 상태 점검 (docker ps, systemctl status observer)
- [ ] 서버 재부팅 이력 관리 (last reboot 명령어)
- [ ] 이상 징후 발견 시 즉시 중단 원칙 적용 (로그 확인 후 수동 조치)

---

# 🚦 Phase 6. 자동화 진입 판단 체크포인트

- [ ] 서버 재부팅 후 Observer 자동 실행 확인 (systemctl status observer)
- [ ] 로그 파일 끊김 없이 누적되는지 확인 (tail -f observer.log)
- [ ] 실패 시 즉시 인지 가능한지 확인 (journalctl -u observer)
- [ ] 서버 상태 예측 가능성 확인 (CPU < 80%, Memory < 85%)
- [ ] 실행 중인 Observer 버전 즉시 식별 가능 (docker image inspect)

---

## ❌ 아직 일부러 하지 않는 것 (명시)

- [ ] ❌ 무인 자동 배포
- [ ] ❌ Terraform 재적용
- [ ] ❌ 로그 로테이션 구현
- [ ] ❌ 다중 Observer 운영
- [ ] ❌ 모니터링/알람 고도화



모든 문서는 ide형 ai에서 작성하도록 하고 폴더 경로는 "docs/" 폴더내에 필요시에는 폴더 생성해서 폴더단위로 관리 하도록 진행