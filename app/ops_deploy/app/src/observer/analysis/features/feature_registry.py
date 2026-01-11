# src/ops/observer/analysis/features/feature_registry.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional

from .feature_schema import FeatureSchema, FeatureSpec


class FeatureRegistry:
    """
    Registry of features for a given schema version.

    Responsibilities:
      - Holds FeatureSchema
      - Enforces that only registered features are emitted
      - Provides lookup utilities
    """

    def __init__(self, schema: FeatureSchema) -> None:
        self._schema = schema

    @property
    def schema(self) -> FeatureSchema:
        return self._schema

    def has(self, key: str) -> bool:
        return key in self._schema.features

    def get(self, key: str) -> FeatureSpec:
        return self._schema.features[key]

    def keys(self) -> Iterable[str]:
        return self._schema.features.keys()

    def validate_keys_subset(self, emitted_keys: Iterable[str]) -> None:
        """
        Ensure emitted_keys are all registered.
        """
        for k in emitted_keys:
            if k not in self._schema.features:
                raise KeyError(f"Unregistered feature key: {k} (schema={self._schema.version})")
