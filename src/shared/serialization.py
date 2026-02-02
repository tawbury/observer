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
    "order_hint_fingerprint",
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
