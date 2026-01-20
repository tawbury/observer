# Observer 아키텍처 TODO - 마스터 인덱스

**범위:** 아키텍처 문서 완료 전용 (구현/코딩 TODO 제외)  
**목표:** 모든 아키텍처 문서의 계약, 경계, 링크 정합성 확보  
**상태:** 진행 중

---

## 📋 Phase별 TODO 파일

| Phase | 파일명 | 목적 | 상태 |
|-------|--------|------|------|
| 00 | [todo_phase_00_foundation.md](docs/todo_phase_00_foundation.md) | 문서 구조/SSoT/링크 정책 확정 | 예정 |
| 01 | [todo_phase_01_anchor_contracts.md](docs/todo_phase_01_anchor_contracts.md) | 앵커 문서 완결 (프로젝트 정의/경계/모드) | 예정 |
| 02 | [todo_phase_02_paths_env_contracts.md](docs/todo_phase_02_paths_env_contracts.md) | 경로/환경변수/시크릿 계약 정합화 | 예정 |
| 03 | [todo_phase_03_archive_runner_arch.md](docs/todo_phase_03_archive_runner_arch.md) | Archive Runner 문서 완결 | 예정 |
| 04 | [todo_phase_04_trading_db_runner_arch_reserved.md](docs/todo_phase_04_trading_db_runner_arch_reserved.md) | Trading DB Runner 초안 확정 (보류) | 예정 |
| 05 | [todo_phase_05_deployment_automation_arch.md](docs/todo_phase_05_deployment_automation_arch.md) | Deployment Automation 문서 완결 | 예정 |
| 06 | [todo_phase_06_architecture_validation_review.md](docs/todo_phase_06_architecture_validation_review.md) | 아키텍처 최종 검증 및 DoD 통과 | 예정 |

---

## 🎯 글로벌 완료 체크리스트

아키텍처가 "완료"되기 위해 모든 항목이 참이어야 함:

- [ ] 모든 Phase TODO 파일이 생성되고 각각의 Acceptance Criteria 통과
- [ ] obs_anchor.md에서 obs_architecture.md로의 리다이렉트가 정상 작동
- [ ] 모든 아키텍처 문서가 docs/development/ 하위에 통합됨
- [ ] Phase 03-05 문서 간 링크가 모두 유효함 (깨진 링크 없음)
- [ ] 환경변수 명명 규칙이 모든 문서에서 일관됨 (QTS_OBSERVER_STANDALONE 표준)
- [ ] 실행 모드 용어가 collect/etl로 통일됨
- [ ] Archive/Trading DB/Deployment 각 SSoT 선언이 명확함
- [ ] Phase 04가 "Reserved" 상태로 명확히 표기됨
- [ ] 모든 문서의 버전 정보와 변경 이력이 최신 상태임

---

## ✅ Definition of Done (아키텍처 완료 기준)

아키텍처가 완료되었다고 선언하기 위한 최종 조건:

1. **문서 완결성:** 모든 Phase 문서가 각자의 목적에 맞게 완결된 내용을 포함
2. **링크 정합성:** 문서 간 모든 내부 링크가 유효하고 올바른 경로를 참조
3. **계약 일관성:** Archive/Trading DB/Deployment 계약이 문서 간 일관되게 정의
4. **SSoT 명확성:** 각 영역별 단일 진실 소스가 명확히 선언되고 참조됨
5. **경계 명시:** 프로젝트의 목적과 범위, 하지 않는 것이 명확히 구분됨
6. **용어 표준화:** 실행 모드, 환경변수, 기술 용어가 모든 문서에서 일관됨
7. **보류 명확화:** Phase 04 등 보류 항목이 명확한 상태와 이유로 표기됨
8. **검증 가능성:** 모든 TODO 항목이 구체적인 산출물과 검증 기준을 포함

---

**다음 단계:** Phase 00부터 순차적으로 진행하여 모든 체크리스트 완료 후 Phase 06에서 최종 검증 수행
