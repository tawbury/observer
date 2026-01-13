# Observer 배포 TODO 리스트

## 📅 업데이트: 2026-01-13

---

## 🎯 전체 로드맵

### Phase 0: 현황 점검 ✅
- [x] 로컬 배포 파일 준비 완료
- [x] VM 인프라 준비 완료 (Docker 설치)
- [x] 문서화 완료 (Phase 2-3 가이드)

### Phase 1: 기술 준비 ✅
- [x] Docker 설치 (v29.1.4)
- [x] Docker Compose 설치 (v5.0.1)
- [x] 로그 디렉토리 구조 설계
- [x] 환경변수 템플릿 작성

### Phase 2: Observer 수동 실행 ⏸️
- [ ] 로컬 프로젝트 정리
- [ ] VM 서버 초기화
- [ ] 파일 전송 (SCP)
- [ ] Docker 빌드 및 실행
- [ ] 로그 확인 및 검증

### Phase 3: systemd 자동 관리 ⏹️
- [ ] systemd 서비스 파일 생성
- [ ] 자동 시작 설정
- [ ] 재부팅 테스트

### Phase 4: 안정화 및 검증 ⏹️
- [ ] 1주일 안정 운영
- [ ] 장애 복구 시나리오 테스트
- [ ] 로그 모니터링

### Phase 5: Git 기반 배포 ⏹️
- [ ] VM에 Git 저장소 클론
- [ ] 수동 Pull + 재배포 프로세스 검증
- [ ] 배포 스크립트 작성

### Phase 6: GitHub Actions 자동화 ⏹️
- [ ] Workflow 파일 작성
- [ ] SSH 키 설정
- [ ] 자동 배포 테스트

### Phase 7: Terraform 통합 (선택) ⏹️
- [ ] 인프라 변경 필요 시 적용

---

## 📋 즉시 실행 계획 (오늘)

### ✅ Step 1: 로컬 프로젝트 정리 (30분)

**작업 목록:**
- [ ] Git rebase 중단 상태 해결
  - `git rebase --abort`
  - `git status` 확인
  
- [ ] Python 캐시 파일 삭제
  - `__pycache__` 폴더 삭제 (8개)
  - `*.pyc` 파일 삭제 (42개)
  
- [ ] 불필요한 폴더 정리
  - `temp/` 폴더 삭제
  - `project_tree.txt` 삭제
  - `qts_ops_deploy/` 확인 후 삭제 고려
  
- [ ] 신규 파일 Git 추가
  - `docs/phase2_*.md` (8개)
  - `docs/phase3_*.md` (4개)
  - `docs/todo_list.md`
  - `docs/file_transfer_diagnosis_report.md`
  - `infra/systemd/observer.service`
  - `app/obs_deploy/env.template`
  - `deploy_to_vm.ps1`
  
- [ ] 커밋 및 푸시
  - 커밋 메시지: "feat: Phase 2-3 Observer 배포 준비 완료"
  - `git push origin main`

**검증 기준:**
- [ ] `git status` → clean
- [ ] `__pycache__` → 0개
- [ ] `obs_deploy` → 115개 파일 유지

---

### ✅ Step 2: VM 서버 초기화 및 파일 전송 (30분)

**2-1. 서버 정리**
- [ ] 기존 잘못된 파일 삭제
```bash
rm -rf ~/observer-deploy
rm -rf ~/app
rm obs_deploy.tar.gz
```
- [ ] 디렉토리 확인: `ls -la ~`

**2-2. 로컬에서 파일 압축 및 전송**
- [ ] 압축 파일 생성
```powershell
cd d:\development\prj_ops
tar -czf obs_deploy.tar.gz app/obs_deploy/
```
- [ ] 파일 크기 확인 (300KB 이상)
- [ ] SCP 전송
```powershell
scp obs_deploy.tar.gz azureuser@20.200.145.7:~/
```

**2-3. VM에서 압축 해제 및 검증**
- [ ] 압축 해제
```bash
cd ~
tar -xzf obs_deploy.tar.gz
mv app/obs_deploy observer-deploy
cd observer-deploy
```
- [ ] 파일 검증
  - [ ] `observer.py`: 2,895 bytes
  - [ ] `paths.py`: 6,808 bytes
  - [ ] `src` 폴더: 111개 파일
  - [ ] 전체 크기: ~310KB

**검증 기준:**
- [ ] 모든 파일 정상 크기
- [ ] src 폴더 구조 완전
- [ ] 권한: azureuser:azureuser

---

### ✅ Step 3: Observer 수동 실행 (30분)

**작업 목록:**
- [ ] 환경변수 설정
```bash
cp env.template .env
nano .env  # KIS API 키 입력
```
  
- [ ] 필수 디렉토리 생성
```bash
mkdir -p data logs config/observer
```
  
- [ ] Docker 이미지 빌드
```bash
docker compose build
```
  
- [ ] 컨테이너 실행
```bash
docker compose up -d
```
  
- [ ] 실행 상태 확인
```bash
docker ps
docker logs observer-prod
```

**검증 기준:**
- [ ] 컨테이너 상태: running
- [ ] 로그: "Observer started" 메시지
- [ ] `observer.jsonl` 파일 생성
- [ ] KIS API 연동 확인

---

### ✅ Step 4: systemd 설정 (30분)

**작업 목록:**
- [ ] systemd 서비스 파일 생성
```bash
sudo nano /etc/systemd/system/observer.service
```
  
- [ ] 서비스 내용 입력 (infra/systemd/observer.service 참고)
  
- [ ] Daemon reload
```bash
sudo systemctl daemon-reload
```
  
- [ ] 서비스 활성화
```bash
sudo systemctl enable observer
sudo systemctl start observer
```
  
- [ ] 상태 확인
```bash
systemctl status observer
journalctl -u observer -f
```
  
- [ ] 재부팅 테스트
```bash
sudo reboot
# 재접속 후
systemctl status observer
docker ps
```

**검증 기준:**
- [ ] 서비스 상태: active (running)
- [ ] 재부팅 후 자동 시작
- [ ] 컨테이너 정상 작동

---

## 🚫 당분간 하지 않을 것

- [ ] ❌ GitHub Actions 자동화 (Phase 2-3 완료 후)
- [ ] ❌ Terraform 재적용 (필요 시에만)
- [ ] ❌ 문서 서버 배포 (로컬/Git에만 보관)
- [ ] ❌ 다중 Observer 운영 (단일 컨테이너만)

---

## 📊 진행 상황

**완료:** Phase 0-1 (준비 단계)  
**진행 중:** Phase 2 (수동 실행)  
**대기 중:** Phase 3-7

**예상 완료 시간:**
- 오늘 (2026-01-13): Phase 2-3 완료
- 이번 주: Phase 4 (안정화)
- 다음 주: Phase 5-6 (자동화)

---

## 🔄 업데이트 이력

- **2026-01-13 17:30**: TODO 리스트 최초 생성
- Phase 2-3 즉시 실행 계획 수립
- 로컬 정리 → 파일 전송 → 수동 실행 → systemd 설정

---

## 📝 참고 문서

- [Phase 2 전체 가이드](phase2_complete_guide.md)
- [Phase 2 서버 명령어](phase2_server_commands.md)
- [Phase 3 배포 가이드](phase3_deployment_guide.md)
- [프로젝트 현황 분석](project_status_report.md)

---

## 💡 중요 원칙

1. **단계별 검증**: 각 단계 완료 후 반드시 검증
2. **수동 우선**: 자동화 전 수동 배포 완벽히 성공
3. **문서 분리**: 가이드 문서는 서버에 배포 안 함
4. **안정화 우선**: 자동화는 안정 운영 후 진행
