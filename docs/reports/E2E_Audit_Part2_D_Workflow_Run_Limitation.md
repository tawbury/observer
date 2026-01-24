# E2E Audit Part 2-D: workflow_run 제한사항 및 해결

**생성 일시**: 2026-01-24 01:25 KST
**상태**: 🎯 부분 성공 (빌드 ✅, 배포 ⚠️)
**태그**: 20260124-012141

---

## 📋 요약

E2E 테스트에서 빌드는 성공했지만 배포가 자동 트리거되지 않았습니다.

### 성공한 부분
- ✅ GitHub Permissions 설정 완료
- ✅ build-push-tag.yml 정상 작동
- ✅ GHCR 이미지 푸시 성공
- ✅ 이미지: ghcr.io/tawbury/observer:20260124-012141

### 실패한 부분
- ❌ deploy-tag.yml 자동 트리거 실패

---

## 🔍 원인: workflow_run의 브랜치 제한

### GitHub Actions workflow_run 동작 방식

**공식 문서**:
> "Workflow files must be present in the default branch (master/main) of the repository for workflow_run to trigger them."

**현재 상황**:
```
observer 브랜치: deploy-tag.yml (workflow_run 포함)
master 브랜치: deploy-tag.yml (구버전, push 트리거만)
```

**결과**:
```
build-push-tag.yml 완료 → workflow_run 이벤트 발생
→ master 브랜치의 deploy-tag.yml 확인
→ workflow_run 트리거 없음 (구버전)
→ 배포 실행 안 됨
```

---

## ✅ 해결 방법

### 방법 1: observer → master PR/Merge (권장)

**장점**:
- ✅ workflow_run 영구적으로 작동
- ✅ 모든 개선사항 master에 반영
- ✅ E2E 파이프라인 완성

**단점**:
- ❌ Merge conflict 해결 필요
- ❌ 시간 소요 (5-10분)

**단계**:
```bash
# 1. Conflict 해결
git checkout master
git merge observer
# - .gitignore conflict 해결
# - Dockerfile conflict 해결
# - infra 파일 삭제 확인

# 2. Commit & Push
git add .
git commit -m "Merge observer: workflow improvements"
git push origin master

# 3. 테스트
TAG=$(date -u +"%Y%m%d-%H%M%S")
git tag $TAG
git push origin $TAG
# → build-push-tag.yml 실행
# → deploy-tag.yml 자동 트리거 (이제 작동!)
```

---

### 방법 2: deploy-tag.yml만 master에 체리픽 (빠른 해결)

**장점**:
- ✅ Merge conflict 회피
- ✅ 즉시 적용 가능
- ✅ workflow_run 작동

**단점**:
- ⚠️ 부분 적용 (HEALTHCHECK 등은 별도 merge 필요)

**단계**:
```bash
# 1. master로 전환
git checkout master

# 2. deploy-tag.yml만 가져오기
git checkout observer -- .github/workflows/deploy-tag.yml
git checkout observer -- .github/workflows/build-push-tag.yml

# 3. Commit & Push
git add .github/workflows/
git commit -m "feat: add workflow_run dependency for deploy"
git push origin master

# 4. 테스트
TAG=$(date -u +"%Y%m%d-%H%M%S")
git tag $TAG
git push origin $TAG
```

---

### 방법 3: 수동 배포 (임시 우회)

**장점**:
- ✅ 즉시 실행 가능
- ✅ workflow_run 문제 우회

**단점**:
- ❌ 자동화 목적 달성 못 함
- ❌ 매번 수동 실행 필요

**단계**:
```bash
# master 브랜치에 workflow_dispatch 추가 후
gh workflow run deploy-tag.yml -f image_tag=20260124-012141
```

---

## 📊 E2E 테스트 결과

### 빌드 파이프라인 (✅ 성공)

| 단계 | 상태 | 소요 시간 |
|------|------|----------|
| Checkout | ✅ | 2s |
| Set IMAGE_TAG | ✅ | 1s |
| Login to GHCR | ✅ | 3s |
| Build and push | ✅ | 1m11s |
| **총 소요 시간** | **✅** | **1m17s** |

**결과**:
```
✅ 이미지: ghcr.io/tawbury/observer:20260124-012141
✅ latest: ghcr.io/tawbury/observer:latest
```

### 배포 파이프라인 (⚠️ 트리거 안 됨)

**예상 동작**:
```
build-push-tag.yml 완료
→ workflow_run 이벤트 발생
→ deploy-tag.yml 자동 실행
→ SSH 배포
→ Health Check
```

**실제 동작**:
```
build-push-tag.yml 완료 ✅
→ workflow_run 이벤트 발생 ✅
→ master 브랜치의 deploy-tag.yml 확인 ✅
→ workflow_run 트리거 없음 (구버전) ❌
→ 배포 실행 안 됨 ❌
```

---

## 🎯 권장 조치 순서

### 우선순위 1: observer → master Merge

**이유**:
- E2E 파이프라인 완성
- 모든 개선사항 반영
- 영구적 해결

**예상 소요 시간**: 10분

**주의 사항**:
- Merge conflict 해결 필요:
  - `.gitignore`: observer 버전 사용
  - `Dockerfile`: observer 버전 사용 (HEALTHCHECK 수정 포함)
  - `docker-compose.yml`: observer 버전 사용
  - `infra/*`: 삭제 확인 (observer에서 제거됨)

### 우선순위 2: E2E 재테스트

Merge 완료 후:
```bash
# 1. 새 태그 생성
TAG=$(date -u +"%Y%m%d-%H%M%S")
git tag $TAG
git push origin $TAG

# 2. 전체 파이프라인 확인
# - build-push-tag.yml 실행
# - deploy-tag.yml 자동 트리거
# - 서버 배포
# - Health Check 통과

# 3. 검증
ssh azureuser@20.200.145.7
docker ps --format "{{.Image}}"
# → ghcr.io/tawbury/observer:20YYMMDD-HHMMSS 확인
```

---

## 📝 교훈

### 1. workflow_run의 브랜치 제한

**발견**:
- workflow_run은 default branch의 워크플로우 파일만 사용
- Feature branch에서 테스트 불가

**대응**:
- 중요한 워크플로우 변경은 master에 먼저 적용
- 또는 workflow_dispatch로 수동 테스트 후 merge

### 2. E2E 테스트의 완전성

**발견**:
- 빌드 성공 ≠ 배포 성공
- 전체 파이프라인 검증 필요

**대응**:
- 각 단계별 검증
- 자동화 트리거 동작 확인

### 3. GitHub Actions Permissions

**발견**:
- Repository Workflow Permissions 설정 중요
- write_package 권한 필요

**대응**:
- ✅ 해결됨: "Read and write permissions" 활성화

---

## 🔗 관련 문서

- [GitHub workflow_run 공식 문서](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_run)
- [E2E Audit Part 2-C](./E2E_Audit_Part2_C_Workflow_Permission_Fix.md) - Permissions 해결
- [Workflow Tag Management Analysis](./Workflow_Tag_Management_Analysis.md) - 태그 관리 방식

---

## ⏭️ 다음 단계

1. observer → master Merge 진행
2. Conflict 해결
3. E2E 재테스트
4. 성공 시 Part 2-E (완전한 E2E 검증) 문서화

---

**보고서 끝**

*Generated by E2E Audit System - Part 2-D (Workflow Run Limitation)*
