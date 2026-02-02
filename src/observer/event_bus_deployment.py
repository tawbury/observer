from __future__ import annotations

"""
event_bus_deployment.py

Deployment version of EventBus for /app/ops structure.

This version uses deployment-specific paths instead of project root paths.py
to enable standalone deployment.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Iterable, List, Optional

from .pattern_record import PatternRecord
from .log_rotation import RotationConfig, RotationManager, create_rotation_config, validate_rotation_config
from .deployment_paths import observer_asset_dir, observer_asset_file


logger = logging.getLogger(__name__)


# ============================================================
# Sink Interface
# ============================================================

class SnapshotSink(ABC):
    """
    SnapshotSink 인터페이스

    역할:
    - PatternRecord를 받아서 "어딘가에 저장하거나 전달"한다.

    예시:
    - JsonlFileSink  → 파일에 저장
    - DbSink         → DB에 저장 (미래)
    - ApiSink        → 외부 API 전송 (미래)
    """

    @abstractmethod
    def write(self, record: PatternRecord) -> None:
        """PatternRecord를 저장/전달한다."""
        pass

    @abstractmethod
    def flush(self) -> None:
        """버퍼가 있다면 강제로 flush한다."""
        pass


# ============================================================
# File Sink Implementation
# ============================================================

class JsonlFileSink(SnapshotSink):
    """
    JSONL 파일 기반 Sink

    역할:
    - PatternRecord를 JSONL 형식으로 파일에 저장
    - RotationManager를 통해 로테이션 지원
    """

    def __init__(
        self,
        filename: str = "observer.jsonl",
        rotation_config: Optional[RotationConfig] = None,
        enable_rotation: bool = True,
    ):
        self.filename = filename
        self.rotation_config = rotation_config or create_rotation_config()
        self.enable_rotation = enable_rotation

        # Deployment-specific path resolution
        self.file_path = observer_asset_file(filename)
        self.rotation_manager = RotationManager(
            self.file_path, self.rotation_config, enable_rotation
        )

        # Ensure directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info("JsonlFileSink initialized: %s", self.file_path)

    def write(self, record: PatternRecord) -> None:
        """PatternRecord를 JSONL 파일에 쓴다."""
        try:
            # Rotation check before write
            if self.enable_rotation:
                self.rotation_manager.check_and_rotate()

            # Write record
            line = json.dumps(record.to_dict(), ensure_ascii=False, separators=(",", ":"))
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

            logger.debug("Record written to %s", self.file_path)

        except Exception as e:
            logger.error("Failed to write record to %s: %s", self.file_path, e)
            raise

    def flush(self) -> None:
        """파일 flush (JSONL은 즉시 쓰기라 noop)"""
        pass


# ============================================================
# Event Bus Implementation
# ============================================================

class EventBus:
    """
    Observer-Core Event Bus

    역할:
    - PatternRecord를 여러 Sink에게 fan-out 전달
    - 개별 Sink 실패를 전체 시스템에서 격리
    - Sink 등록/해지 관리

    특징:
    - Observer는 EventBus를 통해 "기록 요청"을 한다
    - Observer는 직접 저장하지 않는다 (책임 분리)
    - 실패 격리: 한 Sink가 실패해도 다른 Sink는 계속 동작
    """

    def __init__(self, sinks: Optional[Iterable[SnapshotSink]] = None):
        """
        EventBus 초기화

        Args:
            sinks: 초기 Sink 목록 (선택사항)
        """
        self._sinks: List[SnapshotSink] = list(sinks) if sinks else []
        self._log = logging.getLogger("EventBus")

        self._log.info("EventBus initialized with %d sinks", len(self._sinks))

    def add_sink(self, sink: SnapshotSink) -> None:
        """Sink를 추가한다."""
        self._sinks.append(sink)
        self._log.info("Sink added: %s", type(sink).__name__)

    def remove_sink(self, sink: SnapshotSink) -> None:
        """Sink를 제거한다."""
        try:
            self._sinks.remove(sink)
            self._log.info("Sink removed: %s", type(sink).__name__)
        except ValueError:
            self._log.warning("Sink not found for removal: %s", type(sink).__name__)

    def dispatch(self, record: PatternRecord) -> None:
        """
        PatternRecord를 모든 등록된 Sink에게 전달한다.

        실패 격리:
        - 한 Sink에서 예외가 발생해도 다른 Sink는 계속 동작
        - 실패는 로깅만 하고 전체 흐름은 중단하지 않음
        """
        if not self._sinks:
            self._log.warning("No sinks registered, record dropped")
            return

        failures = []
        for sink in self._sinks:
            try:
                sink.write(record)
            except Exception as e:
                failures.append((type(sink).__name__, e))
                self._log.error("Sink %s failed: %s", type(sink).__name__, e)

        if failures:
            self._log.error(
                "Dispatch completed with %d failures: %s",
                len(failures),
                [(name, str(err)) for name, err in failures],
            )

    def flush_all(self) -> None:
        """모든 Sink를 flush한다."""
        for sink in self._sinks:
            try:
                sink.flush()
            except Exception as e:
                self._log.error("Failed to flush sink %s: %s", type(sink).__name__, e)

    def get_sink_count(self) -> int:
        """등록된 Sink 수를 반환한다."""
        return len(self._sinks)


# ============================================================
# Factory Functions
# ============================================================

def create_default_event_bus(
    filename: str = "observer.jsonl",
    enable_rotation: bool = True,
    rotation_config: Optional[RotationConfig] = None,
) -> EventBus:
    """
    기본 EventBus를 생성한다.

    Args:
        filename: JSONL 파일 이름
        enable_rotation: 로테이션 활성화 여부
        rotation_config: 로테이션 설정 (선택사항)

    Returns:
        EventBus 인스턴스
    """
    sink = JsonlFileSink(
        filename=filename,
        enable_rotation=enable_rotation,
        rotation_config=rotation_config,
    )
    return EventBus([sink])


def create_multi_sink_event_bus(
    sinks: List[SnapshotSink],
) -> EventBus:
    """
    여러 Sink를 사용하는 EventBus를 생성한다.

    Args:
        sinks: Sink 목록

    Returns:
        EventBus 인스턴스
    """
    return EventBus(sinks)
