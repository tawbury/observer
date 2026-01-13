
from __future__ import annotations

import time
import sys
import logging
from uuid import uuid4

def _configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

def run_observer():
    _configure_logging()
    log = logging.getLogger("ObserverRunner")
    
    session_id = f"observer-{uuid4()}"
    
    log.info("Observer started | session_id=%s", session_id)
    log.info("Observer running in standalone mode")
    log.info("Waiting for events... (Ctrl+C to stop)")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Observer stopped")

if __name__ == "__main__":
    run_observer()
