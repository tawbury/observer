import time
# observer.py
from __future__ import annotations

import sys
import logging
from pathlib import Path
from uuid import uuid4

# ============================================================
# Ensure src/ is on sys.path
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# ============================================================
# Imports
# ============================================================

def _import_observer_cls():
    candidates = [
        ("ops.observer.observer", "Observer"),
        ("ops.observer.core.observer", "Observer"),
    ]
    last_err = None
    for module_name, cls_name in candidates:
        try:
            mod = __import__(module_name, fromlist=[cls_name])
            return getattr(mod, cls_name)
        except Exception as e:
            last_err = e
    raise RuntimeError("Observer class import failed") from last_err


def _import_event_bus_and_sink():
    try:
        from ops.observer.event_bus import EventBus, JsonlFileSink
        return EventBus, JsonlFileSink
    except Exception as e:
        raise RuntimeError("EventBus / JsonlFileSink import failed") from e


# ============================================================
# Logging
# ============================================================

def _configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


# ============================================================
# Observer Runner
# ============================================================

def run_observer():
    _configure_logging()
    log = logging.getLogger("ObserverRunner")

    ObserverCls = _import_observer_cls()
    EventBusCls, JsonlFileSinkCls = _import_event_bus_and_sink()

    session_id = f"observer-{uuid4()}"
    mode = "observer-only"

    # ✅ Phase E: 실제 파일 sink 사용
    sink = JsonlFileSinkCls(filename="observer.jsonl")
    event_bus = EventBusCls(sinks=[sink])

    observer = ObserverCls(
        session_id=session_id,
        mode=mode,
        event_bus=event_bus,
    )

    log.info("Observer started | session_id=%s", session_id)
    log.info("Writing to data/observer/observer.jsonl")
    log.info("Waiting for events... (Ctrl+C to stop)")

    # Prevent busy-loop: sleep when idle (no input)
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        log.info("Observer stopped")


# ============================================================
# Entrypoint
# ============================================================

if __name__ == "__main__":
    run_observer()
