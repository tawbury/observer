#!/usr/bin/env python3
"""
Observer Docker Entry Point

Standalone Observer system with FastAPI server for monitoring and control.
This is the main entry point for Docker container deployment.
"""

from __future__ import annotations

import logging
import sys
import os
import signal
import threading
from pathlib import Path
from uuid import uuid4

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from observer.observer import Observer
from observer.event_bus import EventBus, JsonlFileSink
from observer.api_server import start_api_server_background, get_status_tracker
from datetime import datetime, timezone

def configure_environment():
    """Configure environment variables for Docker deployment"""
    os.environ.setdefault("OBSERVER_STANDALONE", "1")
    os.environ.setdefault("PYTHONPATH", "/app/src:/app")
    os.environ.setdefault("OBSERVER_DATA_DIR", "/app/data/observer")
    os.environ.setdefault("OBSERVER_LOG_DIR", "/app/logs")
    # For backward compatibility with deployment paths module
    os.environ.setdefault("OBSERVER_DEPLOYMENT_MODE", "docker")

def run_observer_with_api():
    """Run Observer system with FastAPI server"""
    configure_environment()

    # Ensure log directory exists
    log_dir = Path(os.environ.get("OBSERVER_LOG_DIR", "/app/logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    system_log_dir = log_dir / "system"
    system_log_dir.mkdir(parents=True, exist_ok=True)

    # Setup logging with both console and file outputs
    log_file = system_log_dir / "observer.log"
    
    # Configure logging with flushing enabled
    file_handler = logging.FileHandler(str(log_file), mode='a')
    file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    file_handler.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    console_handler.setLevel(logging.INFO)
    
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler],
        force=True
    )

    log = logging.getLogger("ObserverDocker")
    session_id = f"observer-{uuid4()}"

    log.info("Starting Observer Docker system with API server | session_id=%s", session_id)

    # Setup event bus with file sink
    observer_data_dir = Path(os.environ.get("OBSERVER_DATA_DIR", "/app/data/observer"))
    observer_data_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = observer_data_dir / "observer.jsonl"
    
    log.info("Event archive will be saved to: %s", jsonl_path)
    
    event_bus = EventBus([
        JsonlFileSink(str(jsonl_path))
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
        observer.start()
        status_tracker.update_state("running", ready=True)

        log.info("Observer system fully operational")
        log.info("Event archive: %s", observer_data_dir)
        log.info("Logs: %s", log_dir)
        log.info("Log file: %s", log_file)
        log.info("Starting FastAPI server on 0.0.0.0:8000")

        # Start API server in background thread
        api_thread = start_api_server_background(host="0.0.0.0", port=8000)

        log.info("FastAPI server started - accessible at http://localhost:8000")
        log.info("Health check: http://localhost:8000/health")
        log.info("Status endpoint: http://localhost:8000/status")
        log.info("Metrics endpoint: http://localhost:8000/metrics")

        # Setup signal handlers for graceful shutdown
        def signal_handler(sig, frame):
            log.info("Received shutdown signal, stopping Observer system...")
            status_tracker.update_state("stopping")
            observer.stop()
            status_tracker.update_state("stopped", ready=False)
            log.info("Observer system stopped")
            # Flush all logging handlers
            for handler in logging.root.handlers:
                handler.flush()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Keep main thread alive - wait for API thread
        api_thread.join()

    except KeyboardInterrupt:
        log.info("Shutting down Observer system...")
        status_tracker.update_state("stopping")
    except Exception as e:
        log.error(f"Observer system error: {e}")
        status_tracker.update_state("error")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        observer.stop()
        status_tracker.update_state("stopped", ready=False)
        log.info("Observer system stopped")
        # Ensure all logs are written
        for handler in logging.root.handlers:
            handler.flush()
            if hasattr(handler, 'close'):
                handler.close()

if __name__ == "__main__":
    try:
        run_observer_with_api()
    except KeyboardInterrupt:
        print("\nObserver stopped by user")
    except Exception as e:
        print(f"Observer failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
