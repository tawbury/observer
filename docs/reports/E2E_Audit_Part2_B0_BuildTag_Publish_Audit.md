# GHCR 태그 빌드/퍼블리시 감사 보고서 - Part 2-B0 (Build Tag Publish Audit)

**작성 시각**: 2026-01-23 17:44 KST  
**담당자**: CI Build/Publish Auditor  
**상태**: ⚠️ 검증 대기 (워크플로 추가 완료, 새 태그 실행 필요)

---

## 1. 문제 진단
- GHCR에 `latest` 이미지는 존재하지만, 타임스탬프 태그(예: `20260123-170510`)가 존재하지 않음.
- 리포지토리에 **빌드/푸시 워크플로가 부재** → 태그를 푸시해도 이미지를 GHCR에 올리는 단계가 없음.
- 배포 워크플로(`deploy-tag.yml`)는 서버에 배포만 수행하며, 이미지 빌드/푸시 로직이 없음.

---

## 2. 증거 (명령과 출력)
### 2.1 레지스트리 상태 확인
- 명령: `docker manifest inspect ghcr.io/tawbury/observer:latest`
- 출력 요약:
  ```
  digest: sha256:ec0abf09f448fd8139e7274f53ea64339efbb5d043ef60e814f8ef801f4a53e8 (amd64)
  ```
- 명령: `docker manifest inspect ghcr.io/tawbury/observer:20260123-170510`
- 출력: `manifest unknown` (태그 없음)

### 2.2 워크플로 존재 여부
- 명령: `dir .github/workflows`
- 출력:
  ```
  build-push-tag.yml   (신규, 2026-01-23 17:43)
  deploy-tag.yml       (배포용)
  ```

### 2.3 배포 워크플로 내용 확인 (요약)
- 파일: `.github/workflows/deploy-tag.yml`
- 트리거: `push` → tags `20*`, `workflow_dispatch`
- 주요 단계: IMAGE_TAG 계산 → SSH로 서버 배포 → 헬스체크
- **결핍**: `docker/login-action`, `docker/build-push-action` 없음 → GHCR로 이미지를 빌드/푸시하지 않음

### 2.4 태그 설정 로직
- `deploy-tag.yml`에서 `IMAGE_TAG`는 설정되지만, 빌드/푸시에 사용되는 단계가 없음 (순수 배포 전용)

---

## 3. 근본 원인 (Root Cause)
1) **빌드/푸시 워크플로 부재**: 태그 푸시 시 GHCR에 이미지를 올리는 자동화가 없음.  
2) **배포 워크플로만 존재**: 서버에서 기존 로컬/기본 이미지를 재사용, GHCR 태그 이미지 미생성.

---

## 4. 최소 수정안 (적용 완료)
- 신규 워크플로 추가: `.github/workflows/build-push-tag.yml`
- 트리거: 태그 푸시(`20*`) 및 수동 `workflow_dispatch`
- 권한: `packages: write`, `contents: read`
- 단계:
  1) 체크아웃
  2) IMAGE_TAG 설정 (`inputs.image_tag` 또는 `github.ref_name`)
  3) GHCR 로그인 (`docker/login-action@v3`, `GITHUB_TOKEN` 사용)
  4) 빌드/푸시 (`docker/build-push-action@v6`, Dockerfile: `app/obs_deploy/Dockerfile`)
     - 태그: `ghcr.io/tawbury/observer:${{ github.ref_name }}` 및 `ghcr.io/tawbury/observer:latest`

### 변경 파일 목록
- 추가: [.github/workflows/build-push-tag.yml](.github/workflows/build-push-tag.yml)

---

## 5. 검증 계획 (대기)
> 현재 새 태그 실행 전이므로 검증 **대기** 상태입니다. 아래 절차 수행 후 결과를 기록해야 합니다.

1) 새 태그 생성 및 푸시 (예: `NEW_TAG=20260123-174500`):
   ```bash
   git tag 20260123-174500
   git push origin 20260123-174500
   ```
2) GitHub Actions에서 `Build & Push Observer Image (Tag)` 워크플로 성공 여부 확인.
3) GHCR 태그 존재 확인:
   ```bash
   docker manifest inspect ghcr.io/tawbury/observer:20260123-174500
   docker manifest inspect ghcr.io/tawbury/observer:latest
   ```
   - 기대: 두 명령 모두 digest를 반환해야 함.
4) (선택) 배포 워크플로 실행 후 서버에서 실제 이미지 태그 확인:
   ```bash
   ssh azureuser@20.200.145.7 "docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'"
   ```

---

## 6. 결론
- **문제**: GHCR에 타임스탬프 태그가 없는 이유는 빌드/푸시 자동화가 없었기 때문.
- **조치**: 태그 푸시 시 GHCR로 빌드·푸시하는 워크플로를 추가하여 최소 수정 완료.
- **다음 단계**: 새 태그 푸시 후 워크플로 실행 및 GHCR manifest로 존재 확인. 결과를 추적 보고서에 추가 필요.

---

**보고서 상태**: 검증 대기 (새 태그 실행 필요)
