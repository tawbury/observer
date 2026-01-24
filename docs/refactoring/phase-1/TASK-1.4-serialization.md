# TASK-1.4: Serialization 유틸리티 생성

## 태스크 정보
- **Phase**: 1 - 공유 유틸리티 추출
- **우선순위**: Critical
- **의존성**: 없음
- **상태**: 대기

---

## 목표
`_safe_to_dict()`와 `_fingerprint()` 함수를 공유 유틸리티로 추출하여 코드 중복을 제거합니다.

---

## 현재 문제

### 중복 코드 패턴

#### `_safe_to_dict()` 함수
sim_executor.py와 virtual_executor.py에서 객체를 딕셔너리로 변환하는 유사한 로직이 존재합니다.

**sim_executor.py (간단한 버전):**
```python
def _safe_to_dict(obj: Any) -> Any:
    if obj is None:
        return None
    if hasattr(obj, "__dict__"):
        return {k: _safe_to_dict(v) for k, v in obj.__dict__.items()}
    return obj
```

**virtual_executor.py (확장된 버전):**
```python
def _safe_to_dict(obj: Any) -> Any:
    if obj is None:
        return None
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        return obj.to_dict()
    if hasattr(obj, "__dict__"):
        return {k: _safe_to_dict(v) for k, v in obj.__dict__.items()}
    return obj
```

#### `_fingerprint()` 함수
두 파일 모두 SHA256 해시를 생성하는 동일한 로직:

```python
def _fingerprint(order: Any, hint: Any) -> str:
    data = json.dumps(
        {"order": _safe_to_dict(order), "hint": _safe_to_dict(hint)},
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(data.encode()).hexdigest()[:16]
```

### 영향 파일 목록 (2개)

| # | 파일 경로 | 라인 |
|---|----------|------|
| 1 | `app/obs_deploy/app/src/decision_pipeline/execution_stub/sim_executor.py` | 16-28 |
| 2 | `app/obs_deploy/app/src/decision_pipeline/execution_stub/virtual_executor.py` | 18-53 |

---

## 구현 계획

### 1. 신규 파일 생성

**파일**: `app/obs_deploy/app/src/shared/serialization.py`

```python
"""
Serialization utilities for converting objects to dictionaries and generating fingerprints.

This module provides consistent serialization across the codebase,
supporting dataclasses, objects with to_dict methods, and regular objects.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Optional


__all__ = [
    "safe_to_dict",
    "fingerprint",
    "json_serialize",
]


def safe_to_dict(obj: Any) -> Any:
    """
    Safely convert an object to a dictionary representation.

    Handles various object types in priority order:
    1. None -> None
    2. Dataclass -> asdict()
    3. Object with to_dict() method -> to_dict()
    4. Object with __dict__ -> recursive conversion
    5. Other -> return as-is

    Args:
        obj: Object to convert

    Returns:
        Dictionary representation or original value

    Example:
        >>> from dataclasses import dataclass
        >>> @dataclass
        ... class Order:
        ...     id: str
        ...     amount: float
        >>> safe_to_dict(Order("123", 100.0))
        {'id': '123', 'amount': 100.0}
    """
    if obj is None:
        return None

    # Handle dataclasses
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)

    # Handle objects with to_dict method
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        try:
            return obj.to_dict()
        except Exception:
            pass  # Fall through to next method

    # Handle objects with __dict__
    if hasattr(obj, "__dict__"):
        return {k: safe_to_dict(v) for k, v in obj.__dict__.items()}

    # Return primitive types as-is
    return obj


def fingerprint(
    *objects: Any,
    length: int = 16,
) -> str:
    """
    Generate a SHA256 fingerprint from one or more objects.

    Creates a deterministic hash from the JSON serialization of objects.
    Useful for generating unique identifiers for order/hint pairs.

    Args:
        *objects: Objects to include in the fingerprint
        length: Length of the returned hash (default: 16)

    Returns:
        Hexadecimal fingerprint string

    Example:
        >>> fingerprint({"order": "123"}, {"hint": "buy"})
        'a1b2c3d4e5f67890'
    """
    data = json.dumps(
        [safe_to_dict(obj) for obj in objects],
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(data.encode()).hexdigest()[:length]


def order_hint_fingerprint(order: Any, hint: Any) -> str:
    """
    Generate a fingerprint specifically for order/hint pairs.

    This maintains backward compatibility with existing executor code.

    Args:
        order: Order object
        hint: Hint object

    Returns:
        16-character hexadecimal fingerprint
    """
    data = json.dumps(
        {"order": safe_to_dict(order), "hint": safe_to_dict(hint)},
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def json_serialize(obj: Any, pretty: bool = False) -> str:
    """
    Serialize an object to JSON string using safe_to_dict.

    Args:
        obj: Object to serialize
        pretty: If True, format with indentation

    Returns:
        JSON string
    """
    data = safe_to_dict(obj)
    if pretty:
        return json.dumps(data, indent=2, default=str, ensure_ascii=False)
    return json.dumps(data, default=str, ensure_ascii=False)
```

### 2. 기존 파일 수정

#### `src/decision_pipeline/execution_stub/sim_executor.py`

**Before:**
```python
import hashlib
import json
from typing import Any

def _safe_to_dict(obj: Any) -> Any:
    if obj is None:
        return None
    if hasattr(obj, "__dict__"):
        return {k: _safe_to_dict(v) for k, v in obj.__dict__.items()}
    return obj

def _fingerprint(order: Any, hint: Any) -> str:
    data = json.dumps(
        {"order": _safe_to_dict(order), "hint": _safe_to_dict(hint)},
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(data.encode()).hexdigest()[:16]
```

**After:**
```python
from shared.serialization import order_hint_fingerprint

# 클래스 내부에서 _fingerprint 대신 사용:
# fingerprint = _fingerprint(order, hint)
# ->
# fingerprint = order_hint_fingerprint(order, hint)
```

#### `src/decision_pipeline/execution_stub/virtual_executor.py`

**Before:**
```python
import hashlib
import json
from dataclasses import asdict, is_dataclass
from typing import Any

def _safe_to_dict(obj: Any) -> Any:
    if obj is None:
        return None
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        return obj.to_dict()
    if hasattr(obj, "__dict__"):
        return {k: _safe_to_dict(v) for k, v in obj.__dict__.items()}
    return obj

def _fingerprint(order: Any, hint: Any) -> str:
    data = json.dumps(
        {"order": _safe_to_dict(order), "hint": _safe_to_dict(hint)},
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(data.encode()).hexdigest()[:16]
```

**After:**
```python
from shared.serialization import order_hint_fingerprint, safe_to_dict

# _fingerprint -> order_hint_fingerprint
# _safe_to_dict -> safe_to_dict (필요한 경우)
```

---

## 검증 방법

### 1. 단위 테스트
```python
# tests/unit/shared/test_serialization.py
import pytest
from dataclasses import dataclass
from shared.serialization import (
    safe_to_dict,
    fingerprint,
    order_hint_fingerprint,
    json_serialize,
)


class TestSafeToDict:
    def test_none(self):
        assert safe_to_dict(None) is None

    def test_dataclass(self):
        @dataclass
        class Order:
            id: str
            amount: float

        order = Order("123", 100.0)
        result = safe_to_dict(order)
        assert result == {"id": "123", "amount": 100.0}

    def test_object_with_to_dict(self):
        class Custom:
            def to_dict(self):
                return {"custom": True}

        result = safe_to_dict(Custom())
        assert result == {"custom": True}

    def test_object_with_dict(self):
        class Simple:
            def __init__(self):
                self.value = 42

        result = safe_to_dict(Simple())
        assert result == {"value": 42}

    def test_primitive(self):
        assert safe_to_dict("hello") == "hello"
        assert safe_to_dict(123) == 123
        assert safe_to_dict([1, 2, 3]) == [1, 2, 3]


class TestFingerprint:
    def test_deterministic(self):
        obj1 = {"key": "value"}
        obj2 = {"key": "value"}
        assert fingerprint(obj1) == fingerprint(obj2)

    def test_different_objects(self):
        obj1 = {"key": "value1"}
        obj2 = {"key": "value2"}
        assert fingerprint(obj1) != fingerprint(obj2)

    def test_custom_length(self):
        result = fingerprint({"test": True}, length=8)
        assert len(result) == 8

    def test_multiple_objects(self):
        result = fingerprint({"a": 1}, {"b": 2})
        assert len(result) == 16


class TestOrderHintFingerprint:
    def test_order_hint(self):
        @dataclass
        class Order:
            id: str

        @dataclass
        class Hint:
            action: str

        order = Order("123")
        hint = Hint("buy")

        fp1 = order_hint_fingerprint(order, hint)
        fp2 = order_hint_fingerprint(order, hint)
        assert fp1 == fp2
        assert len(fp1) == 16


class TestJsonSerialize:
    def test_simple(self):
        result = json_serialize({"key": "value"})
        assert result == '{"key": "value"}'

    def test_pretty(self):
        result = json_serialize({"key": "value"}, pretty=True)
        assert "\n" in result
        assert "  " in result
```

### 2. 통합 테스트
```bash
# 기존 테스트 통과 확인
pytest app/obs_deploy/app/src/decision_pipeline/ -v

# 중복 함수 검색 (shared 외에 0개여야 함)
grep -rn "def _safe_to_dict" --include="*.py" app/obs_deploy/app/src/ | grep -v shared/
grep -rn "def _fingerprint" --include="*.py" app/obs_deploy/app/src/ | grep -v shared/
```

### 3. 핑거프린트 일관성 테스트
```python
# 기존 코드와 새 코드의 핑거프린트가 동일한지 확인
def test_backward_compatibility():
    # 기존 방식
    import hashlib
    import json

    def old_safe_to_dict(obj):
        if obj is None:
            return None
        if hasattr(obj, "__dict__"):
            return {k: old_safe_to_dict(v) for k, v in obj.__dict__.items()}
        return obj

    def old_fingerprint(order, hint):
        data = json.dumps(
            {"order": old_safe_to_dict(order), "hint": old_safe_to_dict(hint)},
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    # 새 방식
    from shared.serialization import order_hint_fingerprint

    # 테스트 데이터
    class TestOrder:
        def __init__(self):
            self.id = "123"
            self.amount = 100

    class TestHint:
        def __init__(self):
            self.action = "buy"

    order = TestOrder()
    hint = TestHint()

    # 비교
    old_fp = old_fingerprint(order, hint)
    new_fp = order_hint_fingerprint(order, hint)

    assert old_fp == new_fp, f"Fingerprints differ: {old_fp} vs {new_fp}"
```

---

## 완료 조건

- [ ] `src/shared/serialization.py` 파일 생성됨
- [ ] `safe_to_dict()` 함수 구현됨 (dataclass, to_dict, __dict__ 지원)
- [ ] `fingerprint()` 함수 구현됨
- [ ] `order_hint_fingerprint()` 함수 구현됨 (하위 호환성)
- [ ] `json_serialize()` 함수 구현됨
- [ ] sim_executor.py에서 중복 코드 제거됨
- [ ] virtual_executor.py에서 중복 코드 제거됨
- [ ] 단위 테스트 통과
- [ ] 하위 호환성 테스트 통과 (핑거프린트 동일)
- [ ] 기존 테스트 모두 통과

---

## 주의사항

1. **핑거프린트 호환성**: 기존 시스템에서 생성된 핑거프린트와 새 코드의 핑거프린트가 동일해야 함. 이는 감사 추적(audit trail)에 영향을 미칠 수 있음.

2. **직렬화 순서**: `sort_keys=True`를 유지하여 결정론적 출력 보장

3. **dataclass 우선순위**: virtual_executor의 확장된 버전을 채택하여 dataclass를 먼저 처리

---

## 관련 태스크
- [TASK-3.2](../phase-3/TASK-3.2-base-executor.md): BaseExecutor (이 유틸리티 사용)
