from __future__ import annotations

"""
schema_lite.py

Observer 전용 "Schema Auto Lite" 레이어

왜 필요한가?
- Observer 로그(JSONL)는 장기 자산이다.
- Phase 4~5~6에서 메타데이터 구조가 확장/변경될 수 있다.
- 스키마가 조금만 바뀌어도 분석기/파서가 깨지면 운영이 불가능해진다.

이 파일의 역할:
- Observer 출력 레코드(PatternRecord)에 대해
  1) 스키마 버전(Record Schema Version)을 부여하고
  2) 확장 네임스페이스를 표준화하며
  3) 최소한의 호환성 규칙을 제공한다.

중요:
- Google Sheets 기반 Schema Auto Engine(Full)은 Observer에 과하다.
- Observer에는 "버전/네임스페이스/호환성"만 있으면 된다.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


# ============================================================
# Constants (Observer Schema-Lite)
# ============================================================

# PatternRecord의 "출력 스키마 버전"
# - Phase 4부터 record.metadata에 _schema/_quality/_interpretation 네임스페이스를 도입한다.
RECORD_SCHEMA_NAME = "PatternRecord"
RECORD_SCHEMA_VERSION = "v1.1.0"

# 과거 레코드 최소 호환 버전(정책)
# - v1.0.0: Phase 3 기준(quality_flags / validation / guard 등)
COMPAT_MIN_VERSION = "v1.0.0"

# 확장 네임스페이스(고정)
NS_SCHEMA = "_schema"
NS_QUALITY = "_quality"
NS_INTERPRETATION = "_interpretation"


@dataclass(frozen=True)
class SchemaLiteInfo:
    """
    레코드에 기록되는 스키마 라이트 정보 구조.
    """
    name: str = RECORD_SCHEMA_NAME
    version: str = RECORD_SCHEMA_VERSION
    compat_min: str = COMPAT_MIN_VERSION


def ensure_namespaces(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    metadata dict에 Schema-Lite 네임스페이스가 존재하도록 보장한다.

    - 기존 metadata는 절대 삭제하지 않는다(append-only 성격 유지).
    - 네임스페이스 키가 이미 있으면 그대로 유지한다.
    """
    out = dict(metadata)  # 얕은 복사(불변성 유지)

    out.setdefault(NS_SCHEMA, {})
    out.setdefault(NS_QUALITY, {})
    out.setdefault(NS_INTERPRETATION, {})

    return out


def apply_schema_lite(
    metadata: Dict[str, Any],
    *,
    producer: str,
    build_id: str,
    dataset_version: str,
    generated_at: str,
    session_id: str,
    mode: str,
    record_schema_version: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Schema-Lite 정보를 metadata에 부착한다.

    producer/build_id/dataset_version 등은 이미 observer.py에서 사용 중인 값들을
    표준 위치(_schema)로 한 번 더 정리해주는 역할이다.

    주의:
    - 전략/판단 관련 정보는 절대 다루지 않는다.
    - 스키마/버전/추적 정보만 다룬다.
    """
    out = ensure_namespaces(metadata)

    schema = dict(out[NS_SCHEMA])
    info = SchemaLiteInfo(version=record_schema_version or RECORD_SCHEMA_VERSION)

    # Schema-Lite 핵심 필드
    schema.setdefault("record_schema_name", info.name)
    schema["record_schema_version"] = info.version
    schema.setdefault("compat_min_version", info.compat_min)

    # 추적/운영 편의 필드(표준화)
    schema.setdefault("producer", producer)
    schema.setdefault("build_id", build_id)
    schema.setdefault("dataset_version", dataset_version)
    schema.setdefault("generated_at", generated_at)
    schema.setdefault("session_id", session_id)
    schema.setdefault("mode", mode)

    out[NS_SCHEMA] = schema
    return out
