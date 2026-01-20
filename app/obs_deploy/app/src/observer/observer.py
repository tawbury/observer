from __future__ import annotations

"""
observer.py

QTS-Observer-Core의 메인 오케스트레이터(중앙 제어 클래스)

현재 구현:
- Validation Layer: 데이터 유효성 검증
- Guard Layer: 안전 장치 및 제약 조건 검사
- PatternRecord Enrichment: 기록 보강
  - Schema Auto Lite (record schema versioning + namespace)
  - Quality Tagging
  - Interpretation Metadata

원칙:
- 전략 계산, 매매 판단, 실행은 절대 여기서 하지 않는다.
- Snapshot을 받아 → Validation → Guard → Record → Enrich → EventBus 로 전달한다.
"""

import logging
from datetime import datetime, timezone

from .snapshot import ObservationSnapshot
from .pattern_record import PatternRecord
from .event_bus import EventBus
from .performance_metrics import get_metrics, LatencyTimer

# Validation and Guard layers
from .validation import DefaultSnapshotValidator, SnapshotValidator
from .guard import DefaultGuard

# Record enrichment
from .phase4_enricher import DefaultRecordEnricher, RecordEnricher


class Observer:
    """
    QTS-Observer-Core Orchestrator

    역할:
    - ObservationSnapshot 수신
    - Validation → Guard
    - PatternRecord 생성
    - Record Enrichment (메타데이터 보강)
    - EventBus dispatch

    절대 하지 않는 것:
    - 매수/매도 판단
    - 전략 계산
    - 주문 실행
    """

    def __init__(
        self,
        *,
        session_id: str,
        mode: str,
        event_bus: EventBus,
        validator: SnapshotValidator | None = None,
        guard: DefaultGuard | None = None,
        enricher: RecordEnricher | None = None,  # Record enrichment hook
    ) -> None:
        self._log = logging.getLogger("Observer")
        self._running = False

        self.session_id = session_id
        self.mode = mode
        self._event_bus = event_bus

        # Validation and Guard defaults
        self._validator = validator or DefaultSnapshotValidator()
        self._guard = guard or DefaultGuard()

        # Record enrichment defaults
        # - None이면 기본 Enricher를 사용한다.
        # - 향후 다른 Enricher로 교체 가능.
        self._enricher = enricher or DefaultRecordEnricher(
            producer="observer_core",
            build_id="observer_core_v1",
            dataset_version="v1.0.0",
        )

    # ==================================================
    # Lifecycle Control
    # ==================================================

    def start(self) -> None:
        self._running = True
        self._log.info("Observer-Core started")

    def stop(self) -> None:
        self._running = False
        self._log.info("Observer-Core stopped")

    # ==================================================
    # Core Entry Point
    # ==================================================

    def on_snapshot(self, snapshot: ObservationSnapshot) -> None:
        """
        Phase 4 호출 흐름:
        1) Snapshot 수신
        2) Validation
        3) Guard
        4) PatternRecord 생성
        5) (Phase 4) Enrich
        6) EventBus dispatch
        """

        with LatencyTimer("snapshot_processing"):
            if not self._running:
                self._log.debug("Observer is not running. Snapshot ignored.")
                return

            # Record performance metrics (Task 06)
            # SAFETY: Metrics are purely observational, do NOT affect behavior
            get_metrics().increment_counter("snapshots_received")

            # --------------------------------------------------
            # Validation
            # --------------------------------------------------
            with LatencyTimer("validation"):
                v = self._validator.validate(snapshot)
            
            if not v.is_valid:
                # Record performance metrics (Task 06)
                # SAFETY: Metrics are purely observational, do NOT affect behavior
                get_metrics().increment_counter("snapshots_blocked_validation")
                self._log.warning(
                    "Snapshot validation failed (blocked)",
                    extra={
                        "session_id": self.session_id,
                        "run_id": snapshot.meta.run_id,
                        "severity": v.severity,
                        "errors": v.errors[:10],
                    },
                )
                return

            # --------------------------------------------------
            # Guard
            # --------------------------------------------------
            with LatencyTimer("guard"):
                g = self._guard.decide(snapshot, v)
            
            if not g.allow:
                # Record performance metrics (Task 06)
                # SAFETY: Metrics are purely observational, do NOT affect behavior
                get_metrics().increment_counter("snapshots_blocked_guard")
                self._log.warning(
                    "Snapshot guard blocked",
                    extra={
                        "session_id": self.session_id,
                        "run_id": snapshot.meta.run_id,
                        "action": g.action,
                        "reason": g.reason,
                    },
                )
                return

            # --------------------------------------------------
            # PatternRecord 생성 (Phase 3 기준)
            # --------------------------------------------------
            with LatencyTimer("record_creation"):
                record = PatternRecord(
                    snapshot=snapshot,
                    regime_tags={},
                    condition_tags=[],
                    outcome_labels={},
                    metadata={
                        # 기존 메타 유지(Phase 3까지의 계약)
                        "schema_version": "v1.0.0",
                        "dataset_version": "v1.0.0",
                        "build_id": "observer_core_v1",
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "session_id": self.session_id,
                        "mode": self.mode,

                        # Phase 3 — always-present quality metadata (legacy)
                        "quality_flags": [],

                        "validation": {
                            "severity": v.severity
                        },
                        "guard": {
                            "action": g.action,
                            "reason": g.reason,
                        },
                    },
                )

            # --------------------------------------------------
            # (Phase 4) Record Enrichment
            # --------------------------------------------------
            # - 판단/전략/실행 금지
            # - metadata 네임스페이스(_schema/_quality/_interpretation)만 추가
            with LatencyTimer("enrichment"):
                record = self._enricher.enrich(record)

            # --------------------------------------------------
            # Dispatch
            # --------------------------------------------------
            with LatencyTimer("dispatch"):
                self._event_bus.dispatch(record)

            # Record successful processing metrics
            # SAFETY: Metrics are purely observational, do NOT affect behavior
            get_metrics().increment_counter("snapshots_processed")
            
            self._log.info(
                "PatternRecord dispatched",
                extra={"session_id": self.session_id},
            )
