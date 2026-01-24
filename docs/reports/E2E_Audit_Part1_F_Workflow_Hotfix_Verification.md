# GHCR 배포 체인 E2E 감사 보고서 - Part 1-F: 워크플로 수정 검증

**생성 일시**: 2026-01-23 17:08  
**담당자**: DevOps E2E Executor + Auditor  
**배포 태그**: `20260123-170510`  
**GitHub Actions 실행**: [Run #21279087323](https://github.com/tawbury/observer/actions/runs/21279087323)

---

## 📋 요약

Part 1-E에서 발견된 `server_deploy.sh` 인자 순서 불일치 문제를 해결하고, 전체 배포 체인의 성공을 검증했습니다.

### 주요 성과
- ✅ GitHub Actions 워크플로 수정 완료 (commit `1696f4c`)
- ✅ Preflight 검증 로직 추가 (디버깅 가시성 개선)
- ✅ 전체 배포 프로세스 성공 (Build → Push → Deploy → Health Check)
- ✅ 서버 운영 상태 정상 확인 (Observer API 200 OK)

---

## 🔍 문제 분석

### Part 1-E에서 발견된 문제
GitHub Actions 워크플로가 서버의 `server_deploy.sh` 스크립트를 잘못된 인자 순서로 호출했습니다.

**잘못된 호출 방식 (Before)**:
```bash
./server_deploy.sh deploy "$IMAGE_TAG"
```

**서버 스크립트 기대 형식**:
```bash
./server_deploy.sh DEPLOY_DIR COMPOSE_FILE IMAGE_TAG MODE
```

**오류 증거** (Run #21278819226 로그):
```
[ERROR] 배포 디렉토리 없음: deploy
[ERROR] 입력 검증 실패
```
→ "deploy"를 배포 디렉토리 경로로 오해석함

---

## 🛠 해결 방안

### 1. 워크플로 파일 수정
**파일**: `.github/workflows/deploy-tag.yml`  
**커밋**: `1696f4c` ("fix: correct server_deploy.sh invocation args...")  
**변경일**: 2026-01-23 17:03 KST

#### 변경 사항 (Lines 85-95)

**Before**:
```yaml
script: |
  cd "$DEPLOY_DIR"
  ./server_deploy.sh deploy "$IMAGE_TAG"
```

**After**:
```yaml
script: |
  cd "$DEPLOY_DIR"
  
  # Preflight 검증 (디버깅용)
  echo "Current directory: $(pwd)"
  echo "Available files:"
  ls -la | head -10
  echo "IMAGE_TAG is set: $([ -n "$IMAGE_TAG" ] && echo "true" || echo "false")"
  
  # 배포 스크립트 실행 (올바른 인자 순서: DEPLOY_DIR COMPOSE_FILE IMAGE_TAG MODE)
  ./server_deploy.sh "$DEPLOY_DIR" docker-compose.server.yml "$IMAGE_TAG" deploy
```

#### 개선 포인트
1. **올바른 인자 전달**: 4개 인자를 정확한 순서로 전달 (`DEPLOY_DIR`, `COMPOSE_FILE`, `IMAGE_TAG`, `MODE`)
2. **Preflight 검증**: 배포 전 환경 상태 확인 (현재 디렉토리, 파일 목록, 환경 변수)
3. **가독성 개선**: 인라인 주석으로 각 인자의 의미 명시

---

## ✅ 검증 결과

### 배포 실행 정보
- **태그**: `20260123-170510`
- **실행 URL**: https://github.com/tawbury/observer/actions/runs/21279087323
- **Job ID**: 61244597126
- **실행 시각**: 2026-01-23 08:05:24 UTC (17:05 KST)
- **총 소요 시간**: 36초
- **최종 상태**: ✅ **SUCCESS**

---

### 단계별 검증

#### Step 1: Checkout Repository
```
✓ Status: SUCCESS
Duration: 0 seconds
```

#### Step 2: Determine IMAGE_TAG from Git Tag
```
✓ Status: SUCCESS
Tag Detected: 20260123-170510
```

#### Step 3: Print Context for Debugging
```
✓ Status: SUCCESS
Logs:
  - GITHUB_REF: refs/tags/20260123-170510
  - GITHUB_REF_NAME: 20260123-170510
  - IMAGE_TAG: 20260123-170510
```

#### Step 4: Log in to GitHub Container Registry
```
✓ Status: SUCCESS
Registry: ghcr.io
```

#### Step 5: Build and Push Docker Image
```
✓ Status: SUCCESS
Image: ghcr.io/tawbury/observer:20260123-170510
Build Time: ~8 seconds
Push Time: ~3 seconds
```

#### Step 6: Setup SSH Known Hosts
```
✓ Status: SUCCESS
Host: 20.200.145.7
```

#### Step 7: Deploy via SSH ⭐ **핵심 단계**
```
✓ Status: SUCCESS
Duration: 26 seconds

Key Evidence from Logs:
┌─────────────────────────────────────────────────────────────────┐
│ out: Current directory: /home/azureuser/observer-deploy         │
│ out: IMAGE_TAG is set: true                                     │
│ out: Available files:                                           │
│   - server_deploy.sh                                            │
│   - docker-compose.server.yml                                   │
│   - .env                                                        │
│   - (... 7 more files)                                          │
│                                                                 │
│ out: [INFO] 배포 설정:                                          │
│ out: [INFO]   • 배포 디렉토리: /home/azureuser/observer-deploy  │
│ out: [INFO]   • Compose 파일: docker-compose.server.yml        │
│ out: [INFO]   • 이미지 TAG: 20260123-170510                    │
│ out: [INFO]   • 배포 모드: deploy                               │
│ out: [INFO] ✅ 입력 검증 완료                                   │
│                                                                 │
│ out: [INFO] 🔄 이미지 TAG 20260123-170510 배포 중...           │
│ out: [+] Running 2/2                                            │
│ out:  ✔ Container observer-postgres  Started                   │
│ out:  ✔ Container observer           Started                   │
│                                                                 │
│ out: [INFO] 🏥 서비스 헬스 체크 중...                          │
│ out: [INFO] ✅ 배포 완료                                        │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 8: Post-deploy Health Check
```
✓ Status: SUCCESS
Duration: 2 seconds

Health Check Details:
┌─────────────────────────────────────────────────────────────────┐
│ Endpoint:     http://localhost:8000/health                      │
│ Timeout:      60 seconds                                        │
│ Retry every:  5 seconds                                         │
│                                                                 │
│ Attempt 1/12: Checking health...                               │
│ ✅ Health check PASSED                                          │
│                                                                 │
│ ✅ POST-DEPLOY HEALTH CHECK: PASSED                             │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 9: Deployment Summary
```
✓ Status: SUCCESS

Final Output:
═══════════════════════════════════════════════════════════════════
✅ DEPLOYMENT SUCCESS
═══════════════════════════════════════════════════════════════════
Image Tag:    20260123-170510
Deploy Time:  2026-01-23 08:05:54 UTC
Server:       20.200.145.7
User:         azureuser
Compose:      docker-compose.server.yml
Health Check: ✅ PASSED (200 OK)
═══════════════════════════════════════════════════════════════════
```

---

## 📊 운영 상태 확인

### 컨테이너 상태
실제 서버에서 실행 중인 컨테이너:

| Container Name       | Status | Health   | Ports         |
|---------------------|--------|----------|---------------|
| observer            | Up     | healthy  | 0.0.0.0:8000→8000 |
| observer-postgres   | Up     | healthy  | 5432          |

### API 헬스 체크
```bash
curl http://localhost:8000/health
HTTP/1.1 200 OK
```

### Observer 로그 확인
서버 시작 시 정상적으로 초기화된 주요 컴포넌트:
- ✅ Universe Scheduler (Task scheduler initialized)
- ✅ Track A Collector (Stock tracking started)
- ✅ FastAPI Server (Application startup complete on 0.0.0.0:8000)

---

## 🎯 결론

### 성공 요인
1. **정확한 문제 진단**: Part 1-E에서 인자 순서 불일치를 명확히 식별
2. **단계적 수정**: Preflight 검증 추가로 향후 디버깅 용이성 확보
3. **증거 기반 검증**: 각 단계의 로그를 수집하여 성공 여부 명확히 확인

### 워크플로 안정성 확보
- GitHub Secrets 설정 완료 (Part 1-D)
- SSH 연결 정상 작동
- 스크립트 인자 전달 수정 (Part 1-F) ← **현재 단계**
- 전체 E2E 체인 검증 완료

---

## 📝 다음 단계

### Part 2: 완전한 E2E 워크플로 실행
이제 전체 배포 체인이 안정화되었으므로 다음 작업을 진행할 수 있습니다:

1. **정기 배포 테스트**: 새 기능 추가 시 동일한 태그 기반 배포 프로세스 사용
2. **모니터링 강화**: Grafana/Prometheus를 통한 서버 상태 지속 관찰
3. **롤백 테스트**: `server_deploy.sh rollback` 명령 검증
4. **운영 매뉴얼 작성**: 배포 표준 운영 절차(SOP) 문서화

### 권장 사항
- ✅ **현재 시스템 운영 준비 완료**: 프로덕션 배포 가능
- 📊 **서버 로그 모니터링**: `/home/azureuser/observer-deploy/logs/` 정기 확인
- 🔒 **백업 전략 수립**: 데이터베이스 정기 백업 자동화
- 🚨 **알람 설정**: Health check 실패 시 알림 메커니즘 구축

---

## 🔗 관련 문서

- [Part 1-A: 초기 E2E 감사 보고서](./E2E_Audit_Part1_A_Initial_Execution.md)
- [Part 1-D: GitHub Secrets 설정 요구사항](./E2E_Audit_Part1_D_Secrets_Setup_Required.md)
- [Part 1-E: Secrets 설정 후 검증](./E2E_Audit_Part1_E_Post_Secrets_Verification.md)
- [GitHub Actions 실행 로그](https://github.com/tawbury/observer/actions/runs/21279087323)
- [server_deploy.sh 스크립트](https://github.com/tawbury/observer/blob/main/app/obs_deploy/server_deploy.sh)

---

**보고서 끝**

*Generated by DevOps E2E Audit System - Part 1-F (Workflow Hotfix Verification)*
