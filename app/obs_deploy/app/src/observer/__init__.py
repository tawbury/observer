"""
observer package

Observer Core - Standalone monitoring system with FastAPI API server.

This package provides:
- Core observation engine (Observer)
- Data models (ObservationSnapshot, PatternRecord)
- Event bus for data distribution
- REST API server for monitoring (FastAPI)
- Deployment modes (Docker, Kubernetes, CLI, Development)
- Status tracking and metrics collection

Public API:
- Observer: Core orchestrator class
- ObservationSnapshot: Data contract for observations
- PatternRecord: Enriched observation record
- EventBus: Event distribution system
- run_observer_with_api: Docker entry point
- DeploymentMode: Abstract deployment interface
- create_deployment_mode: Factory for deployment modes

Example:
    import asyncio
    from observer import Observer, EventBus, JsonlFileSink

    # Create event bus with file sink
    event_bus = EventBus([JsonlFileSink("observer.jsonl")])

    # Create and run observer
    observer = Observer(
        session_id="session-001",
        mode="DOCKER",
        event_bus=event_bus
    )

    asyncio.run(observer.start())
"""

from __future__ import annotations

# Core classes
from .observer import Observer
from .snapshot import (
    ObservationSnapshot,
    Meta,
    Context,
    Observation,
)
from .pattern_record import PatternRecord
from .event_bus import (
    EventBus,
    JsonlFileSink,
    SnapshotSink,
)

# Entry points
from .api_server import (
    run_api_server,
    start_api_server_background,
    ObserverStatusTracker,
)

# Deployment modes
from .deployment_mode import (
    IDeploymentMode,
    DeploymentMode,
    DeploymentModeType,
    DeploymentConfig,
    create_deployment_mode,
)

# Docker entry point
async def run_observer_with_api(
    host: str = "0.0.0.0",
    port: int = 8000,
    log_level: str = "info"
) -> None:
    """
    Run Observer with FastAPI server (Docker entry point).

    This is the main entry point for Docker container deployment.
    It starts both the Observer core and the FastAPI monitoring server.

    Args:
        host: Host to bind API server to (default: 0.0.0.0)
        port: Port to bind API server to (default: 8000)
        log_level: Logging level (default: info)

    Example:
        import asyncio
        asyncio.run(run_observer_with_api())
    """
    import os
    import logging
    from uuid import uuid4
    from datetime import datetime, timezone

    # Configure environment
    os.environ.setdefault("OBSERVER_STANDALONE", "1")
    os.environ.setdefault("PYTHONPATH", "/app/src:/app")
    os.environ.setdefault("OBSERVER_DATA_DIR", "/app/data/observer")
    os.environ.setdefault("OBSERVER_LOG_DIR", "/app/logs")

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    log = logging.getLogger("ObserverDocker")
    session_id = f"observer-{uuid4()}"

    log.info(f"Starting Observer Docker system with API server | session_id={session_id}")

    try:
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
        from .api_server import status_tracker
        status_tracker.update_state("starting", ready=False)

        # Start observer
        await observer.start()
        status_tracker.mark_observer_started()
        status_tracker.mark_eventbus_connected(True)

        log.info("Observer system fully operational")
        log.info("Event archive: /app/data/observer/")
        log.info("Logs: /app/logs/")
        log.info(f"Starting FastAPI server on {host}:{port}")

        # Start API server in background
        api_task = start_api_server_background(host=host, port=port, log_level=log_level)

        log.info(f"FastAPI server started - accessible at http://localhost:{port}")
        log.info(f"Health check: http://localhost:{port}/health")
        log.info(f"Status endpoint: http://localhost:{port}/status")
        log.info(f"Metrics endpoint: http://localhost:{port}/metrics")

        # Keep running until interrupted
        await asyncio.Event().wait()

    except KeyboardInterrupt:
        log.info("Shutting down Observer system...")
        status_tracker.mark_observer_stopped()
    except Exception as e:
        log.error(f"Observer system error: {e}")
        status_tracker.mark_observer_stopped()
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Cleanup
        try:
            await observer.stop()
        except Exception:
            pass
        log.info("Observer system stopped")


__all__ = [
    # Core classes
    "Observer",
    "ObservationSnapshot",
    "Meta",
    "Context",
    "Observation",
    "PatternRecord",
    "EventBus",
    "JsonlFileSink",
    "IEventSink",
    # Entry points
    "run_api_server",
    "start_api_server_background",
    "ObserverStatusTracker",
    "run_observer_with_api",
    # Deployment
    "IDeploymentMode",
    "DeploymentMode",
    "DeploymentModeType",
    "DeploymentConfig",
    "create_deployment_mode",
]
