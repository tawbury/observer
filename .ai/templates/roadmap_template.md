# Meta
- Document Type: Roadmap
- Document ID: DOC-ROADMAP-YYYYMMDD-0001 (0001은 예시이며, 동일 날짜 내 생성 순번에 따라 0002, 0003처럼 증가시킵니다)
- Title: [프로젝트명 로드맵]
- Status: draft
- Created: {{CURRENT_DATE}}
- Updated: {{CURRENT_DATE}}
- Owner: {{USER}}
- Parent Document: [[anchor.md]]
- Related Reference: [[task_example.md]], [[run_record_example.md]] (실제 작업 시 구체적인 파일명으로 교체)
- Tags: roadmap, planning, execution-tracking

---

## 링크 규칙

- **Parent Document / Related Reference**: 실제 문서 파일명만 [[filename.md]] 형식으로 링크합니다.
- **와일드카드 패턴 사용 금지**: task_*.md 같은 패턴은 링크에 사용하지 않습니다.
- **올바른 예시**: [[roadmap_project_v1.md]], [[task_001_backend_api.md]], [[run_record_20260121_001.md]]

---

# [프로젝트명] 로드맵

> **안내**: 이 로드맵은 Task 실행을 주도하며 Run Record에 의해 지속적으로 업데이트됩니다.
> Task는 이 로드맵을 Parent Document로 참조하고, Run Record는 실행 증거로 이 로드맵에 피드백합니다.

---

## 1. 개요

### 목적
[이 로드맵의 목적과 달성하고자 하는 바를 간결하게 서술]

### 범위
[이 로드맵이 다루는 범위: 기간, 팀, 도메인 등]

### 운영 원칙
- 로드맵은 Run Record 피드백을 기반으로 지속적으로 업데이트됨
- Task는 로드맵 항목과 메타데이터로 연결됨 (Parent Document 필드)
- 상태는 Work Not Started, In Progress, Done 3가지만 사용
- 실행 세부사항은 Run Record에 기록, 로드맵은 구조와 상태만 관리

---

## 2. 목표 및 성공지표

### 정량 목표
- [측정 가능한 목표 1]: [목표값]
- [측정 가능한 목표 2]: [목표값]
- [측정 가능한 목표 3]: [목표값]

### 정성 목표
- [정성적 목표 1]
- [정성적 목표 2]
- [정성적 목표 3]

### 성공 기준
- [성공 판단 기준 1]
- [성공 판단 기준 2]
- [성공 판단 기준 3]

---

## 3. 범위 및 제외 사항

### 포함 (In Scope)
- [이번 로드맵에서 수행할 항목 1]
- [이번 로드맵에서 수행할 항목 2]
- [이번 로드맵에서 수행할 항목 3]

### 제외 (Out of Scope)
- [이번 로드맵에서 수행하지 않을 항목 1]
- [이번 로드맵에서 수행하지 않을 항목 2]
- [이번 로드맵에서 수행하지 않을 항목 3]

---

## 4. 마일스톤

### Phase 1: [단계명]
- **기한**: YYYY-MM-DD
- **상태**: Work Not Started | In Progress | Done
- **완료 기준**:
  - [기준 1]
  - [기준 2]
- **주요 Task**:
  - [[task_001.md]] - [Task 설명]
  - [[task_002.md]] - [Task 설명]
- **관련 Run Records**: [[run_record_20260121_001.md]]

### Phase 2: [단계명]
- **기한**: YYYY-MM-DD
- **상태**: Work Not Started | In Progress | Done
- **완료 기준**:
  - [기준 1]
  - [기준 2]
- **주요 Task**:
  - [[task_003.md]] - [Task 설명]
  - [[task_004.md]] - [Task 설명]
- **관련 Run Records**: [[run_record_20260121_002.md]]

### Phase 3: [단계명]
- **기한**: YYYY-MM-DD
- **상태**: Work Not Started | In Progress | Done
- **완료 기준**:
  - [기준 1]
  - [기준 2]
- **주요 Task**:
  - [[task_005.md]] - [Task 설명]
  - [[task_006.md]] - [Task 설명]
- **관련 Run Records**: [[run_record_20260121_003.md]]

---

## 5. Task 백로그

> **안내**: 각 Task는 체크박스 형태로 관리하며, 완료 시 [x] 표시합니다.
> Task 문서는 별도로 생성하고, Parent Document 필드에 이 로드맵을 링크합니다.

### 우선순위: High
- [ ] [[task_001.md]] - [Task 설명] | 담당: [Agent명] | Skill: [skill명] | 예상 산출물: [산출물명] | Run Record: (생성 후 링크)
- [ ] [[task_002.md]] - [Task 설명] | 담당: [Agent명] | Skill: [skill명] | 예상 산출물: [산출물명] | Run Record: (생성 후 링크)

### 우선순위: Medium
- [ ] [[task_003.md]] - [Task 설명] | 담당: [Agent명] | Skill: [skill명] | 예상 산출물: [산출물명] | Run Record: (생성 후 링크)
- [ ] [[task_004.md]] - [Task 설명] | 담당: [Agent명] | Skill: [skill명] | 예상 산출물: [산출물명] | Run Record: (생성 후 링크)

### 우선순위: Low
- [ ] [[task_005.md]] - [Task 설명] | 담당: [Agent명] | Skill: [skill명] | 예상 산출물: [산출물명] | Run Record: (생성 후 링크)
- [ ] [[task_006.md]] - [Task 설명] | 담당: [Agent명] | Skill: [skill명] | 예상 산출물: [산출물명] | Run Record: (생성 후 링크)

---

## 6. 변경 이력

> **안내**: Run Record 기반으로 로드맵을 갱신할 때마다 여기에 기록합니다.

| 날짜 | 변경 사항 | 근거 Run Record | 담당자 |
|------|----------|----------------|--------|
| YYYY-MM-DD | [변경 내용] | [[run_record_20260121_001.md]] | [담당자명] |
| YYYY-MM-DD | [변경 내용] | [[run_record_20260121_002.md]] | [담당자명] |
| YYYY-MM-DD | [변경 내용] | [[run_record_20260121_003.md]] | [담당자명] |

---

## 7. 참고 및 관련 문서

### 상위 문서
- [[anchor.md]] - 프로젝트 앵커 문서

### 의사결정 기록
- [[decision_001.md]] - [결정 제목]
- [[decision_002.md]] - [결정 제목]

### 관련 워크플로우
- [[workflow_name.workflow.md]] - [워크플로우명]

### 관련 에이전트
- [[agent_name.agent.md]] - [에이전트명]

### 관련 스킬
- .ai/skills/[agent_name]/[skill_name].md

---

## 운영 가이드

**로드맵 업데이트 프로세스**:
1. Run Record 검토: 완료된 작업과 제안사항 확인
2. Task 상태 업데이트: 완료된 Task 체크, 새 Task 추가
3. Phase 상태 갱신: 연결된 Task 상태에 따라 Phase 상태 변경
4. 변경 이력 기록: 변경 사항을 변경 이력 테이블에 추가
5. 다음 세션 계획: 다음 우선순위 Task 선정

**상태 판단 규칙**:
- **Work Not Started**: 연결된 Task가 없거나 모든 Task가 미완료
- **In Progress**: 최소 1개 이상의 Task가 진행 중
- **Done**: 연결된 모든 Task가 완료되고 산출물 검증 완료
