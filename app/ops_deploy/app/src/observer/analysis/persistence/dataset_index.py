# src/ops/observer/analysis/persistence/dataset_index.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class DatasetIdentity:
    """
    Dataset identity for indexing/partitioning.

    Notes:
    - Phase 6 uses this identity for storage layout and lookup only.
    - Do NOT embed strategy/decision semantics here.
    """
    dataset_name: str                 # e.g., "observer_raw", "observer_features"
    dataset_version: str              # e.g., "v1.0.0"
    build_id: str                     # unique build identifier
    session_id: str                   # unique session identifier
    generated_at: datetime            # when generated


@dataclass(frozen=True)
class PartitionKey:
    """
    Partition key to support rolling retention and efficient lookups.
    Recommended to partition by date (YYYY/MM/DD) and optionally symbol.

    Example:
      date_yyyymmdd="2025-12-25", symbol="005930"
    """
    date_yyyymmdd: str
    symbol: Optional[str] = None


class DatasetIndex:
    """
    Responsible for:
      - Converting DatasetIdentity + PartitionKey into canonical relative paths
      - Finding existing partitions / listing partitions

    Not responsible for:
      - writing/reading file content
      - retention deletion (Phase 6 defines policy; enforcement may be Phase 6/6.5)
    """

    def __init__(self, base_dir: str) -> None:
        self.base_dir = base_dir

    def relpath_for_raw_jsonl(self, identity: DatasetIdentity, partition: PartitionKey) -> str:
        """
        Returns a relative path for raw JSONL partition.
        The caller joins with base_dir and performs I/O.
        """
        # Example layout (suggested):
        # {dataset_name}/{dataset_version}/raw/date=YYYY-MM-DD/[symbol=XXXX/]build_id=...__session_id=....jsonl
        symbol_part = f"symbol={partition.symbol}/" if partition.symbol else ""
        filename = f"build_id={identity.build_id}__session_id={identity.session_id}.jsonl"
        return (
            f"{identity.dataset_name}/{identity.dataset_version}/raw/"
            f"date={partition.date_yyyymmdd}/{symbol_part}{filename}"
        )

    def relpath_for_features_parquet(self, identity: DatasetIdentity, partition: PartitionKey) -> str:
        """
        Returns a relative path for feature parquet partition.
        """
        symbol_part = f"symbol={partition.symbol}/" if partition.symbol else ""
        filename = f"build_id={identity.build_id}__session_id={identity.session_id}.parquet"
        return (
            f"{identity.dataset_name}/{identity.dataset_version}/features/"
            f"date={partition.date_yyyymmdd}/{symbol_part}{filename}"
        )
