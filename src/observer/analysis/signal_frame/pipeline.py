from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

from .contracts.signal_bundle import SignalBundle, ensure_plain_dict
from .features.base import FeatureContext
from .features.time import TimeFeatures
from .features.frequency import FrequencyFeatures
from .features.volatility import VolatilityLiteFeatures
from .conditions.base import ConditionContext
from .conditions.threshold import ThresholdConditions
from .conditions.window import WindowConditions


JsonDict = Dict[str, Any]


@dataclass(frozen=True)
class SignalFrameConfig:
    """
    Stateless knobs for feature + condition extraction.

    No strategy semantics. No scoring.
    """
    schema_version: str = "signal_bundle.v1"

    window_n: int = 20

    # threshold conditions
    value_change_exceeds_x: float = 0.01
    event_frequency_exceeds_n: int = 20

    # window conditions
    consecutive_events_ge_n: int = 3
    pattern_reappeared_within_t: float = 60.0

    # meta sizing (for window condition)
    include_records_window_in_meta: bool = True


def make_record_key(record: Mapping[str, Any], index: int) -> str:
    rid = record.get("id", record.get("record_id"))
    return str(rid) if rid is not None else f"idx:{index}"


def build_signal_bundles(
    replay_records: List[Mapping[str, Any]],
    *,
    config: SignalFrameConfig = SignalFrameConfig(),
    time_axis_index: Optional[List[int]] = None,
) -> List[SignalBundle]:
    """
    ReplayDataset -> (pure features) -> (pure conditions) -> SignalBundle

    Pure + deterministic:
      - No I/O
      - No mutation of input records
      - Same input -> same output
    """
    # feature extractors (stateless)
    f_time = TimeFeatures()
    f_freq = FrequencyFeatures()
    f_vol = VolatilityLiteFeatures()

    # condition evaluators (stateless)
    c_threshold = ThresholdConditions()
    c_window = WindowConditions()

    cond_cfg: JsonDict = {
        "value_change_exceeds_x": float(config.value_change_exceeds_x),
        "event_frequency_exceeds_n": int(config.event_frequency_exceeds_n),
        "consecutive_events_ge_n": int(config.consecutive_events_ge_n),
        "pattern_reappeared_within_t": float(config.pattern_reappeared_within_t),
    }
    cond_ctx = ConditionContext(config=cond_cfg)

    out: List[SignalBundle] = []

    for i, record in enumerate(replay_records):
        ctx = FeatureContext(
            records=replay_records,
            index=i,
            window_n=int(config.window_n),
            time_axis_index=(time_axis_index[i] if time_axis_index is not None else None),
        )

        features: JsonDict = {}
        features.update(f_time.extract(record, ctx))
        features.update(f_freq.extract(record, ctx))
        features.update(f_vol.extract(record, ctx))

        meta: JsonDict = {}
        if config.include_records_window_in_meta:
            start = max(0, i - int(config.window_n) + 1)
            # keep JSON-safe (copy only)
            meta["records_window"] = [dict(r) for r in replay_records[start : i + 1]]

        bundle_dict: JsonDict = {
            "schema_version": config.schema_version,
            "record_key": make_record_key(record, i),
            "meta": meta,
            "features": features,
        }

        conditions: Dict[str, bool] = {}
        conditions.update(c_threshold.evaluate(bundle_dict, cond_ctx))
        conditions.update(c_window.evaluate(bundle_dict, cond_ctx))

        out.append(
            SignalBundle(
                schema_version=config.schema_version,
                record_key=bundle_dict["record_key"],
                meta=ensure_plain_dict(meta),
                features=ensure_plain_dict(features),
                conditions=conditions,
            )
        )

    return out
