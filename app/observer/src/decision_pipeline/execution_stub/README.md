# Execution Stub Module

의사결정 파이프라인의 주문 실행 계층입니다.

## 아키텍처

```
BaseExecutor (추상 클래스)
    ├── NoopExecutor (실행 없음, 로깅만)
    ├── SimExecutor (시뮬레이션 실행)
    └── VirtualExecutor (KIS 모의투자 계좌 실행)
```

## BaseExecutor

모든 Executor의 공통 기능을 제공하는 추상 베이스 클래스입니다.

### 주요 기능

1. **실행 모드 관리**: `ExecutionMode` enum으로 모드 구분
2. **핑거프린트 생성**: Order + Hint의 고유 해시 생성으로 중복 실행 방지
3. **에러 핸들링**: 통일된 에러 결과 반환
4. **실행 횟수 추적**: `_execution_count`로 통계 수집

### 실행 흐름

```
execute() → _do_execute() → ExecutionResult
    ↓
1. Decision ID 추출
2. Fingerprint 생성
3. 실제 실행 로직 호출 (_do_execute)
4. 결과 반환 (성공/실패)
```

### 사용 예시

```python
from decision_pipeline.execution_stub.base_executor import BaseExecutor, ExecutionMode
from decision_pipeline.execution_stub.types import ExecutionResult

class MyExecutor(BaseExecutor):
    def __init__(self):
        super().__init__(mode=ExecutionMode.REAL)
    
    def _do_execute(self, *, order, hint, context, decision_id, fingerprint) -> ExecutionResult:
        """실제 주문 실행 로직"""
        try:
            # 주문 제출
            order_id = self.broker.submit_order(order)
            
            return ExecutionResult(
                decision_id=decision_id,
                fingerprint=fingerprint,
                status="success",
                order_id=order_id
            )
        except Exception as e:
            return self._create_error_result(
                decision_id=decision_id,
                fingerprint=fingerprint,
                error=str(e)
            )

# Executor 사용
executor = MyExecutor()
result = executor.execute(
    order=order_decision,
    hint=execution_hint,
    context=execution_context
)
```

## NoopExecutor

주문을 실행하지 않고 로깅만 수행합니다.

### 사용 시나리오
- 의사결정 파이프라인 테스트
- Dry-run 모드 (실제 주문 없이 로직 검증)
- 주문 생성 통계 수집

## SimExecutor

로컬 시뮬레이션 환경에서 주문을 실행합니다.

### 특징
- In-memory 포지션 관리
- 간단한 체결 시뮬레이션
- 백테스팅용 빠른 실행
- 실제 API 호출 없음

## VirtualExecutor

KIS 모의투자 계좌에서 주문을 실행합니다.

### 특징
- 실제 KIS API 사용 (모의투자 서버)
- 실계좌와 동일한 주문 프로세스
- 체결 확인 및 상태 추적
- 실전 배포 전 최종 검증용

### 설정

```python
from decision_pipeline.execution_stub.virtual_executor import VirtualExecutor

executor = VirtualExecutor(
    app_key=os.getenv("KIS_APP_KEY"),
    app_secret=os.getenv("KIS_APP_SECRET"),
    account_no="모의계좌번호",
    is_virtual=True  # 모의투자 모드
)
```

## 핑거프린트 시스템

중복 실행을 방지하기 위한 핑거프린트 시스템:

```python
from shared.serialization import order_hint_fingerprint

# Order와 Hint로 고유 해시 생성
fp = order_hint_fingerprint(order, hint)
# 예: "a3f5e9d2b1c4f8a7"

# 동일한 Order + Hint는 항상 같은 핑거프린트 생성
# → 중복 실행 방지 가능
```

## ExecutionResult

모든 Executor는 표준화된 `ExecutionResult` 반환:

```python
@dataclass
class ExecutionResult:
    decision_id: str
    fingerprint: str
    status: str  # "success", "error", "pending"
    order_id: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
```

## 확장 가이드

새로운 Executor를 추가하려면:

1. `BaseExecutor` 상속
2. `_do_execute()` 메서드 구현
3. `ExecutionMode` enum에 새 모드 추가
4. 테스트 작성 (tests/unit/execution_stub/)

```python
class MyNewExecutor(BaseExecutor):
    def __init__(self):
        super().__init__(mode=ExecutionMode.MY_NEW_MODE)
    
    def _do_execute(self, *, order, hint, context, decision_id, fingerprint):
        # 실행 로직 구현
        pass
```
