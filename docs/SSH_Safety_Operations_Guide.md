# SSH 안전성 운영 가이드

**버전:** v1.0.0  
**작성일:** 2026-01-11  
**적용:** QTS Observer 시스템 배포 및 운영  
**목적:** SSH 안전성 검증 시스템 운영 및 문제 해결  

---

## 1. 개요

### 1.1 SSH 안전성 철학

QTS Observer 시스템은 SSH를 **불변 인프라 경계(Immutable Infrastructure Boundary)**로 취급합니다:

- **검증 전용(Verify-Only)**: SSH 권한을 확인만 하고 자동 수정하지 않음
- **즉시 실패(Fail-Fast)**: SSH 문제 발생 시 즉시 배포 중단
- **수개 요구(Manual Intervention Required)**: 모든 SSH 문제는 수동 수정 필요

### 1.2 시스템 구성

```
SSH Safety System
├── ssh-safety-check.sh          # SSH 권한 검증 스크립트 (읽기 전용)
├── deploy.sh                    # 메인 배포 스크립트
├── deploy_to_infrastructure.sh  # 인프라 배포 스크립트
└── SSH_Troubleshooting_Guide.md # 문제 해결 가이드
```

---

## 2. SSH 안전성 검증 시스템

### 2.1 검증 항목

| 항목 | 요구 사항 | 검증 방법 |
|------|-----------|-----------|
| 홈 디렉토리 (`~`) | 권한: 700, 소유자: 현재 사용자 | `stat -c %a ~`, `stat -c %U ~` |
| `.ssh` 디렉토리 | 권한: 700, 소유자: 현재 사용자 | `stat -c %a ~/.ssh`, `stat -c %U ~/.ssh` |
| `authorized_keys` | 권한: 600, 소유자: 현재 사용자, 파일 존재 | `stat -c %a ~/.ssh/authorized_keys` |
| SSH 서비스 | 실행 중 상태 | `systemctl is-active sshd` |
| SSH 포트 | 수신 대기 중 | `netstat -ln \| grep :22` |

### 2.2 검증 스크립트 실행

> **⚠️ 중요:** SSH 안전성 검증 스크립트는 다음 용도로만 사용해야 합니다:
> - 운영자의 수동 검증
> - 배포 직전 사전 검증
> - **cron job이나 자동 복구 용도로 사용 금지**
> - **CI/CD 파이프라인에서 자동 수정 용도로 사용 금지**

```bash
# 수동 검증 실행 (운영자 직접 실행)
./infra/scripts/ssh-safety-check.sh

# 성공 예시 출력
[INFO] SSH 안전성 검증 시작 (사용자: azureuser)
[INFO] 홈 디렉토리 권한 정상: 700
[INFO] SSH 디렉토리 권한 정상: 700
[INFO] authorized_keys 권한 정상: 600
[INFO] SSH 키 1 개 등록됨
[INFO] SSH 서비스 실행 중 (sshd)
[INFO] SSH 포트 22 수신 대기 중
[INFO] ✅ SSH 안전성 검증 통과

# 실패 예시 출력
[ERROR] 홈 디렉토리 권한 오류: 755 (요구: 700)
[ERROR] ❌ SSH 안전성 검증 실패 (1 개 오류)

[ERROR] ❌ SSH 안전성 검증 실패 (1 개 오류)

🔧 수동 수정 필요:
   chmod 700 ~
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/authorized_keys
   chown -R $CURRENT_USER:$CURRENT_USER ~/.ssh

> **🚨 금지:** 자동화된 chmod/chown 실행은 절대 금지됩니다.
> SSH 권한 변경은 반드시 운영자가 직접 검토 후 수행해야 합니다.
```

---

## 3. 배포 프로세스

### 3.1 SSH 검증 게이트

모든 배포 스크립트는 SSH 환경에서 실행 시 자동으로 안전성 검증을 수행합니다:

```bash
# SSH 환경 감지 조건
if [ -n "$SSH_CONNECTION" ] || [ -n "$SSH_CLIENT" ] || [ -n "$SSH_TTY" ]; then
    # SSH 안전성 검증 실행
    ./scripts/ssh-safety-check.sh || exit 1
fi
```

### 3.2 배포 실행 흐름

```
배포 시작
    ↓
SSH 환경 감지?
    ├─ No → 일반 배포 진행
    └─ Yes → SSH 안전성 검증
           ├─ 통과 → 배포 진행
           └─ 실패 → 배포 중단 (수동 수정 필요)
```

### 3.3 배포 명령어

```bash
# 개발 환경 배포
./infra/scripts/deploy.sh dev deploy

# 스테이징 환경 배포
./infra/scripts/deploy.sh staging deploy

# 프로덕션 환경 배포
./infra/scripts/deploy.sh prod deploy

# 인프라 배포
./infra/scripts/deploy_to_infrastructure.sh
```

---

## 4. 운영 시나리오

### 4.1 정상 운영

#### SSH 권한이 올바른 경우
```bash
$ ./infra/scripts/deploy.sh staging deploy
🔍 SSH 연결 감지 - 안전성 검증 중...
[INFO] SSH 안전성 검증 시작 (사용자: azureuser)
[INFO] ✅ SSH 안전성 검증 통과
✅ SSH 안전성 검증 통과
🚀 QTS Observer 배포 시작 (staging)
... 배포 계속 진행 ...
```

### 4.2 SSH 문제 발생 시

#### 권한 문제로 배포 실패
```bash
$ ./infra/scripts/deploy.sh staging deploy
🔍 SSH 연결 감지 - 안전성 검증 중...
[ERROR] 홈 디렉토리 권한 오류: 755 (요구: 700)
[ERROR] ❌ SSH 안전성 검증 실패 (1 개 오류)
❌ SSH 안전성 검증 실패 - 배포 중단
🔧 수동 수정이 필요합니다. SSH 트러블슈팅 가이드를 참조하세요.
```

#### 수동 수정 후 재시도
```bash
# 1. 권한 수정 (운영자 직접 수행)
chmod 700 ~
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# 2. 검증 확인
./infra/scripts/ssh-safety-check.sh
# → "✅ SSH 안전성 검증 통과" 확인

# 3. 배포 재시도 (SSH 무결성 확인 후에만)
./infra/scripts/deploy.sh staging deploy
```

> **⚠️ 중요:** SSH 검증 실패 후 즉시 재배포를 시도하지 마십시오.
> SSH 무결성이 완전히 복원된 것을 확인한 후에만 배포를 재시도해야 합니다.

---

## 5. 문제 해결

### 5.1 일반적인 SSH 권한 문제

| 문제 | 원인 | 해결 방법 |
|------|------|-----------|
| `Permission denied` | 홈 디렉토리 권한 700 아님 | `chmod 700 ~` (운영자 직접 수행) |
| `Public key denied` | `.ssh` 디렉토리 권한 700 아님 | `chmod 700 ~/.ssh` (운영자 직접 수행) |
| `Authentication failed` | `authorized_keys` 권한 600 아님 | `chmod 600 ~/.ssh/authorized_keys` (운영자 직접 수행) |
| 키 파일 없음 | `authorized_keys` 파일 없음 | `ssh-copy-id` 또는 수동 키 복사 |

> **🚨 보안 경고:** CI/CD 파이프라인에 SSH 권한 변경 명령(chmod/chown)을 포함시키지 마십시오.
> 모든 SSH 권한 변경은 운영자의 직접 검토와 수행이 필요합니다.

### 5.2 진단 명령어

```bash
# 전체 상태 확인
./infra/scripts/ssh-safety-check.sh

# 개별 권한 확인
ls -ld ~
ls -ld ~/.ssh
ls -l ~/.ssh/authorized_keys

# SSH 서비스 상태
sudo systemctl status sshd

# 포트 확인
sudo netstat -tlnp | grep :22
```

### 5.3 응급 복구 절차

1. **SSH 접속 불가 시**
   ```bash
   # 콘솔 접속 후 권한 수정
   chmod 700 ~
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/authorized_keys
   chown -R $USER:$USER ~/.ssh
   ```

2. **SSH 서비스 문제**
   ```bash
   sudo systemctl restart sshd
   sudo systemctl status sshd
   ```

3. **방화벽 문제**
   ```bash
   sudo ufw status
   sudo ufw allow ssh
   ```

---

## 6. 운영 체크리스트 및 점검

### 6.1 운영 체크리스트

> **참고:** 이 섹션은 운영자의 수동 점검을 위한 체크리스트입니다.
> 자동화된 모니터링이나 자가 치유 메커니즘이 아닙니다.

#### 배포 전 체크리스트
- [ ] SSH 안전성 검증 스크립트 수동 실행
- [ ] 모든 검증 항목 통과 확인
- [ ] SSH 접속 테스트 수행

#### 일일 운영 체크리스트
- [ ] SSH 접속 로그 수동 검토
- [ ] 배포 로그 확인
- [ ] 비정상 접속 시도 수동 확인

#### 주간 운영 체크리스트
- [ ] SSH 키 목록 수동 검토
- [ ] 불필요한 SSH 키 제거 (운영자 직접)
- [ ] SSH 서비스 설정 수동 검토

### 6.2 로그 분석 (수동 검토)

> **중요:** 로그 분석은 운영자의 수동 검토용입니다.
> 자동화된 경보나 자가 치유 메커니즘이 아닙니다.

```bash
# SSH 접속 성공 로그 (운영자 수동 검토)
grep "Accepted" /var/log/auth.log | tail -10

# SSH 접속 실패 로그 (운영자 수동 검토)
grep "Failed" /var/log/auth.log | tail -10

# 배포 시 SSH 검증 로그 (운영자 수동 검토)
grep "SSH 안전성 검증" /var/log/deploy.log
```

---

## 7. 보안 권장사항

### 7.1 SSH 설정 강화

```bash
# /etc/ssh/sshd_config 권장 설정
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
ClientAliveInterval 300
```

### 7.2 키 관리

- **정기적인 키 로테이션**: 90일 주기 권장
- **최소 권한 원칙**: 필요한 사용자에게만 키 발급
- **키 비밀번호**: 개인 키는 반드시 암호화

### 7.3 접근 제어

- **IP 제한**: 특정 IP에서만 SSH 접속 허용
- **fail2ban**: 무차별 대입 공격 방지
- **로그 모니터링**: 비정상 접속 시도 탐지

---

## 8. 복구 운영 절차

### 8.1 SSH 복구 절차
1. **SSH 접속 불가 시**
   - Azure Portal에서 VM 콘솔 접속
   - 홈/SSH 디렉토리 및 authorized_keys 권한 수동 복구
   - 필요 시 SSH 공개 키 재설정 (Azure Portal)
   - 복구 후 반드시 ssh-safety-check.sh로 검증

2. **SSH 서비스 장애 시**
   - 콘솔에서 `sudo systemctl restart sshd` 실행
   - 서비스 상태 확인 및 로그 분석

3. **방화벽/네트워크 문제 시**
   - `sudo ufw status` 및 `sudo ufw allow ssh`로 규칙 확인
   - Azure NSG/VNet 설정 점검

### 8.2 Docker 컨테이너 복구 절차
1. **컨테이너 비정상 종료/오류 발생 시**
   - `docker ps -a`로 상태 확인
   - `docker restart <container>`로 재시작
   - 필요 시 `docker logs <container>`로 원인 분석
   - 이미지/볼륨 문제 시 백업 후 재배포

### 8.3 Azure VM 복구 절차
1. **VM 장애/재시작 필요 시**
   - Azure Portal에서 VM 상태(중지/재시작/시작) 직접 제어
   - VM 스냅샷/백업에서 복구 가능
   - 네트워크/디스크 문제는 Azure Portal에서 점검

### 8.4 전체 인프라/앱 재배포 절차
1. **재해 복구/전체 장애 발생 시**
   - 최신 IaC(Terraform) 코드로 인프라 재배포
   - `./infra/scripts/deploy_to_infrastructure.sh` 실행
   - 앱/컨테이너 재배포 후 정상 동작 확인
   - 복구 후 모든 운영 체크리스트 수행

### 8.5 GitHub Actions 워크플로우 실패 복구
1. **워크플로우 실패 시**
   - GitHub Actions 로그에서 오류 원인 확인
   - 필요한 경우 secrets, 환경 변수, 인프라 상태 점검
   - 실패 원인 수정 후 워크플로우 재실행
   - 반복 실패 시 수동 배포 절차로 전환

---

## 9. 연관 문서

### 9.1 필수 문서
- [SSH_Troubleshooting_Guide.md](SSH_Troubleshooting_Guide.md) - 상세 문제 해결 가이드
- [Ops_Dep_Arch.md](Ops_Dep_Arch.md) - 배포 아키텍처 가이드

### 9.2 참고 자료
- [Observer Architecture](arch/Obs_Architecture.md) - 시스템 아키텍처
- [CI/CD Workflows](../.github/workflows/) - 자동화 배포 파이프라인

---

## 10. 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|-----------|--------|
| v1.0.0 | 2026-01-11 | 초기 문서 생성 | QTS Ops Team |
| v1.1.0 | 2026-01-11 | 보안 강화 및 운영 명확화 추가 | QTS Ops Team |

---

## 11. 지원 및 연락처

### 기술 지원
- **시스템 관리자**: [관리자 연락처]
- **DevOps팀**: [DevOps팀 연락처]
- **보안팀**: [보안팀 연락처]

### 비상 연락
- **긴급 복구**: [긴급 연락처]
- **주말/휴일**: [비상 연락처]

---

**⚠️ 중요:** 이 가이드는 QTS Observer 시스템의 SSH 안전성을 유지하기 위한 공식 운영 절차입니다. 모든 조치는 이 가이드에 따라 수행해야 합니다.
