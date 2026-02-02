from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

from .persistence.dataset_index import DatasetIdentity, DatasetIndex, PartitionKey
from .persistence.dataset_reader import DatasetReader
from .persistence.dataset_writer import DatasetWriter
from .features.feature_builder import FeatureBuildContext, FeatureBuilder
from .features.feature_registry import FeatureRegistry
from .features.feature_schema import load_decision_feature_schema_v1


@dataclass(frozen=True)
class DecisionConfig:
    """
    Decision pipeline configuration.
    """
    base_dir: str
    raw_dataset_name: str = "observer_raw"
    feature_dataset_name: str = "observer_features"
    dataset_version: str = "v1.0.0"


class DecisionPipeline:
    """
    Decision Pipeline.

    Responsibilities:
      - Persist raw observation datasets (JSONL)
      - Build schema-first observation features
      - Persist feature datasets (Parquet)

    Explicitly NOT responsible for:
      - Strategy / signal generation
      - Scoring or prediction
      - Execution
      - Backup automation
    """

    def __init__(self, cfg: DecisionConfig) -> None:
        self.cfg = cfg

        self.index = DatasetIndex(base_dir=cfg.base_dir)
        self.writer = DatasetWriter(self.index)
        self.reader = DatasetReader(self.index)

        schema = load_decision_feature_schema_v1()
        self.registry = FeatureRegistry(schema)
        self.feature_builder = FeatureBuilder(self.registry)

    # ------------------------------------------------------------------
    # Raw persistence
    # ------------------------------------------------------------------

    def persist_raw(
        self,
        *,
        build_id: str,
        session_id: str,
        date_yyyymmdd: str,
        symbol: Optional[str],
        records: Iterable[Dict[str, Any]],
    ) -> str:
        identity = DatasetIdentity(
            dataset_name=self.cfg.raw_dataset_name,
            dataset_version=self.cfg.dataset_version,
            build_id=build_id,
            session_id=session_id,
            generated_at=datetime.now(timezone.utc),
        )
        partition = PartitionKey(
            date_yyyymmdd=date_yyyymmdd,
            symbol=symbol,
        )
        return self.writer.write_raw_jsonl(identity, partition, records)

    # ------------------------------------------------------------------
    # Feature build & persistence
    # ------------------------------------------------------------------

    def build_and_persist_features_from_records(
        self,
        *,
        build_id: str,
        session_id: str,
        date_yyyymmdd: str,
        symbol: Optional[str],
        records: Iterable[Dict[str, Any]],
    ) -> str:
        ctx = FeatureBuildContext(
            symbol=symbol,
            date_yyyymmdd=date_yyyymmdd,
        )

        feature_row = self.feature_builder.build_from_records(ctx, records)

        identity = DatasetIdentity(
            dataset_name=self.cfg.feature_dataset_name,
            dataset_version=self.cfg.dataset_version,
            build_id=build_id,
            session_id=session_id,
            generated_at=datetime.now(timezone.utc),
        )
        partition = PartitionKey(
            date_yyyymmdd=date_yyyymmdd,
            symbol=symbol,
        )

        return self.writer.write_features_parquet(identity, partition, [feature_row])

    # ------------------------------------------------------------------
    # Feature loading (공식 API)
    # ------------------------------------------------------------------

    def load_features(
        self,
        *,
        build_id: str,
        session_id: str,
        date_yyyymmdd: str,
        symbol: Optional[str],
    ):
        """
        Load persisted feature rows for a given partition.

        This is the ONLY supported way to load features
        from outside the DecisionPipeline.
        """
        identity = DatasetIdentity(
            dataset_name=self.cfg.feature_dataset_name,
            dataset_version=self.cfg.dataset_version,
            build_id=build_id,
            session_id=session_id,
            generated_at=datetime.now(timezone.utc),
        )
        partition = PartitionKey(
            date_yyyymmdd=date_yyyymmdd,
            symbol=symbol,
        )
        return self.reader.load_features_parquet(identity, partition)
