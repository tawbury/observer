from __future__ import annotations

import logging
import os
from typing import Any, Optional, Type
from uuid import uuid4

from ops.runtime.phase15_current_price_source import build_phase15_source
from ops.runtime.phase15_input_bridge import Phase15InputBridge

# Phase E alignment (NO execution here)
from runtime.config.execution_mode import decide_execution_mode, ExecutionMode

log = logging.getLogger("Phase15Runner")


# ============================================================
# Bootstrap & Safety
# ============================================================

def _configure_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )


def _safety_assertions() -> None:
    """
    Phase 15: NO TRADING is strictly enforced.
    This phase is observation-only.
    """
    trading_enabled = os.getenv("TRADING_ENABLED", "false").lower().strip()
    if trading_enabled in {"1", "true", "yes", "y"}:
        raise RuntimeError(
            "Phase 15 is observation-only. "
            "TRADING_ENABLED must be false."
        )


# ============================================================
# Flexible imports (Observer / Snapshot)
# ============================================================

def _import_snapshot_cls() -> Type[Any]:
    candidates = [
        ("ops.observer.snapshot", "ObservationSnapshot"),
        ("ops.observer.core.snapshot", "ObservationSnapshot"),
        ("ops.observer.observation.snapshot", "ObservationSnapshot"),
    ]

    last_err: Optional[Exception] = None
    for module_name, cls_name in candidates:
        try:
            mod = __import__(module_name, fromlist=[cls_name])
            return getattr(mod, cls_name)
        except Exception as e:
            last_err = e

    raise RuntimeError(
        "ObservationSnapshot import failed. "
        "Adjust import candidates in phase15_runner.py"
    ) from last_err


def _import_observer() -> Type[Any]:
    candidates = [
        ("ops.observer.observer", "Observer"),
        ("ops.observer.core.observer", "Observer"),
    ]

    last_err: Optional[Exception] = None
    for module_name, cls_name in candidates:
        try:
            mod = __import__(module_name, fromlist=[cls_name])
            return getattr(mod, cls_name)
        except Exception as e:
            last_err = e

    raise RuntimeError(
        "Observer import failed. "
        "Adjust import candidates in phase15_runner.py"
    ) from last_err


# ============================================================
# Observer construction
# ============================================================

def _build_phase15_observer(ObserverCls: Type[Any]) -> Any:
    """
    Phase 15 Observer:
    - Observation only
    - EventBus with empty sinks
    """
    try:
        from ops.observer.event_bus import EventBus
    except Exception as e:
        raise RuntimeError(
            "EventBus import failed. Phase 15 requires Observer infra."
        ) from e

    session_id = f"phase15-{uuid4()}"
    mode = "phase15"

    event_bus = EventBus(sinks=[])

    return ObserverCls(
        session_id=session_id,
        mode=mode,
        event_bus=event_bus,
    )


# ============================================================
# Execution Mode Gate (Phase E aligned, Phase 15 locked)
# ============================================================

def _log_execution_mode_context() -> None:
    """
    Phase 15 does NOT execute trades.
    This function exists to align runner structure with Phase E.
    """
    sheet_mode = os.getenv("EXECUTION_MODE")          # optional / informational
    sheet_live_enabled = os.getenv("LIVE_ENABLED")    # optional / informational
    env_ack = os.getenv("QTS_LIVE_ACK")

    decision = decide_execution_mode(
        sheet_execution_mode=sheet_mode,
        sheet_live_enabled=sheet_live_enabled,
        env_live_ack=env_ack,
    )

    # Phase 15 hard override
    if decision.mode == ExecutionMode.LIVE:
        log.warning(
            "ExecutionMode=LIVE detected but overridden to PAPER (Phase 15 NO TRADING). "
            "reason=%s",
            decision.reason,
        )
    else:
        log.info(
            "ExecutionMode=PAPER (Phase 15 enforced). reason=%s",
            decision.reason,
        )


# ============================================================
# Main runner
# ============================================================

def run_phase15_current_price(symbol: str) -> None:
    _configure_logging()
    _safety_assertions()
    _log_execution_mode_context()

    SnapshotCls = _import_snapshot_cls()
    ObserverCls = _import_observer()

    observer = _build_phase15_observer(ObserverCls)

    source = build_phase15_source(symbol=symbol)
    bridge = Phase15InputBridge(snapshot_cls=SnapshotCls)

    log.info(
        "Phase 15 start | mode=current_price | symbol=%s | observation_only",
        symbol,
    )

    for ev in source.stream():
        try:
            snapshot = bridge.build_snapshot(ev)

            if hasattr(observer, "observe"):
                observer.observe(snapshot)
            elif hasattr(observer, "on_snapshot"):
                observer.on_snapshot(snapshot)
            else:
                raise RuntimeError(
                    "Observer has no known entrypoint: observe(snapshot) or on_snapshot(snapshot)"
                )

            log.info("tick received_at=%s", ev.received_at)

        except Exception:
            log.exception("Phase 15 ingest failed")
            raise


if __name__ == "__main__":
    sym = os.getenv("PHASE15_SYMBOL", "005930")
    run_phase15_current_price(symbol=sym)
