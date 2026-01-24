# app/ 폴더 리팩토링 계획

## 개요
app/ 폴더 내 중복 코드 및 파일들을 정리하고, 폴더 구조를 재정립하여 유지보수성을 향상시킵니다.

## 현재 상태 분석 결과

### 구조적 문제
- **중첩 구조**: `app/obs_deploy/app/` 패턴으로 "app"이 두 번 등장
- **총 파일 수**: Python 파일 ~150개, 21개 주요 모듈

### 식별된 중복 코드
| 중복 패턴 | 영향 파일 수 | 우선순위 |
|-----------|-------------|----------|
| ZoneInfo import 패턴 | 9+ 파일 | Critical |
| `_now()` 헬퍼 메서드 | 8 파일 | Critical |
| `_safe_to_dict()`, `_fingerprint()` | 2 파일 | Critical |
| `_in_trading_hours()` | 2 파일 | Medium |
| APP_ROOT/sys.path 설정 | 12 파일 | High |
| Retention 모듈 중복 | 2 모듈 | High |
| Backup 모듈 중복 | 2 모듈 | High |
| Collector 패턴 중복 | 2 파일 | High |

---

## 생성할 문서 구조

```
docs/
└── refactoring/
    ├── ROADMAP.md                    # 전체 로드맵
    ├── phase-1/
    │   ├── TASK-1.1-timezone-utility.md
    │   ├── TASK-1.2-time-helper-mixin.md
    │   ├── TASK-1.3-trading-hours.md
    │   └── TASK-1.4-serialization.md
    ├── phase-2/
    │   ├── TASK-2.1-consolidate-retention.md
    │   ├── TASK-2.2-consolidate-backup.md
    │   └── TASK-2.3-remove-syspath.md
    ├── phase-3/
    │   ├── TASK-3.1-base-collector.md
    │   └── TASK-3.2-base-executor.md
    ├── phase-4/
    │   ├── TASK-4.1-flatten-structure.md
    │   └── TASK-4.2-reorganize-tests.md
    └── phase-5/
        ├── TASK-5.1-documentation.md
        ├── TASK-5.2-remove-deprecated.md
        └── TASK-5.3-migration-guide.md
```

---

## Phase 1: 공유 유틸리티 추출 (Priority: Critical)

### 목표
중복 코드를 중앙화된 유틸리티 모듈로 추출

### Task 1.1: Timezone 유틸리티 생성
- **파일**: `src/shared/timezone.py`
- **대상 파일 (9개)**:
  - `src/auth/token_lifecycle_manager.py`
  - `src/collector/track_a_collector.py`
  - `src/collector/track_b_collector.py`
  - `src/gap/gap_detector.py`
  - `src/monitoring/prometheus_metrics.py`
  - `src/monitoring/grafana_dashboard.py`
  - `src/optimize/performance_profiler.py`
  - `src/observer/log_rotation_manager.py`
  - `src/universe/universe_scheduler.py`

### Task 1.2: Time Helper Mixin 생성
- **파일**: `src/shared/time_helpers.py`
- **대상 파일 (8개)**: `_now()` 메서드 중복 제거

### Task 1.3: Trading Hours 유틸리티
- **파일**: `src/shared/trading_hours.py`
- **대상 파일**: track_a_collector.py, track_b_collector.py

### Task 1.4: Serialization 유틸리티
- **파일**: `src/shared/serialization.py`
- **대상 파일**: sim_executor.py, virtual_executor.py

---

## Phase 2: 모듈 통합 (Priority: High)

### Task 2.1: Retention 모듈 통합
- **현재**: `src/retention/` + `src/maintenance/retention/`
- **목표**: 단일 `src/retention/` 모듈로 통합
- **통합 대상**: RetentionPolicy 클래스 (TTL + 카테고리 기반 지원)

### Task 2.2: Backup 모듈 통합
- **현재**: `src/backup/backup_manager.py` + `src/backup/manager.py` + `src/maintenance/backup/`
- **목표**: 역할별 분리 (manager.py, scheduler.py, plan.py)

### Task 2.3: sys.path 패턴 제거
- **대상**: 12개 파일의 `sys.path.append(APP_ROOT)` 제거
- **해결책**: 패키지 설정 개선 및 상대 import 사용

---

## Phase 3: 베이스 클래스 추출 (Priority: High)

### Task 3.1: BaseCollector 추상 클래스
- **파일**: `src/collector/base.py`
- **공유 패턴**: `_now()`, `_in_trading_hours()`, 에러 콜백, async 루프

### Task 3.2: BaseExecutor 추상 클래스
- **파일**: `src/decision_pipeline/execution_stub/base_executor.py`
- **공유 패턴**: 직렬화, 핑거프린트, decision ID 추출

---

## Phase 4: 폴더 구조 재정립 (Priority: Medium)

### Task 4.1: 폴더 구조 재정립 (Option B 선택됨)
**현재**: `app/obs_deploy/app/src/...`
**목표**: `app/observer/src/...` (이름 명확화)

**마이그레이션 단계**:
1. `app/observer/` 디렉토리 생성
2. `app/obs_deploy/app/` 내용물 이동
3. 모든 import 경로 업데이트
4. Docker 설정 업데이트
5. 배포 스크립트 업데이트
6. 기존 구조 제거

### Task 4.2: 테스트 파일 재구성
**현재**: 소스 코드와 혼재
**목표**:
```
tests/
├── unit/
├── integration/
└── local/
```

---

## Phase 5: 문서화 및 정리 (Priority: Low)

### Task 5.1: 모듈 문서화
### Task 5.2: 폐기 파일 제거
- `observer_backup_20260120_211722.py`
- 빈 유틸리티 파일들

### Task 5.3: 마이그레이션 가이드 작성

---

## 구현 순서 및 의존성

```
Phase 1 (기반) ──────────────────────────────────────┐
  1.1 timezone ──┬──> 1.2 time_helpers               │
  1.3 trading   ─┤                                   │
  1.4 serialize ─┘                                   │
                                                     ▼
Phase 2 (통합) ──────────────────────────────────────┐
  2.1 retention (depends on 1.x)                     │
  2.2 backup (depends on 1.x)                        │
  2.3 sys.path removal                               │
                                                     ▼
Phase 3 (추상화) ────────────────────────────────────┐
  3.1 BaseCollector (depends on 1.x, 2.3)            │
  3.2 BaseExecutor (depends on 1.4)                  │
                                                     ▼
Phase 4 (구조) ──────────────────────────────────────┐
  4.1 flatten structure (depends on 1-3)             │
  4.2 reorganize tests (depends on 4.1)              │
                                                     ▼
Phase 5 (문서) ──────────────────────────────────────┘
  5.1, 5.2, 5.3 (depends on 1-4)
```

---

## 검증 방법

### Phase별 검증
1. **Phase 1**: 모든 테스트 통과, 중복 패턴 0개
2. **Phase 2**: 단일 Policy/Manifest 클래스, maintenance 하위 모듈 제거
3. **Phase 3**: Base 클래스 상속 확인, 코드 중복 40%+ 감소
4. **Phase 4**: Docker 빌드 성공, CI/CD 통과
5. **Phase 5**: 문서 완성, 폐기 파일 제거

### 최종 검증
- [ ] 전체 테스트 스위트 통과
- [ ] Docker 이미지 빌드 성공
- [ ] 기존 기능 동작 확인

---

## 수정 대상 주요 파일

| 파일 경로 | 작업 내용 |
|-----------|----------|
| `src/shared/utils.py` | 유틸리티 허브로 확장 |
| `src/shared/timezone.py` | 신규 생성 |
| `src/shared/time_helpers.py` | 신규 생성 |
| `src/shared/trading_hours.py` | 신규 생성 |
| `src/shared/serialization.py` | 신규 생성 |
| `src/retention/policy.py` | 통합 Policy 클래스 |
| `src/backup/manager.py` | 역할 분리 |
| `src/collector/base.py` | 신규 생성 |
| `src/decision_pipeline/execution_stub/base_executor.py` | 신규 생성 |
| `paths.py` | 구조 변경 시 업데이트 |
