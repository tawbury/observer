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

# Add src (parent of observer package) to Python path
_src_root = Path(__file__).resolve().parent.parent
if str(_src_root) not in sys.path:
    sys.path.insert(0, str(_src_root))

from observer.observer import Observer
from observer.event_bus import EventBus, JsonlFileSink
from observer.api_server import start_api_server_background, get_status_tracker
from observer.paths import log_dir, system_log_dir, observer_data_dir, validate_execution_contract
from universe.universe_scheduler import UniverseScheduler, SchedulerConfig
from provider import KISAuth, ProviderEngine, KISRestProvider, RateLimiter
from collector.swing_collector import SwingCollector, SwingConfig
from collector.scalp_collector import ScalpCollector, ScalpConfig
from trigger.trigger_engine import TriggerEngine, TriggerConfig
from slot.slot_manager import SlotManager
from datetime import datetime, timezone
import asyncio

def configure_environment():
    """Load env files via RUN_MODE and set deployment defaults."""
    from observer.paths import load_env_by_run_mode
    load_env_by_run_mode()
    os.environ.setdefault("OBSERVER_STANDALONE", "1")
    os.environ.setdefault("OBSERVER_DEPLOYMENT_MODE", "docker")
    os.environ.setdefault("TRACK_A_ENABLED", "true")
    os.environ.setdefault("TRACK_B_ENABLED", "true")


def run_observer_with_api():
    """Run Observer system with FastAPI server and Universe Scheduler"""
    configure_environment()

    # Ensure log directory exists (canonical: project_root/logs, legacy app/observer ignored)
    _log_dir = log_dir()
    _system_log_dir = system_log_dir()

    # Setup logging with both console and file outputs
    # HourlyRotatingFileHandler로 정각 기준 시간별 로테이션
    from shared.hourly_handler import HourlyRotatingFileHandler

    # Configure logging with hourly rotation (정각 기준)
    # 파일명 형식: YYYYMMDD_HH.log
    file_handler = HourlyRotatingFileHandler(_system_log_dir)
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

    # Validate execution contract (logging is ready, fatal errors will be recorded)
    validate_execution_contract()

    log.info("Starting Observer Docker system with API server | session_id=%s", session_id)

    # KIS credentials: ONLY os.environ is checked. .env file load status is IGNORED.
    # If KIS_APP_KEY and KIS_APP_SECRET exist in os.environ (e.g. K8s Secret env), collectors are enabled.
    kis_app_key = os.environ.get("KIS_APP_KEY") or os.environ.get("REAL_APP_KEY")
    kis_app_secret = os.environ.get("KIS_APP_SECRET") or os.environ.get("REAL_APP_SECRET")
    kis_is_virtual = os.environ.get("KIS_IS_VIRTUAL", "false").lower() in ("true", "1", "yes")

    has_creds = bool(kis_app_key and kis_app_secret)

    # Create shared rate limiter for all KIS API calls
    # 15 req/sec = 75% of official 20 req/sec limit (safe margin for sustained minute handling)
    # 15 * 60 = 900 req/min (Under 1000 req/min limit)
    shared_rate_limiter = RateLimiter(requests_per_second=15, requests_per_minute=900) if has_creds else None
    if shared_rate_limiter:
        log.info("Shared RateLimiter created: 15 req/sec (Strict Pacing), 900 req/min")

    universe_scheduler = None
    if has_creds:
        cred_source = "environment variables"
        log.info("KIS credentials found from %s - Universe Scheduler will be enabled", cred_source)
        try:
            kis_auth = KISAuth(kis_app_key, kis_app_secret, is_virtual=kis_is_virtual)
            kis_rest = KISRestProvider(kis_auth, rate_limiter=shared_rate_limiter)
            provider_engine = ProviderEngine(kis_auth, rest_provider=kis_rest, is_virtual=kis_is_virtual)
            
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
            "KIS_APP_KEY and KIS_APP_SECRET not in os.environ - Universe Scheduler disabled. "
            "Set them in os.environ (e.g. K8s Secret env) or .env file.",
        )

    # Setup event bus with file sink
    observer_data_dir = observer_data_dir()
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

    # Start scalp Collector in background if enabled
    swing_collector = None
    track_a_enabled = os.environ.get("TRACK_A_ENABLED", "true").lower() in ("true", "1", "yes")
    if track_a_enabled and kis_app_key and kis_app_secret:
        log.info("Swing Collector will be enabled")
        try:
            kis_auth_a = KISAuth(kis_app_key, kis_app_secret, is_virtual=kis_is_virtual)
            kis_rest_a = KISRestProvider(kis_auth_a, rate_limiter=shared_rate_limiter)
            provider_engine_a = ProviderEngine(kis_auth_a, rest_provider=kis_rest_a, is_virtual=kis_is_virtual)
            
            # Use canonical config_dir from paths utility
            from observer.paths import config_dir as get_config_dir
            _config_dir = get_config_dir()
            universe_dir = _config_dir / "universe"
            # NOTE: Directory creation is handled by K8s initContainer
            # App does NOT create directories - only validates existence
            
            track_a_config = SwingConfig(
                interval_minutes=5,
                market="kr_stocks",
                session_id=session_id,
                mode="DOCKER"
            )
            
            swing_collector = SwingCollector(
                provider_engine_a,
                config=track_a_config,
                universe_dir=str(universe_dir),
                on_error=lambda msg: log.warning(f"Swing Error: {msg}")
            )
            log.info("Swing Collector configured: 5-minute interval (universe_dir=%s)", universe_dir)
        except Exception as e:
            log.error(f"Failed to initialize Swing Collector: {e}")
    else:
        log.info("Swing Collector disabled (TRACK_A_ENABLED=false or KIS credentials missing)")

    # Start Scalp Collector in background if enabled
    scalp_collector = None
    track_b_enabled = os.environ.get("TRACK_B_ENABLED", "false").lower() in ("true", "1", "yes")
    if track_b_enabled and kis_app_key and kis_app_secret:
        log.info("Scalp Collector will be enabled")
        try:
            kis_auth_b = KISAuth(kis_app_key, kis_app_secret, is_virtual=kis_is_virtual)
            kis_rest_b = KISRestProvider(kis_auth_b, rate_limiter=shared_rate_limiter)
            provider_engine_b = ProviderEngine(kis_auth_b, rest_provider=kis_rest_b, is_virtual=kis_is_virtual)
            
            trigger_config = TriggerConfig(
                volume_surge_ratio=5.0,
                volatility_spike_threshold=0.05,
                max_candidates=100
            )
            trigger_engine = TriggerEngine(config=trigger_config)
            
            track_b_config = ScalpConfig(
                market="kr_stocks",
                session_id=session_id,
                mode="DOCKER",
                max_slots=41,
                trigger_check_interval_seconds=30
            )
            
            scalp_collector = ScalpCollector(
                provider_engine_b,
                trigger_engine=trigger_engine,
                config=track_b_config,
                on_error=lambda msg: log.warning(f"Scalp Error: {msg}")
            )
            log.info("Scalp Collector configured: WebSocket real-time (41 slots)")
        except Exception as e:
            log.error(f"Failed to initialize Scalp Collector: {e}")
    else:
        if not track_b_enabled:
            log.info("Scalp Collector disabled (TRACK_B_ENABLED=false)")
        else:
            log.info("Scalp Collector disabled (KIS credentials missing)")

    try:
        # Start observer
        observer.start()
        status_tracker.update_state("running", ready=True)

        log.info("Observer system fully operational")
        log.info("Event archive: %s", observer_data_dir)
        log.info("Logs: %s", _log_dir)
        log.info("Starting FastAPI server on 0.0.0.0:8000")

        # Start Swing/Scalp Collectors in background threads
        track_a_thread = None
        if swing_collector:
            def run_swing_async():
                """Run Swing Collector in asyncio event loop"""
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    log.info("Starting Swing Collector background task...")
                    loop.run_until_complete(swing_collector.start())
                except Exception as e:
                    log.error(f"Swing Collector error: {e}")
                finally:
                    loop.close()
            
            track_a_thread = threading.Thread(target=run_swing_async, daemon=True)
            track_a_thread.start()
            log.info("Swing Collector thread started")

        # Start scalp Collector in background thread
        track_b_thread = None
        if scalp_collector:
            def run_scalp_async():
                """Run Scalp Collector in asyncio event loop"""
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    log.info("Starting Scalp Collector background task...")
                    loop.run_until_complete(scalp_collector.start())
                except Exception as e:
                    log.error(f"Scalp Collector error: {e}")
                finally:
                    loop.close()
            
            track_b_thread = threading.Thread(target=run_scalp_async, daemon=True)
            track_b_thread.start()
            log.info("scalp Collector thread started")

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
            if swing_collector:
                log.info("Stopping Swing Collector...")
            if scalp_collector:
                log.info("Stopping Scalp Collector...")
                scalp_collector.stop()
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
