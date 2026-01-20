# Observer TODO 가이드

**버전:** v1.0  
**목적:** 아키텍처 기반의 단계별 개발 가이드  
**SSoT:** 아키텍처 문서 기반 TODO 생성

---

## 사용 방법

### 전역 규칙

#### 체크박스 스타일
- 모든 작업은 Obsidian 스타일 체크박스 사용: `- [ ] 작업 내용`
- 상태 태그: `[WIP]`, `[BLOCKED]`, `[REVIEW]` 등 추가 가능
- 완료 시: `- [x] 작업 내용`

#### 완료 정의 (Definition of Done)
- **코드 기반:** 테스트 통과, 코드 리뷰 완료
- **문서 기반:** SSoT 문서와 일치, 계약 준수 검증
- **운영 기반:** 실제 환경에서 정상 동작 확인

#### 작성 원칙
- 각 작업은 실행 가능하고 구체적이어야 함
- "안정성 개선" 같은 모호한 표현 금지
- SSoT 문서에 없는 내용은 추정하지 말고 "확인..." 작업으로 기술

---

## Phase 목록

### 실행 순서 (권장)
1. **[Phase 01: Foundation](phase_01_foundation.md)** - 기반 구축
2. **[Phase 02: KIS Integration](phase_02_kis_integration.md)** - KIS 연동
3. **[Phase 03: Archive Stabilization](phase_03_archive_stabilization.md)** - 아카이브 안정화 (최우선)
4. **[Phase 04: Trading DB Runner](phase_04_trading_db_runner_reserved.md)** - ETL (예약)
5. **[Phase 05: Deployment Automation](phase_05_deployment_automation.md)** - 배포 자동화

### 우선순위
- **즉시:** Phase 01-03 (로그 생성 안정화)
- **보류:** Phase 04 (Phase 03 완료 후)
- **병행:** Phase 05 (인프라 팀)

---

## SSoT 문서 목록

### 기준 문서 (단일 진실 소스)
1. **[obs_architecture.md](../development/obs_architecture.md)** - 전체 아키텍처
2. **[phase_03_archive_runner.md](../development/phase_03_archive_runner.md)** - 아카이브 SSoT
3. **[deployment_automation.md](../development/deployment_automation.md)** - 배포 SSoT
4. **[phase_04_trading_db_runner.md](../development/phase_04_trading_db_runner.md)** - ETL SSoT (예약)

### 참고 문서
- **[obs_analysis_report.md](../development/obs_analysis_report.md)** - 코드 분석 리포트
- **[Dynamic_Polling_Engine_Design.md](../development/Dynamic_Polling_Engine_Design.md)** - 폴링 엔진 설계

---

## 작업 추적

### 진행 상태
- 각 Phase 문서의 Done Criteria를 기준으로 진행률 측정
- 크로스 Phase 의존성은 명시적으로 관리

### 리뷰 프로세스
- Phase 완료 시 SSoT 문서 업데이트
- 다음 Phase 시작 전 선수 조건 확인

---

**주의:** 이 TODO는 SSoT 문서에서 추출된 작업만 포함합니다. 새로운 요구사항은 먼저 SSoT 문서에 반영 후 TODO에 추가하세요.
