from __future__ import annotations

from pathlib import Path
from typing import Dict, List


class RetentionIndex:
    """
    Lightweight index for retained datasets.

    This index is intended for:
    - audit
    - inspection
    - reporting
    """

    def __init__(self):
        self._index: Dict[str, List[Path]] = {}

    def add(self, key: str, path: Path) -> None:
        self._index.setdefault(key, []).append(path)

    def get(self, key: str) -> List[Path]:
        return self._index.get(key, [])

    def keys(self):
        return self._index.keys()
