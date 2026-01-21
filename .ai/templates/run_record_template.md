# Meta
- Document Type: Run Record
- Document ID: DOC-RUN-YYYYMMDD-0001 (0001은 예시이며, 동일 날짜 내 생성 순번에 따라 0002, 0003처럼 증가시킵니다)
- Title: [실행 기록 - 간단 제목]
- Status: active
- Created: {{CURRENT_DATE}}
- Updated: {{CURRENT_DATE}}
- Owner: {{USER}}
- Parent Document: [[roadmap.md]] 또는 [[task_example.md]]
- Related Reference: [[task_example.md]], [[roadmap_example.md]], [[developer.agent.md]] (실제 작업 시 구체적인 파일명으로 교체)
- Tags: run-record, execution, evidence

---

## 링크 규칙

- **Parent Document / Related Reference**: 실제 문서 파일명만 [[filename.md]] 형식으로 링크합니다.
- **와일드카드 패턴 사용 금지**: task_*.md 같은 패턴은 링크에 사용하지 않습니다.
- **올바른 예시**: [[roadmap_project_v1.md]], [[task_001_backend_api.md]], [[developer.agent.md]]

---

# Run Record: [실행 세션 제목]

> **안내**: Run Record는 사실과 결과 중심의 실행 로그입니다.
> Parent Document는 Task 문서(또는 별도 Task 없이 Roadmap 직접 참조), Related Reference에는 Roadmap, 관련 Skill/Agent 문서를 링크합니다.
> Run Record는 Roadmap 업데이트 시 참조됩니다.

---

## 1. 실행 요약

**한 줄 요약**: [이번 실행에서 무엇을 했는지 한 문장으로 요약]

**결과 상태**:
- ✅ 성공 | ⚠️ 부분 성공 | ❌ 실패 | 🚧 진행 중

**실행 일시**: YYYY-MM-DD HH:MM ~ HH:MM

**실행 담당**: [Agent명 또는 담당자명]

---

## 2. 실행 컨텍스트

### 왜 (Why)
[이 실행을 수행한 이유 및 배경]

### 무엇을 (What)
[구체적으로 무엇을 수행했는지]

### 어디까지 (Scope)
[계획 대비 실제 수행 범위]

---

## 3. 입력

### 사용한 자료
- [[document_001.md]] - [자료 설명]
- [[document_002.md]] - [자료 설명]

### 파라미터 및 설정
- 파라미터 1: [값]
- 파라미터 2: [값]
- 설정 항목: [값]

### 전제 조건
- [전제 조건 1]
- [전제 조건 2]
- [전제 조건 3]

---

## 4. 실행

### 수행 단계 요약
1. [단계 1 설명]
   - 세부 작업: [작업 내용]
   - 소요 시간: [시간]

2. [단계 2 설명]
   - 세부 작업: [작업 내용]
   - 소요 시간: [시간]

3. [단계 3 설명]
   - 세부 작업: [작업 내용]
   - 소요 시간: [시간]

### 사용한 Skill
- [[skill_001.md]] - [Skill 설명]
- [[skill_002.md]] - [Skill 설명]

### 실행 Agent
- [[agent_name.agent.md]] - [Agent 역할 설명]

---

## 5. 출력 및 산출물

### 생성된 파일
- `경로/파일명.확장자` - [파일 설명]
- `경로/파일명.확장자` - [파일 설명]

### 생성된 문서
- [[output_document_001.md]] - [문서 설명]
- [[output_document_002.md]] - [문서 설명]

### 결과 데이터
- [결과 데이터 1]: [값 또는 설명]
- [결과 데이터 2]: [값 또는 설명]

### 외부 링크
- [외부 링크 1]: URL
- [외부 링크 2]: URL

---

## 6. 이슈 및 리스크

### 발생한 문제
| 문제 | 심각도 | 우회 방법 | 해결 여부 |
|------|--------|----------|----------|
| [문제 설명] | High/Medium/Low | [우회 방법] | ✅/❌ |
| [문제 설명] | High/Medium/Low | [우회 방법] | ✅/❌ |

### 미해결 이슈
- [미해결 이슈 1] - [상세 설명]
- [미해결 이슈 2] - [상세 설명]

### 식별된 리스크
- [리스크 1] - 영향도: [High/Medium/Low]
- [리스크 2] - 영향도: [High/Medium/Low]

---

## 7. 다음 액션

### Roadmap에 반영할 내용

#### Task 상태 업데이트 제안
- [[task_001.md]]: Work Not Started → In Progress
- [[task_002.md]]: In Progress → Done
- [[task_003.md]]: 새 Task 추가 필요

#### Phase 상태 업데이트 제안
- Phase 1: In Progress 유지
- Phase 2: Work Not Started → In Progress

#### 새로운 Task 제안
- [새 Task 제목]: [간단 설명]
- [새 Task 제목]: [간단 설명]

### 즉시 수행 필요 액션
1. [액션 1] - 담당: [Agent명] - 기한: YYYY-MM-DD
2. [액션 2] - 담당: [Agent명] - 기한: YYYY-MM-DD

### 후속 세션 추천 사항
- [추천 사항 1]
- [추천 사항 2]

---

## 8. 증거 및 로그

> **IDE 붙여넣기 주의**: 이 섹션의 코드 블록이나 백틱(`)을 IDE 채팅/프롬프트에 붙여넣을 때 포맷 이슈가 발생할 수 있습니다. 가능한 최소화하거나 평문으로 대체하세요.

### 실행 로그 경로
- `ops/run_records/log_YYYYMMDD_HHMMSS.log`
- `ops/run_records/session_YYYYMMDD.json`

### 스크린샷 또는 증거 자료
- `assets/screenshot_001.png` - [설명]
- `assets/evidence_data.csv` - [설명]

### 커맨드 히스토리
```bash
# 실행한 주요 명령어 기록
command 1
command 2
command 3
```

### 관련 커밋
- Commit ID: `abc123def456` - [커밋 메시지]
- Commit ID: `789ghi012jkl` - [커밋 메시지]

---

## 참고 사항

**Run Record 활용 지침**:
- Run Record는 증거이지 명령이 아닙니다
- Roadmap 업데이트는 제안 형태로 작성하고, 운영자가 최종 반영 여부 결정
- 실행 세부사항은 Run Record에 기록하고, Roadmap은 구조와 상태만 유지
- 의미 있는 작업 후에는 즉시 Run Record 생성 (Task/세션 완료 시뿐만 아니라)
