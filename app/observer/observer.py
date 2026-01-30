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
import time
from pathlib import Path
from uuid import uuid4

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from observer.observer import Observer
from observer.event_bus import EventBus, JsonlFileSink
from observer.api_server import start_api_server_background, get_status_tracker
from universe.universe_scheduler import UniverseScheduler, SchedulerConfig
from provider import KISAuth, ProviderEngine
from collector.track_a_collector import TrackACollector, TrackAConfig
from collector.track_b_collector import TrackBCollector, TrackBConfig
from trigger.trigger_engine import TriggerEngine, TriggerConfig
from slot.slot_manager import SlotManager
from datetime import datetime, timezone
import asyncio

def configure_environment():
    """Set default environment variables for Docker deployment (no .env load here)."""
    os.environ.setdefault("OBSERVER_STANDALONE", "1")
    os.environ.setdefault("PYTHONPATH", "/app/src:/app")
    os.environ.setdefault("OBSERVER_DATA_DIR", "/app/data/observer")
    os.environ.setdefault("OBSERVER_LOG_DIR", "/app/logs")
    os.environ.setdefault("OBSERVER_DEPLOYMENT_MODE", "docker")
    os.environ.setdefault("TRACK_A_ENABLED", "true")
    os.environ.setdefault("TRACK_B_ENABLED", "true")


def _resolve_env_file_paths():
    """
    Resolve .env path(s): OBSERVER_ENV_FILE first, then Docker defaults (/app/secrets/.env, /app/.env), else local.
    Returns (paths_attempted, path_loaded). Uses load_dotenv(override=False) so system env wins.
    """
    paths_attempted = []
    path_loaded = None
    explicit = os.environ.get("OBSERVER_ENV_FILE")
    if explicit:
        p = Path(explicit).resolve()
        paths_attempted.append(p)
        if p.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(p, override=False)
                path_loaded = p
            except ImportError:
                pass
            except Exception:
                pass
        return (paths_attempted, path_loaded)
    if os.environ.get("OBSERVER_STANDALONE") == "1" or Path("/app").exists():
        for candidate in [Path("/app/secrets/.env"), Path("/app/.env")]:
            paths_attempted.append(candidate)
            if candidate.exists() and path_loaded is None:
                try:
                    from dotenv import load_dotenv
                    load_dotenv(candidate, override=False)
                    path_loaded = candidate
                except ImportError:
                    pass
                except Exception:
                    pass
        return (paths_attempted, path_loaded)
    local_root = Path(__file__).resolve().parent
    for candidate in [local_root / ".env", local_root / "secrets" / ".env"]:
        paths_attempted.append(candidate)
        if candidate.exists() and path_loaded is None:
            try:
                from dotenv import load_dotenv
                load_dotenv(candidate, override=False)
                path_loaded = candidate
            except ImportError:
                pass
            except Exception:
                pass
    return (paths_attempted, path_loaded)


def run_observer_with_api():
    """Run Observer system with FastAPI server and Universe Scheduler"""
    configure_environment()
    env_paths_attempted, env_path_loaded = _resolve_env_file_paths()

    # Ensure log directory exists
    log_dir = Path(os.environ.get("OBSERVER_LOG_DIR", "/app/logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    system_log_dir = log_dir / "system"
    system_log_dir.mkdir(parents=True, exist_ok=True)

    # Setup logging with both console and file outputs
    # HourlyRotatingFileHandler로 정각 기준 시간별 로테이션
    from shared.hourly_handler import HourlyRotatingFileHandler
    
    # Configure logging with hourly rotation (정각 기준)
    # 파일명 형식: YYYYMMDD_HH.log
    file_handler = HourlyRotatingFileHandler(system_log_dir)
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
    if env_path_loaded:
        log.info("Env file loaded from: %s (absolute)", env_path_loaded.resolve())
    else:
        log.info(
            "Env file not loaded; paths attempted (absolute): %s; OBSERVER_ENV_FILE=%s",
            [str(p.resolve()) for p in env_paths_attempted],
            os.environ.get("OBSERVER_ENV_FILE", "(not set)"),
        )

    # Setup KIS credentials for Universe Scheduler
    kis_app_key = os.environ.get("KIS_APP_KEY")
    kis_app_secret = os.environ.get("KIS_APP_SECRET")
    kis_is_virtual = os.environ.get("KIS_IS_VIRTUAL", "false").lower() in ("true", "1", "yes")
    
    universe_scheduler = None
    if kis_app_key and kis_app_secret:
        log.info("KIS credentials found - Universe Scheduler will be enabled")
        try:
            kis_auth = KISAuth(kis_app_key, kis_app_secret, is_virtual=kis_is_virtual)
            provider_engine = ProviderEngine(kis_auth, is_virtual=kis_is_virtual)
            
            scheduler_config = SchedulerConfig(
                hour=17,  # TEMPORARY TEST: Changed from 16:05 to 17:00 KST for E2E validation
                minute=5,  # Next run at 17:05
                min_price=4000,
                min_count=10,  # TEMPORARY TEST: Lowered from 100 to allow fallback symbols
                market="kr_stocks",
                anomaly_ratio=0.30
            )
            
            universe_scheduler = UniverseScheduler(
                engine=provider_engine,
                config=scheduler_config,
                on_alert=lambda alert_type, data: log.warning(
                    f"Universe Alert: {alert_type} | {data}"
                )
            )
            log.info("Universe Scheduler configured: daily run at 16:05 KST")
        except Exception as e:
            log.error(f"Failed to initialize Universe Scheduler: {e}")
    else:
        log.warning(
            "KIS_APP_KEY/SECRET not set - Universe Scheduler disabled. "
            "Env file paths attempted (absolute): %s; loaded from: %s; OBSERVER_ENV_FILE=%s",
            [str(p.resolve()) for p in env_paths_attempted],
            str(env_path_loaded.resolve()) if env_path_loaded else "none",
            os.environ.get("OBSERVER_ENV_FILE", "(not set)"),
        )

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

    # Start Universe Scheduler in background if enabled
    scheduler_task = None
    if universe_scheduler:
        def run_scheduler_async():
            """Run scheduler in asyncio event loop"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                log.info("Starting Universe Scheduler background task...")
                loop.run_until_complete(universe_scheduler.run_forever())
            except Exception as e:
                log.error(f"Universe Scheduler error: {e}")
            finally:
                loop.close()
        
        scheduler_thread = threading.Thread(target=run_scheduler_async, daemon=True)
        scheduler_thread.start()
        log.info("Universe Scheduler thread started")

    # Start Track A Collector in background if enabled
    track_a_collector = None
    track_a_enabled = os.environ.get("TRACK_A_ENABLED", "true").lower() in ("true", "1", "yes")
    if track_a_enabled and kis_app_key and kis_app_secret:
        log.info("Track A Collector will be enabled")
        try:
            kis_auth_a = KISAuth(kis_app_key, kis_app_secret, is_virtual=kis_is_virtual)
            provider_engine_a = ProviderEngine(kis_auth_a, is_virtual=kis_is_virtual)
            
            # Use environment variable for config path (production parity)
            config_dir = Path(os.environ.get("OBSERVER_CONFIG_DIR", "/app/config"))
            universe_dir = config_dir / "universe"
            universe_dir.mkdir(parents=True, exist_ok=True)
            
            track_a_config = TrackAConfig(
                interval_minutes=5,
                market="kr_stocks",
                session_id=session_id,
                mode="DOCKER"
            )
            
            track_a_collector = TrackACollector(
                provider_engine_a,
                config=track_a_config,
                universe_dir=str(universe_dir),
                on_error=lambda msg: log.warning(f"Track A Error: {msg}")
            )
            log.info("Track A Collector configured: 5-minute interval (universe_dir=%s)", universe_dir)
        except Exception as e:
            log.error(f"Failed to initialize Track A Collector: {e}")
    else:
        log.info("Track A Collector disabled (TRACK_A_ENABLED=false or KIS credentials missing)")

    # Start Track B Collector in background if enabled
    track_b_collector = None
    track_b_enabled = os.environ.get("TRACK_B_ENABLED", "false").lower() in ("true", "1", "yes")
    if track_b_enabled and kis_app_key and kis_app_secret:
        log.info("Track B Collector will be enabled")
        try:
            kis_auth_b = KISAuth(kis_app_key, kis_app_secret, is_virtual=kis_is_virtual)
            provider_engine_b = ProviderEngine(kis_auth_b, is_virtual=kis_is_virtual)
            
            trigger_config = TriggerConfig(
                volume_surge_ratio=5.0,
                volatility_spike_threshold=0.05,
                max_candidates=100
            )
            trigger_engine = TriggerEngine(config=trigger_config)
            
            track_b_config = TrackBConfig(
                market="kr_stocks",
                session_id=session_id,
                mode="DOCKER",
                max_slots=41,
                trigger_check_interval_seconds=30
            )
            
            track_b_collector = TrackBCollector(
                provider_engine_b,
                trigger_engine=trigger_engine,
                config=track_b_config,
                on_error=lambda msg: log.warning(f"Track B Error: {msg}")
            )
            log.info("Track B Collector configured: WebSocket real-time (41 slots)")
        except Exception as e:
            log.error(f"Failed to initialize Track B Collector: {e}")
    else:
        if not track_b_enabled:
            log.info("Track B Collector disabled (TRACK_B_ENABLED=false)")
        else:
            log.info("Track B Collector disabled (KIS credentials missing)")

    try:
        # Start observer
        observer.start()
        status_tracker.update_state("running", ready=True)

        log.info("Observer system fully operational")
        log.info("Event archive: %s", observer_data_dir)
        log.info("Logs: %s", log_dir)
        log.info("Starting FastAPI server on 0.0.0.0:8000")

        # Start Track A Collector in background thread
        track_a_thread = None
        if track_a_collector:
            def run_track_a_async():
                """Run Track A in asyncio event loop"""
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    log.info("Starting Track A Collector background task...")
                    loop.run_until_complete(track_a_collector.start())
                except Exception as e:
                    log.error(f"Track A Collector error: {e}")
                finally:
                    loop.close()
            
            track_a_thread = threading.Thread(target=run_track_a_async, daemon=True)
            track_a_thread.start()
            log.info("Track A Collector thread started")

        # Start Track B Collector in background thread
        track_b_thread = None
        if track_b_collector:
            def run_track_b_async():
                """Run Track B in asyncio event loop"""
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    log.info("Starting Track B Collector background task...")
                    loop.run_until_complete(track_b_collector.start())
                except Exception as e:
                    log.error(f"Track B Collector error: {e}")
                finally:
                    loop.close()
            
            track_b_thread = threading.Thread(target=run_track_b_async, daemon=True)
            track_b_thread.start()
            log.info("Track B Collector thread started")

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
            if track_a_collector:
                log.info("Stopping Track A Collector...")
            if track_b_collector:
                log.info("Stopping Track B Collector...")
                track_b_collector.stop()
            observer.stop()
            status_tracker.update_state("stopped", ready=False)
            log.info("Observer system stopped")
            # Flush all logging handlers
            for handler in logging.root.handlers:
                handler.flush()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Keep main thread alive - infinite wait
        # API server runs in daemon thread, so we need to keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            signal_handler(signal.SIGINT, None)

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
