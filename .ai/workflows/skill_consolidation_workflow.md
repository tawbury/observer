# 스킬 통합 및 AI 문서 거버넌스 워크플로우 (SSoT)

## 1) 문서 목적 (SSoT 선언)
- 세션이 바뀌어도 동일한 결과를 내기 위한 고정 워크플로우
- 본 프로젝트는 Git 비연동(개별 프로젝트)이며, 백업/리포트 기반으로 안전성을 확보

## 2) 적용 범위
- 대상 폴더: `.ai/agents`, `.ai/skills`, `.ai/templates`, `.ai/validators`, `.ai/workflows`, `.ai/.cursorrules`
- 산출물(리포트/매니페스트/운영 문서)은 최종적으로 `.ai/docs` 아래로 귀속

## 3) 핵심 원칙 (Non-negotiables)
- 1스텝 = 1프롬프트 (리뷰/실행 분리)
- Review(READ-ONLY) → Execution 분리
- Execution 전에 `archived` 백업 필수
- Phase 중 삭제 금지(삭제 게이트로만 관리)
- Pre/Post reference scan 필수
- 의미/기능 100% 보존이 최우선
- 중복 제거는 “파일 통합” 또는 “경계/의존성 정리” 중 리스크 낮은 방법 선택

## 4) 표준 폴더 규칙 (최종 귀속 포함)
- Active skills: `.ai/skills/<agent>/`
- Archived backups: `backup/phase2/skills/<agent>/`
- Deprecated stubs: `backup/phase2/skills/deprecated/`
- Workflow SSoT: `.ai/workflows/`
- AI Docs SSoT (final): `.ai/docs/`
  - `.ai/docs/reports/`
  - `.ai/docs/manifests/`
  - (optional) `.ai/docs/readme/`
- Final Manifest SSoT: `.ai/docs/manifests/PHASE2_DEPRECATED_SKILLS_MANIFEST.md` (리팩터 중에는 외부에 임시로 있을 수 있으나, Closeout 시 반드시 최종 경로로 이동)
- NOTE: 리팩터 중 `docs/reports` 등에 임시 위치 가능하나, Closeout 시 모두 `.ai/docs/`로 이관

## 5) 표준 실행 시퀀스 (체크리스트)
### Review Step (READ-ONLY)
- [ ] inventory (대상 스킬/파일 목록화)
- [ ] mapping verification (agent 매핑 확인)
- [ ] duplication candidates grouping (중복/유사도 묶기)
- [ ] batch plan (one prompt per batch 계획)

### Execution Step
- [ ] A) Pre-flight scan (참조 카운트/위치 기록)
- [ ] B) Backup to archived (전체 파일 .bak 생성)
- [ ] C) Edit skills (merge OR dependency/boundary 정리)
- [ ] D) Update agent mapping / dependency rules
- [ ] E) Update validator rules (minimal)
- [ ] F) Post-flight scan (참조 재확인, 깨진 링크 0 확인)
- [ ] G) Update manifest (append-only)
- [ ] H) Write report

## 6) 병합 vs 분리 유지 결정 기준 (운영/리스크 관점)
- 병합 추천 조건 (high confidence near-identical): 목적/레벨/도구/입출력이 거의 동일, 유지보수 비용 > 분할 가치, 통합 시 문서 크기/가독성 허용
- 분리 유지 추천 조건: 계층/선행 관계 존재, 기술 특화(React/NoSQL 등), 미래 확장 범위가 넓음, 역할이 명확히 다른 경우
- 경계 재작성/중복 제거만 하는 조건: 공통 개념은 참조로 연결, 실행 로직 중복을 제거하거나 분리된 책임을 명시할 때

## 7) 삭제 게이트 (Deletion Gate)
- 삭제는 Phase 종료 + 운영 테스트(1주) + 최종 승인 후
- 삭제 대상은 `deprecated` 폴더만
- `archived`는 보존(최소 Phase 종료 후까지)
- Final Manifest SSoT: `.ai/docs/manifests/PHASE2_DEPRECATED_SKILLS_MANIFEST.md` (Closeout 시 강제 귀속, 임시 외부 위치 금지)

## 8) Closeout 절차 (중요)
- Closeout 시 반드시 수행:
  - 모든 AI 관련 리포트/매니페스트/운영 문서를 `.ai/docs/` 로 이관
  - 기존 외부 위치에 남아있는 문서는 제거 또는 리다이렉트 후 최종 정리
  - Closeout README 생성 (SSoT index)
### Closeout 체크리스트 (실행 가능)
- [ ] Closeout Pre-scan: `.ai/` 외부 AI 문서(예: `docs/reports`)를 열거하고 이동 리스트 작성
- [ ] Move policy: 원본을 `.ai/docs/`로 이동하고, 필요 시 구 경로에 1줄 리다이렉트 파일 임시 배치
- [ ] Closeout Post-scan: `.ai/docs/`에 모든 문서가 존재하는지 확인하고, 외부 AI 문서 위치는 비워두거나 리다이렉트만 남김
- 최종 상태: external AI-doc locations = 0

## 11) 명명 규칙 (Naming Conventions)
- Reports: `PHASE2_SKILLS_<STEP>_<AGENT>_<BATCH>_REPORT.md`
- Reviews: `PHASE2_SKILLS_<STEP>_<AGENT>_<BATCH>_REVIEW.md`
- Backups: `<original_filename>.bak_YYYYMMDD`
- Deprecated: 원본 파일명 유지, deprecated 폴더로만 위치 변경
- 모든 명명 규칙은 검색성과 Closeout 자동화를 위해 필수

## 12) 의존성/관계 문장 템플릿
- `Prerequisite: <skill_file>`
- `Related Skills: <skill_file>, <skill_file>`
- `Used by: <skill_file>`
- Soft rule: `권장: <skill_file>를 함께 참조` (하드 의존성 아님)
- Validator는 Prerequisite에만 하드 룰을 적용하며, Soft rule은 권고 용도로만 사용

## 9) 프롬프트 템플릿 (짧은 skeleton)
- Review prompt skeleton: "[Phase/Step] 대상 스킬 목록, 현황 요약, 중복/의존성 조사, 리포트만 작성 (READ-ONLY)."
- Execution prompt skeleton: "[Phase/Step] Pre-scan → 백업 → 스킬 수정(병합 또는 의존성) → agent/validator 갱신 → Post-scan → manifest/report 작성."
- Move-to-.ai/docs closeout skeleton: "모든 리포트/매니페스트/운영 문서 `.ai/docs/` 이관, 외부 경로 정리, Closeout README 작성."

## 10) 운영자 검수 포인트 (5~10개)
- [ ] broken references 0
- [ ] circular dependency 0
- [ ] mapping mismatch 0 (agent 스킬 매핑 정확성)
- [ ] deprecated isolation (deprecated 폴더 내 격리)
- [ ] archived backup existence (최신 .bak 확인)
- [ ] report/manifest updated (append-only 반영)
- [ ] 의미/기능 손실 없음
- [ ] Phase 중 삭제 없음

## 변경 이력
- 2026-01-19: Manifest SSoT 경로 명시, 명명 규칙 추가, 의존성 문장 템플릿 추가, Closeout 체크리스트 강화
