from __future__ import annotations

from pathlib import Path
from typing import Iterable, List


class DatasetScanner:
    """
    Scans observer dataset directories.
    """

    def __init__(self, dataset_root: Path):
        self.dataset_root = dataset_root

    def exists(self) -> bool:
        return self.dataset_root.exists()

    def iter_files(self) -> Iterable[Path]:
        if not self.exists():
            return []

        for p in self.dataset_root.rglob("*"):
            if p.is_file() and not p.name.startswith("."):
                yield p

    def list_files(self) -> List[Path]:
        return list(self.iter_files())
