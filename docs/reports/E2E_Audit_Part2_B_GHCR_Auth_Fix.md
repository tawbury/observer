# GHCR 배포 체인 E2E 감사 보고서 - Part 2-B: GHCR 인증 복구

**작성 시각**: 2026-01-23 17:24 KST  
**담당자**: DevOps E2E Executor + Auditor  
**상태**: ⚠️ BLOCKED (GHCR 403로 진행 불가)

---

## 1. 요약
- 목표: GHCR 인증 문제를 해결해 Part 2 롤백 E2E를 진행
- 결과: **403 Forbidden**으로 이미지 pull 불가 → PAT 재발급 필요
- 다음 단계: 새 PAT 발급 및 docker login 후 재시도 (지금은 BLOCKED)

---

## 2. 증거 (명령어 & 출력)

### 2.1 로컬 프리플라이트
- 명령: `git status --short`
- 출력:
  ```
  ?? docs/reports/E2E_Audit_Part1_F_Workflow_Hotfix_Verification.md
  ?? docs/reports/E2E_Audit_Part2_A_Rollback_Verification.md
  ```

- 명령: `git tag --sort=-creatordate | head -4`
- 출력:
  ```
  20260123-170510
  20260123-162549
  20260123-165323
  20260123-142040
  ```

### 2.2 서버 컨텍스트
- 명령: `ssh ... "whoami && pwd && docker --version && docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'"`
- 출력:
  ```
  azureuser
  /home/azureuser
  Docker version 29.1.4, build 0e6fee6
  NAMES                   IMAGE                        STATUS
  observer                obs_deploy-observer:latest   Up 17 minutes (unhealthy)
  observer-postgres       postgres:15-alpine           Up 17 minutes (healthy)
  observer-grafana        grafana/grafana:latest       Up 7 hours
  observer-prometheus     prom/prometheus:latest       Up 7 hours
  observer-alertmanager   prom/alertmanager:latest     Up 7 hours
  ```

### 2.3 GHCR 인증 상태 (토큰 미노출)
- 명령: `ssh ... "cat ~/.docker/config.json"`
- 출력 (auth 값은 Base64 그대로, 미해독):
  ```
  {
          "auths": {
                  "ghcr.io": {
                          "auth": "dGF3YnVyeTpnaG9fdXZzRjh2UzFwTHl2R1BkdmRnbzZBSHhmNjN0dk1kMG9FTG1W"
                  }
          }
  }
  ```

### 2.4 GHCR Pull 재현 (실패)
- 명령: `docker pull ghcr.io/tawbury/observer:latest`
- 출력:
  ```
  Error response from daemon: unknown: failed to resolve reference "ghcr.io/tawbury/observer:latest": unexpected status from HEAD request ... 403 Forbidden
  ```

- 명령: `docker pull ghcr.io/tawbury/observer:20260123-170510`
- 출력:
  ```
  Error response from daemon: unknown: failed to resolve reference "ghcr.io/tawbury/observer:20260123-170510": unexpected status from HEAD request ... 403 Forbidden
  ```

---

## 3. 원인 분석
1) 서버의 Docker 인증 토큰이 만료되었거나 권한이 부족함 (403 Forbidden)  
2) GHCR 패키지가 private인 경우, 토큰에 `read:packages` 및 리포지토리 접근 권한이 필요  
3) 현 상태에서는 GHCR 이미지 pull이 불가능하여 롤백/재배포 진행 불가

---

## 4. 필요 조치 (사용자 입력 필요)
**BLOCKED 해소를 위해 새 PAT가 필요합니다.**  
- 권장: GitHub **Fine-grained PAT**
  - 권한: Packages → Read
  - 리포지토리 접근: `tawbury/observer`에 Read 접근
- 대안: Classic PAT
  - 스코프: `read:packages` (패키지가 private이면 `repo`도 필요)

### 새 PAT 발급 후 수행할 명령 (서버)
> ⚠️ PAT 값은 절대 로그에 남기지 않습니다.
1. `docker logout ghcr.io`
2. `echo $NEW_PAT | docker login ghcr.io -u tawbury --password-stdin`
3. `docker pull ghcr.io/tawbury/observer:20260123-170510`
4. `docker pull ghcr.io/tawbury/observer:latest`

**현재 상태**: 새 PAT가 없으므로 여기서 중단합니다. (BLOCKED)

---

## 5. 다음 단계 (PAT 수령 후 진행)
1) 새 PAT로 GHCR 로그인 및 pull 재시도  
2) pull 성공 시 이미지 digest 캡처  
3) Part 1-F 재검증용 신규 태그 배포 및 서버에서 GHCR 이미지/컨테이너 확인  
4) 롤백 테스트 재실행 (Part 2-A 이어서 진행)

---

**보고서 상태**: BLOCKED (GHCR 인증 필요)

*본 문서는 GHCR 인증 문제 해결 전까지의 증거와 요구사항을 기록합니다.*
