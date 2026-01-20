#!/usr/bin/env python3
"""
Observer Docker Entry Point
Observer system with FastAPI server for monitoring and control
"""

from __future__ import annotations

import asyncio
import logging
import sys
import os
from pathlib import Path
from uuid import uuid4

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from observer.observer import Observer
from observer.event_bus import EventBus, JsonlFileSink
from observer.api_server import run_api_server, get_status_tracker
from datetime import datetime, timezone

def configure_environment():
    """Configure environment variables for Docker deployment"""
    os.environ.setdefault("OBSERVER_STANDALONE", "1")
    os.environ.setdefault("PYTHONPATH", "/app/src:/app")
    os.environ.setdefault("OBSERVER_DATA_DIR", "/app/data/observer")
    os.environ.setdefault("OBSERVER_LOG_DIR", "/app/logs")

async def run_observer_with_api():
    """Run Observer system with FastAPI server"""
    configure_environment()

    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    log = logging.getLogger("ObserverDocker")
    session_id = f"observer-{uuid4()}"

    log.info("Starting Observer Docker system with API server | session_id=%s", session_id)

    # Setup event bus with file sink
    event_bus = EventBus([
        JsonlFileSink("observer.jsonl")
    ])

    # Create observer
    observer = Observer(
        session_id=session_id,
        mode="DOCKER",
        event_bus=event_bus
    )

    # Get status tracker for monitoring
    status_tracker = get_status_tracker()

    try:
        # Start observer
        await observer.start()
        status_tracker.mark_observer_started()
        status_tracker.mark_eventbus_connected(True)

        log.info("Observer system fully operational")
        log.info("Event archive: /app/data/observer/")
        log.info("Logs: /app/logs/")
        log.info("Starting FastAPI server on 0.0.0.0:8000")

        # Start API server in background
        api_task = asyncio.create_task(run_api_server(host="0.0.0.0", port=8000))

        log.info("FastAPI server started - accessible at http://localhost:8000")
        log.info("Health check: http://localhost:8000/health")
        log.info("Status endpoint: http://localhost:8000/status")
        log.info("Metrics endpoint: http://localhost:8000/metrics")

        # Keep running
        await api_task

    except KeyboardInterrupt:
        log.info("Shutting down Observer system...")
        status_tracker.mark_observer_stopped()
    except Exception as e:
        log.error(f"Observer system error: {e}")
        status_tracker.mark_observer_stopped()
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        await observer.stop()
        log.info("Observer system stopped")

if __name__ == "__main__":
    try:
        asyncio.run(run_observer_with_api())
    except KeyboardInterrupt:
        print("\nObserver stopped by user")
    except Exception as e:
        print(f"Observer failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
