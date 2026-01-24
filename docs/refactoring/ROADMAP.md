# app/ 폴더 리팩토링 로드맵

## 문서 정보
- **생성일**: 2026-01-24
- **상태**: 계획 완료
- **예상 범위**: Python 파일 ~150개, 21개 모듈

---

## 목차
1. [프로젝트 개요](#프로젝트-개요)
2. [현재 상태 분석](#현재-상태-분석)
3. [리팩토링 Phase 요약](#리팩토링-phase-요약)
4. [Phase 별 상세](#phase-별-상세)
5. [의존성 다이어그램](#의존성-다이어그램)
6. [검증 체크리스트](#검증-체크리스트)

---

## 프로젝트 개요

### 목표
`app/` 폴더 내 중복 코드 및 파일들을 정리하고, 폴더 구조를 재정립하여 유지보수성을 향상시킵니다.

### 핵심 변경사항
1. **공유 유틸리티 추출**: 9개 이상 파일에서 중복되는 코드를 중앙화
2. **모듈 통합**: Retention, Backup 등 중복 모듈 통합
3. **베이스 클래스 추출**: Collector, Executor 패턴 추상화
4. **폴더 구조 재정립**: `app/obs_deploy/app/` → `app/observer/`
5. **테스트 재구성**: 소스와 분리된 테스트 폴더 구조

---

## 현재 상태 분석

### 구조적 문제
```
현재 구조 (문제점)
app/
└── obs_deploy/
    └── app/              ← "app" 중복 등장
        ├── observer.py
        ├── paths.py
        └── src/
            └── (21개 모듈)
```

### 식별된 중복 코드

| 카테고리 | 중복 패턴 | 영향 파일 수 | 우선순위 |
|----------|-----------|-------------|----------|
| 유틸리티 | ZoneInfo import 패턴 | 9+ | Critical |
| 유틸리티 | `_now()` 헬퍼 메서드 | 8 | Critical |
| 유틸리티 | `_safe_to_dict()`, `_fingerprint()` | 2 | Critical |
| 유틸리티 | `_in_trading_hours()` | 2 | Medium |
| 설정 | APP_ROOT/sys.path 설정 | 12 | High |
| 모듈 | Retention 모듈 중복 | 2 모듈 | High |
| 모듈 | Backup 모듈 중복 | 2 모듈 | High |
| 패턴 | Collector 클래스 중복 | 2 | High |
| 패턴 | Executor 클래스 중복 | 3 | Medium |

### 모듈 구조 (21개)
```
src/
├── auth/           # 인증 및 토큰 관리
├── automation/     # 자동화 스크립트 (비어있음)
├── backup/         # 백업 관리
├── collector/      # 데이터 수집기 (Track A/B)
├── db/             # 데이터베이스 마이그레이션
├── decision_pipeline/  # 의사결정 파이프라인
├── gap/            # 갭 감지
├── maintenance/    # 유지보수 작업
├── monitoring/     # 모니터링 대시보드
├── observer/       # 핵심 관찰 엔진 (최대 모듈)
├── optimize/       # 성능 최적화
├── provider/       # 데이터 제공자 (KIS)
├── retention/      # 데이터 보존 정책
├── runtime/        # 런타임 실행
├── safety/         # 안전 가드
├── shared/         # 공유 유틸리티
├── slot/           # 슬롯 관리
├── test/           # E2E 테스트
├── trigger/        # 트리거 엔진
└── universe/       # 유니버스 관리
```

---

## 리팩토링 Phase 요약

| Phase | 이름 | 우선순위 | 태스크 수 | 주요 작업 |
|-------|------|----------|----------|----------|
| 1 | 공유 유틸리티 추출 | Critical | 4 | timezone, time_helpers, trading_hours, serialization |
| 2 | 모듈 통합 | High | 3 | retention 통합, backup 통합, sys.path 제거 |
| 3 | 베이스 클래스 추출 | High | 2 | BaseCollector, BaseExecutor |
| 4 | 폴더 구조 재정립 | Medium | 2 | 구조 평탄화, 테스트 재구성 |
| 5 | 문서화 및 정리 | Low | 3 | 문서화, 폐기 파일 제거, 마이그레이션 가이드 |

---

## Phase 별 상세

### Phase 1: 공유 유틸리티 추출 (Critical)
중복 코드를 중앙화된 유틸리티 모듈로 추출합니다.

| 태스크 | 파일 | 설명 |
|--------|------|------|
| [TASK-1.1](phase-1/TASK-1.1-timezone-utility.md) | `src/shared/timezone.py` | ZoneInfo 래퍼 |
| [TASK-1.2](phase-1/TASK-1.2-time-helper-mixin.md) | `src/shared/time_helpers.py` | `_now()` 믹스인 |
| [TASK-1.3](phase-1/TASK-1.3-trading-hours.md) | `src/shared/trading_hours.py` | 거래시간 유틸리티 |
| [TASK-1.4](phase-1/TASK-1.4-serialization.md) | `src/shared/serialization.py` | 직렬화 유틸리티 |

### Phase 2: 모듈 통합 (High)
중복된 모듈을 통합하고 불필요한 패턴을 제거합니다.

| 태스크 | 설명 |
|--------|------|
| [TASK-2.1](phase-2/TASK-2.1-consolidate-retention.md) | Retention 모듈 통합 |
| [TASK-2.2](phase-2/TASK-2.2-consolidate-backup.md) | Backup 모듈 통합 |
| [TASK-2.3](phase-2/TASK-2.3-remove-syspath.md) | sys.path 패턴 제거 |

### Phase 3: 베이스 클래스 추출 (High)
공통 패턴을 추상 클래스로 추출합니다.

| 태스크 | 파일 | 설명 |
|--------|------|------|
| [TASK-3.1](phase-3/TASK-3.1-base-collector.md) | `src/collector/base.py` | BaseCollector 추상 클래스 |
| [TASK-3.2](phase-3/TASK-3.2-base-executor.md) | `src/decision_pipeline/execution_stub/base_executor.py` | BaseExecutor 추상 클래스 |

### Phase 4: 폴더 구조 재정립 (Medium)
폴더 구조를 개선하고 테스트를 재구성합니다.

| 태스크 | 설명 |
|--------|------|
| [TASK-4.1](phase-4/TASK-4.1-flatten-structure.md) | `app/obs_deploy/app/` → `app/observer/` 변경 |
| [TASK-4.2](phase-4/TASK-4.2-reorganize-tests.md) | 테스트 파일 `tests/` 폴더로 이동 |

### Phase 5: 문서화 및 정리 (Low)
문서를 작성하고 불필요한 파일을 정리합니다.

| 태스크 | 설명 |
|--------|------|
| [TASK-5.1](phase-5/TASK-5.1-documentation.md) | 모듈별 README 작성 |
| [TASK-5.2](phase-5/TASK-5.2-remove-deprecated.md) | 폐기 파일 제거 |
| [TASK-5.3](phase-5/TASK-5.3-migration-guide.md) | 마이그레이션 가이드 작성 |

---

## 의존성 다이어그램

```
Phase 1 (기반 작업)
├── TASK-1.1: timezone ─────────┐
├── TASK-1.3: trading_hours ────┼──→ TASK-1.2: time_helpers
└── TASK-1.4: serialization ────┘
                                │
                                ▼
Phase 2 (모듈 통합)
├── TASK-2.1: retention (requires Phase 1)
├── TASK-2.2: backup (requires Phase 1)
└── TASK-2.3: sys.path removal
                                │
                                ▼
Phase 3 (추상화)
├── TASK-3.1: BaseCollector (requires 1.x, 2.3)
└── TASK-3.2: BaseExecutor (requires 1.4)
                                │
                                ▼
Phase 4 (구조 변경)
├── TASK-4.1: folder restructure (requires Phase 1-3)
└── TASK-4.2: test reorganization (requires 4.1)
                                │
                                ▼
Phase 5 (마무리)
├── TASK-5.1: documentation
├── TASK-5.2: cleanup
└── TASK-5.3: migration guide
```

---

## 검증 체크리스트

### Phase 1 완료 조건
- [ ] 모든 테스트 통과
- [ ] `try: from zoneinfo` 패턴 0개
- [ ] `_now()` 중복 구현 0개
- [ ] `_safe_to_dict()` 중복 구현 0개
- [ ] 모든 import가 `from shared.x import y` 형태

### Phase 2 완료 조건
- [ ] 단일 `RetentionPolicy` 클래스
- [ ] 단일 `BackupManifest` 클래스
- [ ] `src/maintenance/retention/` 디렉토리 제거됨
- [ ] `src/maintenance/backup/` 디렉토리 제거됨
- [ ] `sys.path.append` 소스 파일에 없음

### Phase 3 완료 조건
- [ ] `BaseCollector` 클래스 존재
- [ ] `BaseExecutor` 클래스 존재
- [ ] TrackA/TrackB 컬렉터가 베이스 상속
- [ ] 모든 executor가 베이스 상속
- [ ] 코드 중복 40%+ 감소

### Phase 4 완료 조건
- [ ] `app/obs_deploy/app/` 중첩 구조 제거됨
- [ ] 모든 import 업데이트됨
- [ ] Docker 빌드 성공
- [ ] 모든 테스트가 `tests/` 디렉토리에 있음
- [ ] CI/CD 파이프라인 통과

### Phase 5 완료 조건
- [ ] 모듈별 README 존재
- [ ] 마이그레이션 가이드 발행
- [ ] 폐기 파일 제거됨
- [ ] 고아 import 없음

### 최종 검증
- [ ] 전체 테스트 스위트 통과
- [ ] Docker 이미지 빌드 성공
- [ ] 기존 기능 정상 동작 확인
- [ ] 코드 리뷰 완료

---

## 주요 파일 목록

### 신규 생성 파일
| 파일 | 설명 |
|------|------|
| `src/shared/timezone.py` | Timezone 유틸리티 |
| `src/shared/time_helpers.py` | Time helper 믹스인 |
| `src/shared/trading_hours.py` | 거래시간 유틸리티 |
| `src/shared/serialization.py` | 직렬화 유틸리티 |
| `src/collector/base.py` | BaseCollector 추상 클래스 |
| `src/decision_pipeline/execution_stub/base_executor.py` | BaseExecutor 추상 클래스 |

### 수정 대상 파일
| 파일 | 작업 |
|------|------|
| `src/retention/policy.py` | 통합 Policy 클래스 |
| `src/backup/manager.py` | 역할 분리 |
| `src/collector/track_a_collector.py` | BaseCollector 상속 |
| `src/collector/track_b_collector.py` | BaseCollector 상속 |
| `paths.py` | 구조 변경 반영 |

### 삭제 대상 파일
| 파일 | 이유 |
|------|------|
| `observer_backup_20260120_211722.py` | 백업 파일 |
| `src/maintenance/retention/` | 통합으로 불필요 |
| `src/maintenance/backup/` | 통합으로 불필요 |
