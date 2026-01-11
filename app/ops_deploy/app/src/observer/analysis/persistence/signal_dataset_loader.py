from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Iterator

from src.ops.observer.analysis.signal_frame.contracts.signal_bundle import SignalBundle


class SignalDatasetLoader:
    """
    Phase 13: JSONL Signal Dataset Loader

    Principles:
    - read-only
    - lazy iteration
    - no filtering / no reordering
    - no interpretation
    """

    def __init__(self, dataset_path: Path):
        self.dataset_path = dataset_path

    def load(self) -> Iterable[SignalBundle]:
        """
        Lazy-load SignalBundle records from JSONL.

        Yields:
            SignalBundle (one per line)
        """
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Signal dataset not found: {self.dataset_path}")

        return self._iter_records()

    def _iter_records(self) -> Iterator[SignalBundle]:
        with self.dataset_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                data = json.loads(line)

                yield SignalBundle(
                    schema_version=data["schema_version"],
                    record_key=data["record_key"],
                    meta=data.get("meta", {}),
                    features=data.get("features", {}),
                    conditions=data.get("conditions", {}),
                )
