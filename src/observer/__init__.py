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

__version__ = "1.0.0"

import asyncio
import logging
import os
import signal
from uuid import uuid4

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
    status_tracker,
    get_status_tracker,
)

# Deployment modes
from .deployment_mode import (
    IDeploymentMode,
    DeploymentModeType,
    DeploymentConfig,
    create_deployment_mode,
)


def _configure_deployment_env() -> None:
    """Set default env for Docker/Kubernetes deployment (aligned with observer.py)."""
    os.environ.setdefault("OBSERVER_STANDALONE", "1")
    os.environ.setdefault("OBSERVER_DEPLOYMENT_MODE", "docker")
    os.environ.setdefault("TRACK_A_ENABLED", "true")
    os.environ.setdefault("TRACK_B_ENABLED", "true")


async def run_observer_with_api(
    host: str = "0.0.0.0",
    port: int = 8000,
    log_level: str = "info",
) -> None:
    """
    Run Observer with FastAPI server and async Universe/Track A/B collectors (Docker entry point).

    Starts Observer core, EventBus → JsonlFileSink, FastAPI server (thread), and optionally
    UniverseScheduler, TrackACollector, TrackBCollector as asyncio tasks when KIS credentials
    are present. API and core do not block each other.

    Args:
        host: Host to bind API server to (default: 0.0.0.0)
        port: Port to bind API server to (default: 8000)
        log_level: Logging level (default: info)
    """
    _configure_deployment_env()
    from observer.paths import load_env_by_run_mode
    env_result = load_env_by_run_mode()

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    log = logging.getLogger("ObserverDocker")
    session_id = f"observer-{uuid4()}"

    log.info("Starting Observer Docker system with API server | session_id=%s", session_id)
    log.info(
        "Environment: RUN_MODE=%s | files_loaded=%s",
        env_result["run_mode"], env_result["files_loaded"],
    )

    # Ensure log and data dirs exist (canonical paths; legacy app/observer ignored)
    from observer.paths import log_dir as get_log_dir, observer_data_dir as get_observer_data_dir
    _log_dir = get_log_dir()
    _observer_data_dir = get_observer_data_dir()
    jsonl_path = _observer_data_dir / "observer.jsonl"
    log.info("Event archive (EventBus → JsonlFileSink): %s", jsonl_path)

    event_bus = EventBus([JsonlFileSink(str(jsonl_path))])
    observer = Observer(
        session_id=session_id,
        mode="DOCKER",
        event_bus=event_bus,
    )

    status_tracker.update_state("starting", ready=False)
    observer.start()
    status_tracker.mark_observer_started()
    status_tracker.mark_eventbus_connected(True)

    # KIS credentials: ONLY os.environ is checked. .env file load status is IGNORED.
    # If KIS_APP_KEY and KIS_APP_SECRET exist in os.environ (e.g. K8s Secret env), collectors are enabled.
    kis_app_key = os.environ.get("KIS_APP_KEY") or os.environ.get("REAL_APP_KEY")
    kis_app_secret = os.environ.get("KIS_APP_SECRET") or os.environ.get("REAL_APP_SECRET")
    kis_is_virtual = os.environ.get("KIS_IS_VIRTUAL", "false").lower() in ("true", "1", "yes")
    track_a_enabled = os.environ.get("TRACK_A_ENABLED", "true").lower() in ("true", "1", "yes")
    track_b_enabled = os.environ.get("TRACK_B_ENABLED", "false").lower() in ("true", "1", "yes")

    has_creds = bool(kis_app_key and kis_app_secret)
    env_files_loaded = env_result["files_loaded"]
    if not env_files_loaded and has_creds:
        log.info(
            "No .env files loaded; KIS credentials from os.environ (K8s/direct) - collectors enabled",
        )

    universe_scheduler = None
    track_a_collector = None
    track_b_collector = None

    if has_creds:
        cred_source = "env vars (K8s/direct)" if not env_files_loaded else "env files and/or env vars"
        log.info(
            "KIS credentials found from %s - Universe Scheduler and Track A/B will be enabled",
            cred_source,
        )
        try:
            from provider import KISAuth, ProviderEngine
            from universe.universe_scheduler import UniverseScheduler, SchedulerConfig

            kis_auth = KISAuth(kis_app_key, kis_app_secret, is_virtual=kis_is_virtual)
            provider_engine = ProviderEngine(kis_auth, is_virtual=kis_is_virtual)
            scheduler_config = SchedulerConfig(
                hour=17,
                minute=5,
                min_price=4000,
                min_count=10,
                market="kr_stocks",
                anomaly_ratio=0.30,
            )
            universe_scheduler = UniverseScheduler(
                engine=provider_engine,
                config=scheduler_config,
                on_alert=lambda alert_type, data: log.warning("Universe Alert: %s | %s", alert_type, data),
            )
            log.info("Universe Scheduler configured (daily run 17:05 KST)")
        except Exception as e:
            log.error("Failed to initialize Universe Scheduler: %s", e)

        if track_a_enabled:
            try:
                from provider import KISAuth, ProviderEngine
                from collector.track_a_collector import TrackACollector, TrackAConfig

                kis_auth_a = KISAuth(kis_app_key, kis_app_secret, is_virtual=kis_is_virtual)
                provider_engine_a = ProviderEngine(kis_auth_a, is_virtual=kis_is_virtual)
                from observer.paths import config_dir as get_config_dir
                _config_dir = get_config_dir()
                universe_dir = _config_dir / "universe"
                universe_dir.mkdir(parents=True, exist_ok=True)
                track_a_config = TrackAConfig(
                    interval_minutes=5,
                    market="kr_stocks",
                    session_id=session_id,
                    mode="DOCKER",
                )
                track_a_collector = TrackACollector(
                    provider_engine_a,
                    config=track_a_config,
                    universe_dir=str(universe_dir),
                    on_error=lambda msg: log.warning("Track A Error: %s", msg),
                )
                log.info("Track A Collector configured (interval=5m, universe_dir=%s)", universe_dir)
            except Exception as e:
                log.error("Failed to initialize Track A Collector: %s", e)

        if track_b_enabled:
            try:
                from provider import KISAuth, ProviderEngine
                from collector.track_b_collector import TrackBCollector, TrackBConfig
                from trigger.trigger_engine import TriggerEngine, TriggerConfig

                kis_auth_b = KISAuth(kis_app_key, kis_app_secret, is_virtual=kis_is_virtual)
                provider_engine_b = ProviderEngine(kis_auth_b, is_virtual=kis_is_virtual)
                trigger_config = TriggerConfig(
                    volume_surge_ratio=5.0,
                    volatility_spike_threshold=0.05,
                    max_candidates=100,
                )
                trigger_engine = TriggerEngine(config=trigger_config)
                track_b_config = TrackBConfig(
                    market="kr_stocks",
                    session_id=session_id,
                    mode="DOCKER",
                    max_slots=41,
                    trigger_check_interval_seconds=30,
                )
                track_b_collector = TrackBCollector(
                    provider_engine_b,
                    trigger_engine=trigger_engine,
                    config=track_b_config,
                    on_error=lambda msg: log.warning("Track B Error: %s", msg),
                )
                log.info("Track B Collector configured (max_slots=41)")
            except Exception as e:
                log.error("Failed to initialize Track B Collector: %s", e)
    else:
        log.warning(
            "KIS_APP_KEY and KIS_APP_SECRET not in os.environ - Universe and Track A/B collectors disabled. "
            "Set them in os.environ (e.g. K8s Secret env) or .env file.",
        )

    # API server in background thread (non-blocking)
    start_api_server_background(host=host, port=port, log_level=log_level)
    log.info("FastAPI server started on %s:%s | health=%s/health | status=%s/status", host, port, host, host)

    # Async tasks: Universe + Track A/B run in same event loop (no blocking)
    shutdown = asyncio.Event()
    tasks: list[asyncio.Task] = []

    def _on_shutdown() -> None:
        shutdown.set()

    try:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, _on_shutdown)
            except NotImplementedError:
                break
    except NotImplementedError:
        signal.signal(signal.SIGINT, lambda s, f: _on_shutdown())
        try:
            signal.signal(signal.SIGTERM, lambda s, f: _on_shutdown())
        except (AttributeError, ValueError):
            pass

    if universe_scheduler:
        tasks.append(asyncio.create_task(universe_scheduler.run_forever()))
        log.info("Universe Scheduler task registered")
    if track_a_collector:
        tasks.append(asyncio.create_task(track_a_collector.start()))
        log.info("Track A Collector task registered")
    if track_b_collector:
        tasks.append(asyncio.create_task(track_b_collector.start()))
        log.info("Track B Collector task registered")

    log.info("Observer system fully operational (EventBus → JsonlFileSink; data flow logged every 100 dispatches)")

    try:
        await shutdown.wait()
    except asyncio.CancelledError:
        pass
    finally:
        log.info("Shutting down Observer system...")
        if track_b_collector:
            track_b_collector.stop()
        for t in tasks:
            t.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        observer.stop()
        status_tracker.mark_observer_stopped()
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
    "SnapshotSink",
    # Entry points
    "run_api_server",
    "start_api_server_background",
    "ObserverStatusTracker",
    "status_tracker",
    "get_status_tracker",
    "run_observer_with_api",
    # Deployment
    "IDeploymentMode",
    "DeploymentType",
    "DeploymentConfig",
    "create_deployment_mode",
    "DeploymentModeType",
]
