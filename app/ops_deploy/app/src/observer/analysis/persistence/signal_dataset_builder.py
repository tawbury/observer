from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from src.ops.observer.analysis.signal_frame.contracts.signal_bundle import SignalBundle


class SignalDatasetBuilder:
    """
    Phase 13: SignalBundle -> JSONL asset builder

    Principles:
    - append-only write
    - deterministic output for same input
    - no filtering / no interpretation
    """

    def __init__(self, output_path: Path):
        self.output_path = output_path

    def build(self, signal_bundles: Iterable[SignalBundle]) -> None:
        """
        Serialize SignalBundle list into JSONL.

        Each line == one SignalBundle.to_dict()
        """
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        with self.output_path.open("w", encoding="utf-8") as f:
            for bundle in signal_bundles:
                record = bundle.to_dict()
                f.write(json.dumps(record, ensure_ascii=False))
                f.write("\n")
