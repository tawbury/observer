# observer/analysis/features/feature_validator.py
from __future__ import annotations

from typing import Any, Dict

from .feature_registry import FeatureRegistry


class FeatureValidator:
    """
    Validate a single feature row against the registry schema.

    Checks:
      - required fields present
      - dtype coercibility (basic)
    """

    def __init__(self, registry: FeatureRegistry) -> None:
        self.registry = registry

    def validate_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns a validated (and minimally coerced) row.
        """
        # Required checks + defaults
        out: Dict[str, Any] = dict(row)

        for key, spec in self.registry.schema.features.items():
            if spec.required and key not in out:
                if spec.default is not None:
                    out[key] = spec.default
                else:
                    raise ValueError(f"Missing required feature: {key}")

            if key in out and out[key] is not None:
                out[key] = self._coerce_dtype(key, out[key], spec.dtype)

        # Ensure no unknown keys
        self.registry.validate_keys_subset(out.keys())
        return out

    def _coerce_dtype(self, key: str, value: Any, dtype: str) -> Any:
        try:
            if dtype == "int":
                return int(value)
            if dtype == "float":
                return float(value)
            if dtype == "bool":
                # allow "true"/"false"/1/0
                if isinstance(value, str):
                    v = value.strip().lower()
                    if v in ("true", "1", "yes", "y"):
                        return True
                    if v in ("false", "0", "no", "n"):
                        return False
                return bool(value)
            if dtype == "str":
                return str(value)
        except Exception as e:
            raise TypeError(f"Feature dtype coercion failed: {key}={value!r} to {dtype}") from e

        raise ValueError(f"Unknown dtype in schema: {dtype}")
