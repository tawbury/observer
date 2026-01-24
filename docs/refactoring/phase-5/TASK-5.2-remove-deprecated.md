# TASK-5.2: 폐기 파일 제거

## 태스크 정보
- **Phase**: 5 - 문서화 및 정리
- **우선순위**: Low
- **의존성**: Phase 1-4 완료
- **상태**: 대기

---

## 목표
더 이상 필요하지 않은 백업 파일, 빈 유틸리티 파일, 중복 모듈을 정리하여 코드베이스를 깔끔하게 유지합니다.

---

## 삭제 대상 파일

### 1. 백업 파일

| 파일 경로 | 이유 |
|----------|------|
| `observer_backup_20260120_211722.py` | 수동 백업 파일 - Git 히스토리로 대체 가능 |

**확인 방법:**
```bash
# 백업 파일 검색
find app/observer -name "*_backup_*" -type f
find app/observer -name "*.bak" -type f
find app/observer -name "*.backup" -type f
```

### 2. 빈 유틸리티 파일

| 파일 경로 | 현재 내용 | 이유 |
|----------|----------|------|
| `src/shared/utils.py` | 1줄 (비어있음) | Phase 1에서 실제 구현으로 대체됨 |
| `src/shared/decorators.py` | 1줄 (비어있음) | 필요시 구현, 현재는 불필요 |

**확인 방법:**
```bash
# 빈 파일 또는 매우 작은 파일 검색
find app/observer/src/shared -name "*.py" -size -50c
```

### 3. 통합된 중복 모듈

| 디렉토리/파일 | 이유 |
|--------------|------|
| `src/maintenance/retention/` | TASK-2.1에서 `src/retention/`으로 통합됨 |
| `src/maintenance/backup/` | TASK-2.2에서 `src/backup/`으로 통합됨 |
| `src/backup/backup_manager.py` | TASK-2.2에서 분리됨 (scheduler.py로) |
| `src/backup/manager.py` | TASK-2.2에서 core.py로 통합됨 |

### 4. 테스트 관련 정리

| 파일/디렉토리 | 이유 |
|--------------|------|
| `src/backup/test_backup_manager.py` | TASK-4.2에서 `tests/unit/backup/`로 이동됨 |
| `src/monitoring/test_monitoring_dashboard.py` | TASK-4.2에서 이동됨 |
| `src/optimize/test_performance_optimization.py` | TASK-4.2에서 이동됨 |
| `src/test/` | E2E 테스트가 `tests/integration/`으로 이동된 후 빈 디렉토리 |

### 5. 임시 파일

| 파일 패턴 | 이유 |
|----------|------|
| `*.pyc` | 컴파일된 Python 파일 |
| `__pycache__/` | Python 캐시 디렉토리 |
| `.pytest_cache/` | pytest 캐시 |
| `*.egg-info/` | 패키지 정보 |

---

## 구현 계획

### 단계 1: 삭제 전 백업 확인

```bash
# Git 상태 확인 - 모든 변경사항이 커밋되어 있는지
git status

# 삭제 대상 파일 목록 저장
cat > /tmp/files_to_delete.txt << 'EOF'
app/observer/observer_backup_20260120_211722.py
app/observer/src/shared/utils.py
app/observer/src/shared/decorators.py
app/observer/src/maintenance/retention/
app/observer/src/maintenance/backup/
app/observer/src/backup/backup_manager.py
app/observer/src/backup/manager.py
app/observer/src/test/
EOF
```

### 단계 2: 파일 삭제

```bash
# 백업 파일 삭제
rm -f app/observer/observer_backup_*.py

# 빈 유틸리티 파일 삭제 (또는 유지하고 내용 추가)
rm -f app/observer/src/shared/utils.py
rm -f app/observer/src/shared/decorators.py

# 통합된 모듈 삭제
rm -rf app/observer/src/maintenance/retention/
rm -rf app/observer/src/maintenance/backup/

# 이전 backup 파일 삭제 (통합 후)
rm -f app/observer/src/backup/backup_manager.py
rm -f app/observer/src/backup/manager.py

# 이동된 테스트 파일이 있던 위치 정리
rm -rf app/observer/src/test/
rm -f app/observer/src/backup/test_*.py
rm -f app/observer/src/monitoring/test_*.py
rm -f app/observer/src/optimize/test_*.py
```

### 단계 3: 임시 파일 정리

```bash
# Python 캐시 정리
find app/observer -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find app/observer -name "*.pyc" -delete
find app/observer -name "*.pyo" -delete

# pytest 캐시 정리
rm -rf app/observer/.pytest_cache

# egg-info 정리
rm -rf app/observer/*.egg-info
```

### 단계 4: .gitignore 업데이트

**파일**: `app/observer/.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# Environment
.env
.env.local
.env.*.local
venv/
ENV/

# Logs
*.log
logs/

# Local data
data/
secrets/
*.pem
*.key

# Backup files (use git instead)
*_backup_*
*.bak
*.backup
```

### 단계 5: maintenance 모듈 정리

통합 후 `src/maintenance/` 구조:

```
src/maintenance/
├── __init__.py
├── coordinator.py     # 유지
└── (retention/, backup/ 제거됨)
```

**파일**: `app/observer/src/maintenance/__init__.py`

```python
"""
Maintenance operations for Observer system.

Note: retention and backup functionality has been moved to their
respective modules (src/retention/ and src/backup/).
"""
from .coordinator import MaintenanceCoordinator

__all__ = ["MaintenanceCoordinator"]
```

---

## 검증 방법

### 1. 삭제된 파일 확인

```bash
# 백업 파일 없음
find app/observer -name "*_backup_*" | wc -l
# 결과: 0

# 빈 파일 없음
find app/observer/src/shared -name "*.py" -size -50c | wc -l
# 결과: 0

# 통합된 모듈 디렉토리 없음
ls -la app/observer/src/maintenance/
# retention/, backup/ 없어야 함
```

### 2. import 테스트

```bash
cd app/observer
python -c "from backup import create_backup; print('OK')"
python -c "from retention import RetentionPolicy; print('OK')"
python -c "from maintenance import MaintenanceCoordinator; print('OK')"
```

### 3. 테스트 실행

```bash
cd app/observer
pytest tests/ -v
# 모든 테스트 통과해야 함
```

### 4. 린트 확인

```bash
# 사용되지 않는 import 확인
pylint app/observer/src --disable=all --enable=unused-import
```

---

## 완료 조건

- [ ] 백업 파일 (`*_backup_*`) 제거됨
- [ ] 빈 유틸리티 파일 제거됨 (또는 실제 구현됨)
- [ ] `src/maintenance/retention/` 제거됨
- [ ] `src/maintenance/backup/` 제거됨
- [ ] 기존 backup 파일들 제거됨
- [ ] `src/test/` 제거됨
- [ ] src 내 test 파일들 제거됨
- [ ] `.gitignore` 업데이트됨
- [ ] `__pycache__` 정리됨
- [ ] 모든 테스트 통과
- [ ] import 오류 없음

---

## 주의사항

1. **삭제 전 확인**: 모든 변경사항이 Git에 커밋되어 있는지 확인
2. **통합 완료 후**: Phase 2의 통합 작업이 완료된 후에만 삭제
3. **테스트 이동 후**: Phase 4의 테스트 이동이 완료된 후에만 삭제
4. **점진적 삭제**: 한 번에 모두 삭제하지 말고 카테고리별로 삭제 후 테스트

---

## 롤백 계획

```bash
# Git에서 복원
git checkout HEAD~1 -- app/observer/src/maintenance/retention/
git checkout HEAD~1 -- app/observer/src/maintenance/backup/
# 등등
```

---

## 관련 태스크
- [TASK-2.1](../phase-2/TASK-2.1-consolidate-retention.md): Retention 통합 (선행)
- [TASK-2.2](../phase-2/TASK-2.2-consolidate-backup.md): Backup 통합 (선행)
- [TASK-4.2](../phase-4/TASK-4.2-reorganize-tests.md): 테스트 재구성 (선행)
