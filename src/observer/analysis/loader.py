from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

from .contracts.pattern_record_contract import PatternRecordContract


class PatternLoadError(Exception):
    """Raised when pattern loader cannot read or parse input records."""


@dataclass(frozen=True)
class LoadResult:
    records: List[PatternRecordContract]
    total_lines: int
    loaded: int
    skipped: int


def load_pattern_records(
    input_path: Union[str, Path],
    *,
    strict: bool = True,
    max_records: Optional[int] = None,
    encoding: str = "utf-8",
) -> LoadResult:
    """
    Load output into PatternRecordContract.

    Canonical rules:
    - Source is treated as external producer.
    - metadata is REQUIRED.
    - observation is OPTIONAL:
        * if present, used directly
        * if absent, synthesized from top-level fields
    - _schema / _quality / _interpretation are OPTIONAL.
    """
    path = Path(input_path)

    if not path.exists():
        raise PatternLoadError(f"Input file not found: {path}")

    suffix = path.suffix.lower()
    if suffix not in {".jsonl", ".json"}:
        raise PatternLoadError(
            f"Unsupported input format: {suffix} (expected .jsonl or .json)"
        )

    records: List[PatternRecordContract] = []
    total_lines = 0
    loaded = 0
    skipped = 0

    try:
        if suffix == ".jsonl":
            for total_lines, raw in enumerate(
                _iter_jsonl(path, encoding=encoding), start=1
            ):
                rec = _parse_one(raw, strict=strict, idx=total_lines)
                if rec is None:
                    skipped += 1
                else:
                    records.append(rec)
                    loaded += 1

                if max_records is not None and loaded >= max_records:
                    break

        else:
            data = _read_json(path, encoding=encoding)
            if not isinstance(data, list):
                raise PatternLoadError("JSON input must be a list of records.")

            total_lines = len(data)

            for idx, raw in enumerate(data, start=1):
                rec = _parse_one(raw, strict=strict, idx=idx)
                if rec is None:
                    skipped += 1
                else:
                    records.append(rec)
                    loaded += 1

                if max_records is not None and loaded >= max_records:
                    break

                    break

    except PatternLoadError:
        raise
    except Exception as e:
        raise PatternLoadError(f"Failed to load records from {path}: {e}") from e

    if strict and loaded == 0:
        raise PatternLoadError("No valid records loaded in strict mode.")

    return LoadResult(
        records=records,
        total_lines=total_lines,
        loaded=loaded,
        skipped=skipped,
    )


# =====================================================================
# Internal helpers (Pattern Loader)
# =====================================================================

def _iter_jsonl(path: Path, *, encoding: str) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding=encoding) as f:
        for line_no, line in enumerate(f, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                obj = json.loads(text)
            except json.JSONDecodeError as e:
                raise PatternLoadError(
                    f"Invalid JSON at line {line_no}: {e}"
                ) from e

            if not isinstance(obj, dict):
                raise PatternLoadError(
                    f"JSONL record must be an object at line {line_no}"
                )
            yield obj


def _read_json(path: Path, *, encoding: str) -> Any:
    with path.open("r", encoding=encoding) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            raise PatternLoadError(f"Invalid JSON file: {e}") from e


def _parse_one(
    raw: Any,
    *,
    strict: bool,
    idx: Optional[int] = None,
) -> Optional[PatternRecordContract]:
    prefix = f"[record {idx}] " if idx is not None else ""

    if not isinstance(raw, dict):
        if strict:
            raise PatternLoadError(prefix + "Record is not an object/dict.")
        return None

    metadata = raw.get("metadata")
    if not isinstance(metadata, dict):
        if strict:
            raise PatternLoadError(prefix + "Missing or invalid 'metadata' dict.")
        return None

    # --------------------------------------------------
    # Observation handling
    # --------------------------------------------------
    if "observation" in raw:
        observation = raw.get("observation")
        if not isinstance(observation, dict):
            if strict:
                raise PatternLoadError(prefix + "Invalid 'observation' field.")
            return None
    else:
        # Synthesize observation from top-level fields
        observation = {
            k: v
            for k, v in raw.items()
            if k not in {"metadata", "_schema", "_quality", "_interpretation"}
        }

    try:
        return PatternRecordContract(
            session_id=metadata.get("session_id", ""),
            generated_at=metadata.get("generated_at", ""),
            observation=observation,
            schema=raw.get("_schema", {}) or {},
            quality=raw.get("_quality", {}) or {},
            interpretation=raw.get("_interpretation", {}) or {},
        )
    except Exception as e:
        if strict:
            raise PatternLoadError(prefix + f"Failed to parse record: {e}") from e
        return None


# =====================================================================
# Raw Observation Log Loader (append-only)
# =====================================================================

from datetime import datetime, timezone
from typing import Iterator, Tuple


class RawLoadError(Exception):
    """Raised when raw loader cannot read raw observation logs."""


@dataclass(frozen=True)
class RawLogRecord:
    line_no: int
    ts_kst: datetime
    payload: Dict[str, Any]


@dataclass(frozen=True)
class RawLoadResult:
    records: List[RawLogRecord]
    total_lines: int
    loaded: int


def _parse_iso8601_to_kst(value: str) -> datetime:
    from shared.timezone import KST
    v = value.strip()
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    dt = datetime.fromisoformat(v)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=KST or timezone.utc)
    return dt.astimezone(KST or timezone.utc)


def _extract_raw_timestamp(raw: Dict[str, Any]) -> datetime:
    """
    Raw timestamp extraction (producer-agnostic, permissive).

    Priority (expanded after real log inspection):
      1) raw['meta']['captured_at']
      2) raw['meta']['generated_at']
      3) raw['captured_at']
      4) raw['generated_at']
      5) raw['created_at']
      6) raw['metadata']['generated_at']    # Compatibility
    """
    meta = raw.get("meta") if isinstance(raw.get("meta"), dict) else {}
    metadata = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}

    candidates = [
        meta.get("captured_at"),
        meta.get("generated_at"),
        raw.get("captured_at"),
        raw.get("generated_at"),
        raw.get("created_at"),              # 🔴 추가
        metadata.get("generated_at"),
    ]

    for c in candidates:
        if isinstance(c, str) and c.strip():
            return _parse_iso8601_to_kst(c)

    raise RawLoadError(
        "timestamp missing: expected one of "
        "meta.captured_at/meta.generated_at/"
        "captured_at/generated_at/created_at/"
        "metadata.generated_at"
    )


def _iter_jsonl_objects(
    path: Path, *, encoding: str
) -> Iterator[Tuple[int, Dict[str, Any]]]:
    with path.open("r", encoding=encoding) as f:
        for line_no, line in enumerate(f, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                obj = json.loads(text)
            except json.JSONDecodeError as e:
                raise RawLoadError(
                    f"Invalid JSON at line {line_no}: {e}"
                ) from e

            if not isinstance(obj, dict):
                raise RawLoadError(
                    f"JSONL record must be an object at line {line_no}"
                )
            yield line_no, obj



def load_observation_jsonl_records(
    input_path: Union[str, Path],
    *,
    max_records: Optional[int] = None,
    encoding: str = "utf-8",
) -> RawLoadResult:
    """
    Load raw observation logs.
    - Read observer logs back into code.
    - Does NOT depend on PatternRecordContract.
    - Keeps raw payload intact for later analysis.
    """
    path = Path(input_path)

    if not path.exists():
        raise RawLoadError(f"Input file not found: {path}")

    if path.suffix.lower() != ".jsonl":
        raise RawLoadError(
            f"Unsupported input format: {path.suffix} (expected .jsonl)"
        )

    records: List[RawLogRecord] = []
    total_lines = 0

    for line_no, raw in _iter_jsonl_objects(path, encoding=encoding):
        total_lines = line_no
        ts = _extract_raw_timestamp(raw)
        records.append(
            RawLogRecord(
                line_no=line_no,
                ts_kst=ts,
                payload=raw,
            )
        )

        if max_records is not None and len(records) >= max_records:
            break

    return RawLoadResult(
        records=records,
        total_lines=total_lines,
        loaded=len(records),
    )
