# Observer 독립화 리팩토링 상세 가이드

**작업 완료**: 2026-01-20 21:45
**커밋**: 7de2d5e
**원본 커밋**: 5ebac87 (FastAPI 통합)

---

## 🎯 리팩토링 목표

QTS 프로젝트의 특화된 모듈로서의 Observer에서 독립적인 마이크로서비스로 전환:

1. ✅ 환경 변수 정규화 (QTS_* → OBSERVER_*)
2. ✅ 문서 및 코드 현대화 (영문 표준화)
3. ✅ 독립 배포 가능성 확보
4. ✅ 기존 기능 유지 (호환성)

---

## 📋 변경 상세 기록

### File 1: `app/obs_deploy/app/paths.py`

**목적**: 프로젝트 경로 리졸버를 Observer 독립 배포에 맞게 개선

**변경 사항**:

#### 1.1 모듈 문서 갱신

```python
# BEFORE
"""
paths.py

QTS project-wide canonical path resolver.

This module defines the single source of truth for all filesystem paths
used across the QTS project, including:
- execution (main.py)
- observer / ops modules
- pytest
- local scripts

Design principles:
- Resilient to folder restructuring
- No relative depth assumptions (no parents[n])
- Project-level, not package-level

Phase F update:
- Observer-generated JSON / JSONL files are treated as CONFIG ASSETS.
- data/ directory is reserved for ephemeral runtime-only artifacts.
- Observer assets MUST be resolved via observer_asset_dir().
"""

# AFTER
"""
paths.py

Observer project-wide canonical path resolver.

This module defines the single source of truth for all filesystem paths
used across the Observer project, including:
- execution (observer.py)
- observer / runtime modules
- pytest
- local scripts

Design principles:
- Resilient to folder restructuring
- No relative depth assumptions (no parents[n])
- Project-level, not package-level

Path Management Strategy:
- Observer-generated JSON / JSONL files are treated as CONFIG ASSETS.
- data/ directory is reserved for ephemeral runtime-only artifacts.
- Observer assets MUST be resolved via observer_asset_dir().
- Supports standalone Docker deployment with /app as project root.
"""
```

**이유**:
- QTS 프로젝트 맥락 제거
- Observer 독립 배포 명시
- Phase 용어 제거 (전술적 명확성)

#### 1.2 프로젝트 리졸버 함수 업데이트

```python
# BEFORE
def _resolve_project_root(start: Optional[Path] = None) -> Path:
    """
    Resolve QTS project root directory.
    ...
    """
    # 1️⃣ Observer standalone mode (explicit opt-in)
    if os.environ.get("QTS_OBSERVER_STANDALONE") == "1":
        return Path(__file__).resolve().parent

    # 2️⃣ Normal QTS project resolution
    ...
    raise RuntimeError("QTS project root could not be resolved")

# AFTER
def _resolve_project_root(start: Optional[Path] = None) -> Path:
    """
    Resolve Observer project root directory.
    ...
    """
    # 1️⃣ Observer standalone mode (explicit opt-in)
    if os.environ.get("OBSERVER_STANDALONE") == "1":
        return Path(__file__).resolve().parent

    # 2️⃣ Normal Observer project resolution
    ...
    raise RuntimeError("Observer project root could not be resolved")
```

**변경점**:
- `QTS_OBSERVER_STANDALONE` → `OBSERVER_STANDALONE`
- "QTS project" → "Observer project"

#### 1.3 프로젝트 루트 함수 설명

```python
# BEFORE
def project_root() -> Path:
    """QTS project root directory"""
    return _resolve_project_root()

# AFTER
def project_root() -> Path:
    """Observer project root directory"""
    return _resolve_project_root()
```

#### 1.4 데이터 디렉토리 정책 갱신

```python
# BEFORE
def data_dir() -> Path:
    """
    Canonical data root directory.

    Phase F:
    - This directory is reserved for ephemeral / runtime-only artifacts.
    ...
    """

# AFTER
def data_dir() -> Path:
    """
    Canonical data root directory.

    Policy:
    - This directory is reserved for ephemeral / runtime-only artifacts.
    ...
    """
```

**이유**: "Phase F" 용어를 더 명확한 "Policy"로 대체

#### 1.5 설정 디렉토리 정책 갱신

```python
# BEFORE
def config_dir() -> Path:
    """
    Canonical config root directory.

    Phase F:
    - Long-lived operational assets live here.
    """

# AFTER
def config_dir() -> Path:
    """
    Canonical config root directory.

    Policy:
    - Long-lived operational assets live here.
    """
```

#### 1.6 Observer 자산 디렉토리 정의 정규화

```python
# BEFORE
def observer_asset_dir() -> Path:
    """
    Canonical Observer ASSET directory (Phase F).
    ...
    """

# AFTER
def observer_asset_dir() -> Path:
    """
    Canonical Observer ASSET directory.
    ...
    """
```

#### 1.7 레거시 함수 경고 메시지 간소화

```python
# BEFORE
def observer_data_dir() -> Path:
    """
    DEPRECATED since Phase F.
    ...
    """
    logger.warning(
        "observer_data_dir() is deprecated since Phase F. "
        "Use observer_asset_dir() instead."
    )

# AFTER
def observer_data_dir() -> Path:
    """
    DEPRECATED.
    ...
    """
    logger.warning(
        "observer_data_dir() is deprecated. "
        "Use observer_asset_dir() instead."
    )
```

---

### File 2: `app/obs_deploy/app/observer.py` (Docker Entry Point)

**목적**: Docker 진입점을 독립 배포 시스템으로 명확히

**변경 사항**:

#### 2.1 모듈 문서 개선

```python
# BEFORE
"""
Observer Docker Entry Point
Observer system with FastAPI server for monitoring and control
"""

# AFTER
"""
Observer Docker Entry Point

Standalone Observer system with FastAPI server for monitoring and control.
This is the main entry point for Docker container deployment.
"""
```

#### 2.2 환경 설정 함수 강화

```python
# BEFORE
def configure_environment():
    """Configure environment variables for Docker deployment"""
    os.environ.setdefault("OBSERVER_STANDALONE", "1")
    os.environ.setdefault("PYTHONPATH", "/app/src:/app")
    os.environ.setdefault("OBSERVER_DATA_DIR", "/app/data/observer")
    os.environ.setdefault("OBSERVER_LOG_DIR", "/app/logs")

# AFTER
def configure_environment():
    """Configure environment variables for Docker deployment"""
    os.environ.setdefault("OBSERVER_STANDALONE", "1")
    os.environ.setdefault("PYTHONPATH", "/app/src:/app")
    os.environ.setdefault("OBSERVER_DATA_DIR", "/app/data/observer")
    os.environ.setdefault("OBSERVER_LOG_DIR", "/app/logs")
    # For backward compatibility with deployment paths module
    os.environ.setdefault("OBSERVER_DEPLOYMENT_MODE", "docker")
```

**이유**: 배포 경로 모듈과의 호환성 강화

---

### File 3: `app/obs_deploy/app/src/observer/observer.py` (Core)

**목적**: 핵심 오케스트레이터 클래스 문서를 Observer 독립 버전으로 정규화

**변경 사항**:

#### 3.1 모듈 문서 번역 및 정규화

```python
# BEFORE
"""
observer.py

QTS-Observer-Core의 메인 오케스트레이터(중앙 제어 클래스)

현재 구현:
- Validation Layer: 데이터 유효성 검증
- Guard Layer: 안전 장치 및 제약 조건 검사
- PatternRecord Enrichment: 기록 보강
  - Schema Auto Lite (record schema versioning + namespace)
  - Quality Tagging
  - Interpretation Metadata

원칙:
- 전략 계산, 매매 판단, 실행은 절대 여기서 하지 않는다.
- Snapshot을 받아 → Validation → Guard → Record → Enrich → EventBus 로 전달한다.
"""

# AFTER
"""
observer.py

Observer Core - Main Orchestrator (Central Control Class)

Current Implementation:
- Validation Layer: Data validity validation
- Guard Layer: Safety constraints and guards
- PatternRecord Enrichment: Record enrichment
  - Schema Auto Lite (record schema versioning + namespace)
  - Quality Tagging
  - Interpretation Metadata

Principles:
- Strategy calculation, trading decisions, execution are NEVER done here
- Receives Snapshot → Validation → Guard → Record → Enrich → EventBus dispatch
"""
```

**변경점**:
- "QTS-Observer-Core" → "Observer Core"
- 모든 한글 주석 영문 정규화
- 기술적 명확성 향상

#### 3.2 클래스 문서 업데이트

```python
# BEFORE
class Observer:
    """
    QTS-Observer-Core Orchestrator

    역할:
    - ObservationSnapshot 수신
    - Validation → Guard
    - PatternRecord 생성
    - Record Enrichment (메타데이터 보강)
    - EventBus dispatch

    절대 하지 않는 것:
    - 매수/매도 판단
    - 전략 계산
    - 주문 실행
    """

# AFTER
class Observer:
    """
    Observer Core Orchestrator

    Responsibilities:
    - Receives ObservationSnapshot
    - Validation → Guard
    - Creates PatternRecord
    - Record Enrichment (metadata enrichment)
    - EventBus dispatch

    Never does:
    - Buy/sell decisions
    - Strategy calculations
    - Order execution
    """
```

---

### File 4: `app/obs_deploy/app/src/observer/snapshot.py`

**목적**: 관측 데이터 계약 단위 문서 정규화

**변경 사항**:

```python
# BEFORE
@dataclass(frozen=True)
class ObservationSnapshot:
    """
    QTS-Observer-Core 최소 관측 단위
    - Contract v1.0.0 준수 (Phase 2 기준)
    """

# AFTER
@dataclass(frozen=True)
class ObservationSnapshot:
    """
    Observer Core - Minimal Observation Unit (Contract v1.0.0)

    This is the atomic unit of observation data passed through the system.
    """
```

---

### File 5: `app/obs_deploy/app/src/observer/deployment_paths.py`

**목적**: 배포 환경 감지를 Observer 정규화 환경 변수 사용

**변경 사항**:

```python
# BEFORE
def is_deployment_environment() -> bool:
    """Check if running in deployment environment."""
    return (
        os.environ.get("QTS_OBSERVER_STANDALONE") == "1" or
        DEPLOYMENT_ROOT.exists()
    )

# AFTER
def is_deployment_environment() -> bool:
    """Check if running in deployment environment."""
    return (
        os.environ.get("OBSERVER_STANDALONE") == "1" or
        DEPLOYMENT_ROOT.exists()
    )
```

---

### File 6: `app/obs_deploy/app/src/runtime/phase15_runner.py`

**목적**: 라이브 실행 승인 환경 변수 정규화

**변경 사항**:

```python
# BEFORE
def _log_execution_mode_context() -> None:
    """
    Phase 15 does NOT execute trades.
    This function exists to align runner structure with Phase E.
    """
    sheet_mode = os.getenv("EXECUTION_MODE")
    sheet_live_enabled = os.getenv("LIVE_ENABLED")
    env_ack = os.getenv("QTS_LIVE_ACK")

# AFTER
def _log_execution_mode_context() -> None:
    """
    Phase 15 does NOT execute trades.
    This function exists to align runner structure with Phase E.
    """
    sheet_mode = os.getenv("EXECUTION_MODE")
    sheet_live_enabled = os.getenv("LIVE_ENABLED")
    env_ack = os.getenv("OBSERVER_LIVE_ACK")
```

---

### Files 7-8: Module Docstrings

#### File 7: `app/obs_deploy/app/src/backup/__init__.py`

```python
# BEFORE
"""
Backup module for QTS Observer datasets.
"""

# AFTER
"""
Backup module for Observer datasets.
"""
```

#### File 8: `app/obs_deploy/app/src/retention/__init__.py`

```python
# BEFORE
"""
Retention module for QTS Observer outputs.
...
Observer-Core is NOT imported here.
"""

# AFTER
"""
Retention module for Observer outputs.
...
Observer Core is NOT imported here.
"""
```

---

### File 9: `app/obs_deploy/README.md`

**변경 사항**:

```markdown
# QTS Observer Deployment Package
↓
# Observer Deployment Package
```

---

### File 10: `app/obs_deploy/Dockerfile`

**변경 사항**: 병합 충돌 해결

```dockerfile
# BEFORE (병합 충돌 상태)
<<<<<<< Updated upstream
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1
=======
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /bin/sh -c "python - <<'PY'\n..."
>>>>>>> Stashed changes

# AFTER (해결됨)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /bin/sh -c "python - <<'PY'\nimport sys\nimport urllib.request\nurl = 'http://127.0.0.1:8000/health'\ntry:\n    with urllib.request.urlopen(url, timeout=5) as resp:\n        sys.exit(0 if resp.getcode() == 200 else 1)\nexcept Exception:\n    sys.exit(1)\nPY"
```

**이유**: HTTP 기반 헬스 체크 유지 (FastAPI /health 엔드포인트 사용)

---

## 🔄 환경 변수 마이그레이션 가이드

배포 환경을 업데이트할 때 다음 환경 변수를 변경하십시오:

### Docker 환경

```bash
# OLD (QTS 방식)
export QTS_OBSERVER_STANDALONE=1
export QTS_LIVE_ACK=approved

# NEW (Observer 독립)
export OBSERVER_STANDALONE=1
export OBSERVER_LIVE_ACK=approved
```

### Docker Compose

```yaml
# OLD
services:
  observer:
    environment:
      - QTS_OBSERVER_STANDALONE=1
      - QTS_LIVE_ACK=approved

# NEW
services:
  observer:
    environment:
      - OBSERVER_STANDALONE=1
      - OBSERVER_LIVE_ACK=approved
```

### Kubernetes

```yaml
# OLD
env:
  - name: QTS_OBSERVER_STANDALONE
    value: "1"
  - name: QTS_LIVE_ACK
    value: "approved"

# NEW
env:
  - name: OBSERVER_STANDALONE
    value: "1"
  - name: OBSERVER_LIVE_ACK
    value: "approved"
```

---

## ✅ 검증 체크리스트

모든 변경사항에 대해 다음을 검증했습니다:

- ✅ Python 문법 검증 (py_compile)
- ✅ 환경 변수 일관성 확인
- ✅ 문서 및 주석 정합성
- ✅ 기존 기능 유지 확인
- ✅ Git 커밋 및 push 완료

---

## 📚 참고 문서

- [OBSERVER_INDEPENDENCE_COMPLETE.md](./OBSERVER_INDEPENDENCE_COMPLETE.md) - 완료 보고서
- [INTEGRATION_COMPLETE.md](./INTEGRATION_COMPLETE.md) - FastAPI 통합 보고서
- [QUICK_DECISION_GUIDE.md](./QUICK_DECISION_GUIDE.md) - 의사결정 가이드

---

**작업 완료**: 2026-01-20 21:45
**커밋**: 7de2d5e
**상태**: ✅ 완료
