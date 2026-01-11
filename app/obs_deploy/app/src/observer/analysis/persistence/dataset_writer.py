# src/ops/observer/analysis/persistence/dataset_writer.py
from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import Any, Dict, Iterable, Optional, Sequence

from .dataset_index import DatasetIdentity, DatasetIndex, PartitionKey


class DatasetWriter:
    """
    Phase 6 Writer: persistence only.

    Responsible for:
      - Writing raw JSONL partitions (append-only)
      - Writing feature Parquet partitions

    Not responsible for:
      - computing features
      - transforming business meaning
      - validation/guard/eventbus
    """

    def __init__(self, index: DatasetIndex) -> None:
        self.index = index

    def write_raw_jsonl(
        self,
        identity: DatasetIdentity,
        partition: PartitionKey,
        records: Iterable[Dict[str, Any]],
        *,
        ensure_dirs: bool = True,
        include_identity_header: bool = False,
    ) -> str:
        """
        Append records to a JSONL file.

        include_identity_header:
          If True, writes a first line header record containing identity metadata
          with key "_identity". Keep False by default to avoid duplication when appending.

        Returns: absolute path written to.
        """
        rel = self.index.relpath_for_raw_jsonl(identity, partition)
        path = os.path.join(self.index.base_dir, rel)
        if ensure_dirs:
            os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, "a", encoding="utf-8") as f:
            if include_identity_header:
                header = {"_identity": asdict(identity)}
                f.write(json.dumps(header, ensure_ascii=False) + "\n")

            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        return path

    def write_features_parquet(
        self,
        identity: DatasetIdentity,
        partition: PartitionKey,
        rows: Sequence[Dict[str, Any]],
        *,
        ensure_dirs: bool = True,
        compression: str = "zstd",
    ) -> str:
        """
        Write feature rows to a Parquet file.

        Strategy:
          - Prefer pyarrow for explicit schema/metadata control.
          - Fall back to pandas if available.
          - If neither is available, raise a clear error.

        Returns: absolute parquet path written to.
        """
        rel = self.index.relpath_for_features_parquet(identity, partition)
        path = os.path.join(self.index.base_dir, rel)
        if ensure_dirs:
            os.makedirs(os.path.dirname(path), exist_ok=True)

        # Normalize rows: if empty, still write a valid file with no rows (best effort).
        rows_list = list(rows)

        # Try pyarrow first
        try:
            import pyarrow as pa  # type: ignore
            import pyarrow.parquet as pq  # type: ignore

            # Build table from list-of-dicts (column set inferred)
            table = pa.Table.from_pylist(rows_list)

            # Attach minimal metadata (non-semantic)
            meta = {
                b"dataset_name": identity.dataset_name.encode("utf-8"),
                b"dataset_version": identity.dataset_version.encode("utf-8"),
                b"build_id": identity.build_id.encode("utf-8"),
                b"session_id": identity.session_id.encode("utf-8"),
                b"generated_at": identity.generated_at.isoformat().encode("utf-8"),
            }
            existing = table.schema.metadata or {}
            merged = dict(existing)
            merged.update(meta)
            table = table.replace_schema_metadata(merged)

            pq.write_table(table, path, compression=compression)
            return path

        except ModuleNotFoundError:
            # Fall back to pandas
            pass

        # pandas fallback
        try:
            import pandas as pd  # type: ignore

            df = pd.DataFrame(rows_list)
            # pandas uses pyarrow/fastparquet as backend; if neither, will raise.
            df.to_parquet(
                path,
                index=False,
                compression=compression,
            )
            return path

        except ModuleNotFoundError as e:
            raise RuntimeError(
                "Parquet write requires 'pyarrow' or 'pandas' (with a parquet engine). "
                "Install one of them (recommended: pyarrow)."
            ) from e
