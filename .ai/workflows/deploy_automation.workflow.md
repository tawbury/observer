# Meta
- Workflow Name: Server Deployment Automation
- File Name: deploy_automation.workflow.md
- Document ID: WF-DEPLOY-001
- Status: Active
- Created Date: 2026-01-22
- Last Updated: 2026-01-22
- Author: {{USER}}
- Reviewer: {{REVIEWER}}
- Parent Document: [[workflow_base.md]]
- Related Reference: [[anchor_template.md]], [[roadmap_template.md]], [[task_template.md]], [[run_record_template.md]]
- Version: 1.0.0

---

# 서버 배포 자동화 워크플로우

## Purpose
서버 배포 자동화 프로세스를 체계적으로 관리하며, 지속적인 운영 루프를 유지: Roadmap → Task → Run Record → Roadmap.

## Workflow Goal
운영 루프 연속성을 유지하여 보장:
- 모든 작업은 메타데이터 연결 문서를 통해 추적 가능
- 세션 중단이 워크플로우 연속성을 방해하지 않음
- IDE AI는 언제든지 저장소 상태에서 작업 재개 가능
- Run Records가 다음 Roadmap/세션 선택 가능

## Base Workflow
이 워크플로우는 다음을 확장: [[workflow_base.md]]
상속: L1/L2 정의, 표준 1-4단계, 제약 조건 카테고리, 운영 루프

---

## Workflow Overview
로컬 개발 환경에서 서버 배포까지의 전체 자동화 프로세스. 이 워크플로우는 배포 자동화에 특화되며, 코드 수정은 오직 로컬 환경에서만 수행됩니다. 서버는 검증된 패키지 교체만을 위한 실행 환경입니다.

**운영 루프 통합**:
- 이 워크플로우는 표준 루프 내에서 운영: Anchor → Decision → Roadmap → Session → Task → Run Record
- Roadmap 항목은 3가지 상태로 단계/세션 구조 추적: Work Not Started, In Progress, Done
- Task는 Roadmap 항목에 메타데이터로 연결된 최소 실행 단위
- Run Records는 의미 있는 작업 후 루프 종료

### Deployment Scripts
- [scripts/deploy/deploy.ps1](scripts/deploy/deploy.ps1): 기본 전체 배포 스크립트 (env 검증/업로드, 아티팩트 업로드, server_deploy.sh 실행, 헬스 체크 포함). `-EnvOnly` 스위치로 env 업데이트만 수행 가능 (아티팩트/배포 단계 스킵).
- [scripts/deploy/deploy_simple.ps1](scripts/deploy/deploy_simple.ps1): 호환성 래퍼. 내부적으로 deploy.ps1 `-EnvOnly`를 호출하여 빠른 환경 변수 업데이트만 실행.
- EnvOnly 예시:
```
powershell -File scripts\deploy\deploy.ps1 -ServerHost "<host>" -SshUser "<user>" -SshKeyPath "<path_to_key>" -DeployDir "/home/azureuser/observer-deploy" -LocalEnvFile "app\obs_deploy\.env.server" -EnvOnly
```

---

## Workflow Stages

### 1. Planning/Strategy (상속)
- **Responsible**: PM Agent + Developer Agent
- **Input**: 배포 요구사항, 비즈니스 목표
- **Output**: 배포 전략 문서
- **Template**: [[prd_template.md]]
- **Deliverable**: docs/dev/PRD/prd_deploy_<project>.md (예시)
- **Metadata Links**: Parent Document must reference Roadmap or Anchor
- **Note**: workflow_base.md에서 상속된 표준 단계

### 2. Design/Architecture (상속)
- **Responsible**: Developer Agent
- **Input**: 배포 전략 문서
- **Output**: 배포 아키텍처 설계
- **Template**: [[architecture_template.md]]
- **Deliverable**: docs/dev/archi/deploy_architecture_<project>.md (예시)
- **Metadata Links**: Parent Document must reference Roadmap or prior stage output
- **Note**: workflow_base.md에서 상속된 표준 단계

### 3. Specification (상속)
- **Responsible**: Developer Agent
- **Input**: 배포 아키텍처, 요구사항
- **Output**: 배포 명세서
- **Template**: [[spec_template.md]]
- **Deliverable**: docs/dev/spec/deploy_spec_<module>.md (예시)
- **Metadata Links**: Parent Document must reference Roadmap or prior stage output
- **Note**: workflow_base.md에서 상속된 표준 단계

### 4. Decision Making (상속)
- **Responsible**: Developer Agent + PM Agent
- **Input**: 배포 명세, 제약 조건
- **Output**: 배포 결정 기록
- **Template**: [[decision_template.md]]
- **Deliverable**: docs/decisions/decision_deploy_<date>.md (예시)
- **Metadata Links**: Parent Document must reference Roadmap or prior stage output
- **Note**: workflow_base.md에서 상속된 표준 단계

### 5. Local Development & Primary Testing
- **Responsible**: Developer Agent
- **Input**: 배포 명세, 결정 기록
- **Output**: 로컬 테스트 완료 보고서
- **Template**: [[run_record_template.md]]
- **Deliverable**: ops/run_records/local_test_<date>_<session>.md
- **Metadata Links**: Parent Document must reference Roadmap or prior stage output
- **Domain-Specific Activities**:
  - 로컬 개발 환경에서 코드 구현 및 수정
  - 단위 테스트 및 통합 테스트 수행
  - Docker 이미지 빌드 준비
  - 모든 코드 수정은 로컬 환경에서만 수행

### 6. Container Build & Rehearsal Testing
- **Responsible**: Developer Agent
- **Input**: 로컬 테스트 완료 코드
- **Output**: 컨테이너 이미지, 리허설 테스트 결과
- **Template**: [[run_record_template.md]]
- **Deliverable**: ops/run_records/container_test_<date>_<session>.md
- **Metadata Links**: Parent Document must reference Roadmap or prior stage output
- **Domain-Specific Activities**:
  - Docker 이미지 빌드 (타임스탬프 태그 포함)
  - 컨테이너 기반 리허설 테스트 환경 구성
  - 배포 전 최종 검증 수행
  - 검증된 이미지를 서버에서 사용 가능 상태로 준비한다. (배포 채널: 레지스트리 pull / 이미지 tar 전달 등은 환경에 따라 선택; 본 문서는 방법을 고정하지 않는다.)
  - Exit Criteria: 선택된 이미지/버전 식별자(tag) 기록, 해당 식별자에 맞춰 전달 채널 준비 완료, 서버가 동일 이미지를 확보하거나 즉시 로드 가능함을 최소 확인

※ Image Availability Contract: 서버가 선택된 전달 채널을 통해 동일 이미지에 접근 가능함이 확인되어야 Stage 7로 진행 가능.

### 7. Server Deployment & Runtime Validation
- **Responsible**: Developer Agent + Ops Agent
- **Input**: 검증된 컨테이너 이미지
- **Output**: 배포 완료 보고서, 운영 상태 검증
- **Template**: [[run_record_template.md]]
- **Deliverable**: ops/run_records/deploy_<date>_<session>.md
- **Metadata Links**: Parent Document must reference Roadmap or prior stage output
- **Domain-Specific Activities**:
  - 서버 배포 실행 (compose/run 정의 사용)
  - 런타임 상태 검증 (컨테이너 상태, 헬스 체크)
  - 운영 메트릭 자동 확인 (Stage 1)
  - 문제 발생 시 로컬 수정 루프로 복귀

---

## Go/No-Go Release Criteria

### 자동화된 운영 메트릭 확인 (Stage 1)
- **컨테이너 상태**: 모든 컨테이너 실행 중 (100%)
- **헬스 체크**: 모든 서비스 헬스 엔드포인트 정상 (100%)
- **에러 로그**: 치명적 에러 없음 (0개)
- **리소스 사용**: CPU/메모리 사용량 임계치 내
- **네트워크 연결**: 외부 서비스 연결 정상

### 수동 확인 (선택적)
- **기능 검증**: 핵심 기능 동작 확인
- **성능 테스트**: 응답 시간 및 처리량 확인
- **보안 검토**: 보안 설정 및 접근 제어 확인

### 코어 시나리오 자동화 로드맵 (Stage 2)
- **데이터 캡처 → 파일 생성 → 로테이션** 시나리오 자동화
- **API 엔드포인트** 통합 테스트 자동화
- **데이터 무결성 검증** 자동화
- **안정화 후 Stage 2 구현 계획**

---

## Server Modification Prohibition

### 엄격한 금지 규칙
- **서버에서 코드 수정 절대 금지**: 모든 코드 수정은 로컬 환경에서만 수행
- **compose/run 정의 직접 편집 금지**: 서버에서는 읽기 전용 취급
- **설정 파일 직접 수정 금지**: 배포 프로세스를 통해서만 업데이트
- **소스 코드 직접 변경 금지**: 검증된 패키지로만 교체 가능

### 운영적 집행 가능성
- **배포 프로세스 통한 업데이트**: 로컬에서 빌드된 이미지로만 교체
- **환경 변수 값 안전 업데이트**: 값만 변경, 구조는 템플릿 제어
- **롤백 명령 실행**: 이전 버전으로 되돌리기 가능
- **로그 및 모니터링**: 운영 상태 확인 및 기록

---

## Writable Areas Policy

### 쓰기 가능 영역 (초기 넓은 허용 목록)
- **logs/**: 애플리케이션 및 시스템 로그
- **archives/data/**: 데이터 아카이브 및 백업
- **runtime/state/**: 런타임 상태 정보
- **temp/**: 임시 파일 (주기적 정리, 선택적)
- **uploads/**: 사용자 업로드 파일 (필요시 선택적)

### 쓰기 금지 영역
- **소스 코드 디렉토리**: 모든 코드 파일 읽기 전용
- **설정 파일**: env.template 및 compose/run 정의 읽기 전용
- **바이너리/실행 파일**: 배포된 패키지 읽기 전용
- **라이브러리 디렉토리**: 의존성 읽기 전용
- **추가 원칙**: 위 허용 영역 외 코드/구성/compose는 불변으로 취급하고, 교체가 필요하면 배포 절차를 통해서만 반영 (서버 현장 편집 금지)

### 향후 강화 단계
- **안정화 후 최소 권한 원칙 적용**
- **필수 쓰기 영역만 허용으로 제한**
- **파일 시스템 감사 및 접근 제어 강화**

---

## Environment Handling Policy

### 환경 변수 관리
- **Local**: .env 파일 (gitignored, 실제 값 포함)
- **Repository/Image**: env.template만 포함 (구조 및 필수 키 정의)
- **Server**: 실제 .env 파일 (운영 환경 값)
- **Template Control**: 템플릿이 필수 키/구조 제어
- **Server Updates**: 값만 안전하게 업데이트, 구조는 템플릿 따름
- **Ownership**: 환경 값 SSoT은 로컬 .env이며 서버 .env는 배포 스크립트/워크플로우를 통해서만 갱신 (서버 직접 편집 금지)

### 런타임 전용 주입 (향후 업그레이드 경로)
- **현재**: 구현하지 않음 (선택적)
- **향후**: 런타임 시점에만 환경 변수 주입 기능 고려
- **보안 고려사항**: 민감 정보 노출 방지, 감사 추적 유지

---

## Rollback Strategy

### 롤백 전략
- **이미지 태깅**: YYYYMMDD_HHMMSS 형식
- **롤백 명령**: 이전 안정 태그로 되돌리기 (수동)
- **향후 자동 롤백**: 메트릭 임계치 초과 시 자동 복귀 (향후 업그레이드 경로)
- **롤백 기록**: 모든 롤백 작업 Run Record에 기록
- **Tag SSoT**: 롤백 대상은 태그(또는 동등 버전 식별자)를 단일 SSoT로 삼아 선택하며, 해당 식별자로 이미지/패키지를 지정

### 데이터/스키마 변경 가정
- **가정**: 데이터/스키마 변경은 거의 없음
- **보호 조치**: 드문 파괴적 변경에 대한 가드레일 노트
- **호환성**: 이전 버전과의 호환성 유지
- **마이그레이션**: 필요시 자동 마이그레이션 스크립트 준비

---

## Decision Log / Audit Trail

### 저장소 기반 배포 기록
- **GitHub 연결**: 모든 배포 기록 저장소에 기록
- **Run Record 연동**: 배포 작업은 Run Record로 기록
- **메타데이터 추적**: 배포 버전, 태그, 결정 사항 메타데이터에 기록
- **시간순 기록**: 모든 배포 활동 시간순으로 추적 가능

### 서버 상태 최소화
- **last_good_tag**: 마지막 안정 버전 태그만 서버에 저장 (필요시)
- **시크릿 보호**: 로그나 기록에 시크릿 정보 노출 금지
- **상태 정리**: 불필요한 상태 정보 주기적 정리
- **감사 추적**: 모든 변경 사항 추적 가능성 유지

---

## Local Fix Loop

### 문제 해결 프로세스
1. **문제 감지**: 런타임 검증 또는 모니터링에서 문제 발견
2. **서버 롤백**: 이전 안정 버전으로 즉시 복귀
3. **로컬 수정**: 로컬 환경에서 문제 원인 분석 및 수정
4. **재테스트**: 로컬 및 컨테이너 리허설 테스트 재수행
5. **재배포**: 수정된 버전으로 서버 재배포
6. **안정화 확인**: 운영 메트릭 안정화 확인
7. **루프 종료**: 안정화되면 정상 운영 전환

### 루프 탈출 조건
- **운영 메트릭 안정화**: 모든 자동화된 확인 통과
- **수동 검증 통과**: 선택적 수동 검증 완료
- **기간 안정화**: 최소 안정화 기간 달성 (프로덕션 기본 24시간, 테스트 환경은 더 짧은 기간 설정 가능)

---

## Related Documents

### Templates
- [[prd_template.md]] - Stage 1 Planning
- [[architecture_template.md]] - Stage 2 Design
- [[spec_template.md]] - Stage 3 Specification
- [[decision_template.md]] - Stage 4 Decision
- [[task_template.md]] - Task creation
- [[roadmap_template.md]] - Roadmap structure (operational loop driver)
- [[run_record_template.md]] - Run Record format (execution evidence)
- [[report_template.md]] - Final reporting

### Operational Loop Integration Note
**Workflow와 Roadmap/Run Record 연계**:
- 이 Workflow 문서는 배포 자동화 단계와 역할을 정의합니다
- 실제 실행 추적은 [[roadmap_template.md]]와 [[run_record_template.md]]를 사용합니다
- Workflow Meta의 Related Reference에 활성 Roadmap과 주요 Run Records를 링크하세요
- Roadmap은 Workflow 단계를 phase/session으로 구체화하고, Run Records는 실행 증거를 제공합니다

### Agents
- [[developer.agent.md]] - Development and deployment agent
- [[pm.agent.md]] - Planning and strategy agent

### Skills
- .ai/skills/developer/ - Development and deployment related skills
- .ai/skills/_shared/ - Shared frameworks (optimization, analytics)

### Validators
- [[meta_validator.md]] - Metadata validation
- [[structure_validator.md]] - Document structure validation
- [[deployment_validator.md]] - Deployment process validation (if exists)

---

## Constraint Conditions

### 1. Quality Standards
- 모든 산출물은 템플릿을 준수해야 함
- 품질 임계치를 충족해야 함
- 검토 프로세스를 따라야 함
- 모든 워크플로우 아티팩트에 메타데이터 연결 필수

### 2. Server Immutability
- 서버에서 코드 수정 절대 금지
- 설정 파일 직접 편집 금지
- 검증된 패키지로만 교체 가능
- 쓰기 가능 영역 엄격히 제한

### 3. Security Requirements
- 시크릿 정보 노출 방지
- 환경 변수 안전 관리
- 감사 추적 유지
- 접근 제어 준수

### 4. Deployment Safety
- 롤백 항상 가능해야 함
- 타임스탬프 기반 버전 관리
- 자동화된 검증 통과 후 배포
- 문제 발생 시 즉시 복귀 절차

### 5. Performance Requirements
- 운영 메트릭 자동 검증 통과
- 성능 기준 충족
- 안정화 기간 준수

---

## Success Indicators

### 1. Deployment Success
- 자동화된 운영 메트릭 통과율: 100% 목표
- 롤백 발생률: 5% 미만 목표
- 배포 시간 준수: 목표 시간 내
- 안정화 기간 달성: 24시간 내 안정화

### 2. Operational Continuity
- 세션 중단이 워크플로우 연속성을 방해하지 않음: 100% 목표
- 저장소 상태에서 모든 작업 재개 가능: 100% 목표
- 메타데이터 연결 완전하고 정확함: 100% 목표

### 3. Quality Metrics
- 템플릿 준수: 100% 목표
- 통과율: 95%+ 목표
- 보안 준수: 100% 목표

### 4. Efficiency Metrics
- 배포 주기 준수: 목표 준수
- 자동화율: 90%+ 목표
- 롤백 시간: 10분 내 목표

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-22 | 초기 배포 자동화 워크플로우 생성 |
