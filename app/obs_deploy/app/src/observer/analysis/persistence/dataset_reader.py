# observer/analysis/persistence/dataset_reader.py
from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterator, List, Sequence

from .dataset_index import DatasetIdentity, DatasetIndex, PartitionKey


class DatasetReader:
    """
    Phase 6 Reader: loading only.

    Responsible for:
      - Streaming raw JSONL records
      - Loading feature Parquet into a list[dict]

    Not responsible for:
      - feature calculation
      - transforming business meaning
    """

    def __init__(self, index: DatasetIndex) -> None:
        self.index = index

    def iter_raw_jsonl(
        self,
        identity: DatasetIdentity,
        partition: PartitionKey,
        *,
        skip_identity_header: bool = True,
    ) -> Iterator[Dict[str, Any]]:
        """
        Stream raw JSONL partition records.
        """
        rel = self.index.relpath_for_raw_jsonl(identity, partition)
        path = os.path.join(self.index.base_dir, rel)
        if not os.path.exists(path):
            return iter(())  # empty iterator

        def _gen() -> Iterator[Dict[str, Any]]:
            with open(path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    if skip_identity_header and i == 0 and isinstance(obj, dict) and "_identity" in obj:
                        continue
                    yield obj

        return _gen()

    def load_features_parquet(
        self,
        identity: DatasetIdentity,
        partition: PartitionKey,
    ) -> Sequence[Dict[str, Any]]:
        """
        Load feature parquet partition into list[dict].

        Strategy:
          - Prefer pyarrow
          - Fall back to pandas
          - If neither is available, raise a clear error.
        """
        rel = self.index.relpath_for_features_parquet(identity, partition)
        path = os.path.join(self.index.base_dir, rel)
        if not os.path.exists(path):
            return []

        # Try pyarrow first
        try:
            import pyarrow.parquet as pq  # type: ignore

            table = pq.read_table(path)
            # Convert to list-of-dicts
            return table.to_pylist()

        except ModuleNotFoundError:
            pass

        # pandas fallback
        try:
            import pandas as pd  # type: ignore

            df = pd.read_parquet(path)
            return df.to_dict(orient="records")

        except ModuleNotFoundError as e:
            raise RuntimeError(
                "Parquet read requires 'pyarrow' or 'pandas' (with a parquet engine). "
                "Install one of them (recommended: pyarrow)."
            ) from e
