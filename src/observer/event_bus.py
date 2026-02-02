from __future__ import annotations

"""
event_bus.py

Observer-Core에서 생성된 PatternRecord를
"어디로 보낼지"를 관리하는 전달 계층(Event Bus)

초보자 가이드:
- Observer는 기록을 '직접 저장'하지 않는다.
- Observer는 EventBus에게 "이 기록을 처리해줘"라고 맡긴다.
- EventBus는 여러 Sink(출력 대상)에게 전달할 수 있다.

경로 관리 규칙:
- Observer 이벤트 로그는 '운영 자산'으로 간주된다.
- 모든 Observer JSONL 로그는 paths.py가 정의한
  canonical observer asset directory에 저장된다.
- event_bus.py는 더 이상 프로젝트 루트나
  실제 파일 시스템 구조를 추론하지 않는다.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Iterable, List, Optional

from .pattern_record import PatternRecord
from .log_rotation import RotationConfig, RotationManager, create_rotation_config, validate_rotation_config
from observer.paths import observer_asset_dir, observer_asset_file


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

    Observer / EventBus는
    Sink의 내부 구현을 알 필요가 없다.
    """

    @abstractmethod
    def publish(self, record: PatternRecord) -> None:
        """
        record 하나를 처리한다.
        구현체에서 파일 저장 / DB 저장 등을 수행한다.
        """
        raise NotImplementedError


# ============================================================
# File Sink (Append-only JSONL)
# ============================================================

class JsonlFileSink(SnapshotSink):
    """
    PatternRecord를 JSONL 형식으로 파일에 저장하는 Sink

    저장 규칙:
    - append-only (기존 내용 수정 없음)
    - 1 PatternRecord = 1 JSON line
    - 실행 위치(CWD)에 상관없이 항상 동일한 경로 사용

    경로 관리:
    - Observer 로그는 '운영 자산'이다.
    - 실제 저장 경로는 paths.py가 유일하게 결정한다.

    Time-based Rotation (Task 04):
    - rotation이 활성화된 경우, 시간 창에 따라 파일을 분할
    - 파일 이름: {base_filename}_YYYYMMDD_HHMM.jsonl
    - rotation은 append-only 정책을 유지

    출력 경로:
    config/{filename}
    """

    def __init__(
        self,
        filename: str = "observer.jsonl",
        *,
        rotation_config: Optional[RotationConfig] = None,
    ) -> None:
        """
        filename:
        - 저장할 JSONL 파일 이름 (rotation이 비활성화된 경우)
        - 예: observer.jsonl / observer_test.jsonl
        
        rotation_config:
        - 시간 기반 로테이션 설정 (선택 사항)
        - None인 경우 rotation이 비활성화됨
        """

        # --------------------------------------------------
        # 경로 관리: 경로 책임은 paths.py 단일 SSoT
        # --------------------------------------------------
        self.base_dir = observer_asset_dir()
        
        # Rotation setup
        if rotation_config is not None:
            validate_rotation_config(rotation_config)
            self._rotation_manager = RotationManager(rotation_config)
            self.file_path = self._rotation_manager.get_current_file_path()
        else:
            self._rotation_manager = None
            self.file_path = observer_asset_file(filename)

        logger.info(
            "JsonlFileSink initialized",
            extra={
                "file_path": str(self.file_path),
                "rotation_enabled": rotation_config is not None and rotation_config.enable_rotation,
                "rotation_window_ms": rotation_config.window_ms if rotation_config else None,
            },
        )

    def publish(self, record: PatternRecord) -> None:
        """
        PatternRecord 1개를 파일에 한 줄(JSON)로 저장한다.
        
        Time-based rotation이 활성화된 경우:
        - 현재 시간 창에 해당하는 파일에 기록
        - 시간 창이 변경된 경우 자동으로 새 파일로 전환
        """
        try:
            # Check if we need to rotate (only if rotation is enabled)
            if self._rotation_manager is not None:
                current_file_path = self._rotation_manager.get_current_file_path()
                if current_file_path != self.file_path:
                    self.file_path = current_file_path
            
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(
                    json.dumps(record.to_dict(), ensure_ascii=False) + "\n"
                )
        except Exception:
            # 파일 기록 실패는 Observer 전체를 멈추지 않는다.
            logger.exception(
                "JsonlFileSink publish failed",
                extra={"file_path": str(self.file_path)},
            )
    
    def get_rotation_stats(self) -> dict:
        """Get current rotation statistics for monitoring."""
        if self._rotation_manager is None:
            return {"rotation_enabled": False}
        
        return self._rotation_manager.get_rotation_stats()


# ============================================================
# Event Bus
# ============================================================

class EventBus:
    """
    EventBus

    역할:
    - Observer로부터 PatternRecord를 전달받는다.
    - 등록된 모든 Sink에게 record를 전달한다.

    장점:
    - Observer는 출력 대상(파일/DB/네트워크)을 모른다.
    - Sink를 추가해도 Observer 코드는 바뀌지 않는다.
    """

    # Log every N dispatches so Docker/monitoring can verify data flow to sinks
    _LOG_EVERY_N_DISPATCHES = 100

    def __init__(self, sinks: Iterable[SnapshotSink]) -> None:
        """
        sinks:
        - PatternRecord를 처리할 Sink들의 목록
        - 보통 1개(JsonlFileSink)만 사용
        """
        self._sinks: List[SnapshotSink] = list(sinks)
        self._dispatch_count = 0

    def dispatch(self, record: PatternRecord) -> None:
        """
        PatternRecord를 모든 Sink에 전달한다.
        """
        self._dispatch_count += 1
        n = self._dispatch_count
        for sink in self._sinks:
            try:
                sink.publish(record)
            except Exception:
                # Sink 하나의 오류가 전체 파이프라인을 깨지 않도록 보호
                logger.exception(
                    "Unexpected exception from SnapshotSink",
                    extra={"sink": sink.__class__.__name__},
                )
        # Data-flow verification: log periodically so Docker logs show EventBus -> Sink flow
        if n == 1 or n % self._LOG_EVERY_N_DISPATCHES == 0:
            sink_names = [s.__class__.__name__ for s in self._sinks]
            logger.info(
                "EventBus dispatch count=%d → sinks=%s (data flow OK)",
                n,
                sink_names,
                extra={"dispatch_count": n, "sinks": sink_names},
            )
