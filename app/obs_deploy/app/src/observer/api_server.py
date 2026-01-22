"""
FastAPI REST API Server for Observer Application

This module provides a REST API server for monitoring and managing the Observer application.
It exposes endpoints for health checks, readiness probes, status information, and metrics
collection compatible with Kubernetes and Prometheus.

Endpoints:
    - GET /health: Liveness probe - returns basic health status
    - GET /ready: Readiness probe - checks if observer is ready to serve
    - GET /status: Detailed status information about the observer
    - GET /metrics: Prometheus-compatible metrics
    - GET /metrics/observer: Observer-specific metrics in JSON format
    - GET /: Root endpoint with API information

Author: Observer Team
License: MIT
"""

import logging
import os
import psutil
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
import uvicorn

from observer.performance_metrics import get_metrics
from paths import observer_asset_dir, observer_log_dir


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Pydantic Models
class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Health status: 'healthy' or 'unhealthy'")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the health check")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")


class ReadinessResponse(BaseModel):
    """Readiness probe response model"""
    ready: bool = Field(..., description="Whether the service is ready to accept traffic")
    status: str = Field(..., description="Readiness status description")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the readiness check")
    checks: Dict[str, bool] = Field(..., description="Individual readiness check results")


class StatusResponse(BaseModel):
    """Detailed status response model"""
    status: str = Field(..., description="Overall status")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")
    observer_state: str = Field(..., description="Current observer state")
    last_update: Optional[str] = Field(None, description="Last state update timestamp")
    system: Dict[str, Any] = Field(..., description="System resource information")
    paths: Dict[str, str] = Field(..., description="Important directory paths")


class MetricsResponse(BaseModel):
    """Observer metrics response model"""
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")
    observer: Dict[str, Any] = Field(..., description="Observer-specific metrics")
    system: Dict[str, Any] = Field(..., description="System metrics")


# Observer Status Tracker
class ObserverStatusTracker:
    """
    Tracks the current state and status of the Observer application.

    This class maintains the observer's state information and provides
    thread-safe access to status data for API endpoints.
    """

    def __init__(self):
        """Initialize the status tracker"""
        self._lock = threading.Lock()
        self._state = "initializing"
        self._last_update = datetime.utcnow()
        self._start_time = time.time()
        self._ready = False
        self._error_count = 0
        self._last_error = None

    def update_state(self, state: str, ready: bool = None):
        """
        Update the observer state

        Args:
            state: New state value
            ready: Optional readiness flag
        """
        with self._lock:
            self._state = state
            self._last_update = datetime.utcnow()
            if ready is not None:
                self._ready = ready
            logger.info(f"Observer state updated to: {state} (ready: {self._ready})")

    def set_ready(self, ready: bool):
        """
        Set the readiness flag

        Args:
            ready: Readiness flag value
        """
        with self._lock:
            self._ready = ready
            logger.info(f"Observer readiness set to: {ready}")

    def record_error(self, error: str):
        """
        Record an error

        Args:
            error: Error message
        """
        with self._lock:
            self._error_count += 1
            self._last_error = error
            logger.error(f"Error recorded: {error}")

    def get_state(self) -> str:
        """Get current state"""
        with self._lock:
            return self._state

    def is_ready(self) -> bool:
        """Check if observer is ready"""
        with self._lock:
            return self._ready

    def get_uptime(self) -> float:
        """Get uptime in seconds"""
        return time.time() - self._start_time

    def get_last_update(self) -> datetime:
        """Get last update timestamp"""
        with self._lock:
            return self._last_update

    def get_error_count(self) -> int:
        """Get error count"""
        with self._lock:
            return self._error_count

    def get_last_error(self) -> Optional[str]:
        """Get last error message"""
        with self._lock:
            return self._last_error

    def get_full_status(self) -> Dict[str, Any]:
        """Get complete status information"""
        with self._lock:
            return {
                "state": self._state,
                "ready": self._ready,
                "uptime_seconds": self.get_uptime(),
                "last_update": self._last_update.isoformat(),
                "error_count": self._error_count,
                "last_error": self._last_error
            }


# Global status tracker instance
status_tracker = ObserverStatusTracker()


def get_status_tracker() -> ObserverStatusTracker:
    """Get the global status tracker instance."""
    return status_tracker


# FastAPI application
app = FastAPI(
    title="Observer API",
    description="REST API for Observer application monitoring and management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


def get_system_metrics() -> Dict[str, Any]:
    """
    Collect system resource metrics

    Returns:
        Dictionary containing CPU, memory, and disk metrics
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "cpu_percent": cpu_percent,
            "memory": {
                "total_mb": memory.total / (1024 * 1024),
                "available_mb": memory.available / (1024 * 1024),
                "used_mb": memory.used / (1024 * 1024),
                "percent": memory.percent
            },
            "disk": {
                "total_gb": disk.total / (1024 * 1024 * 1024),
                "used_gb": disk.used / (1024 * 1024 * 1024),
                "free_gb": disk.free / (1024 * 1024 * 1024),
                "percent": disk.percent
            }
        }
    except Exception as e:
        logger.error(f"Error collecting system metrics: {e}")
        return {
            "cpu_percent": 0,
            "memory": {"error": str(e)},
            "disk": {"error": str(e)}
        }


def perform_readiness_checks() -> Dict[str, bool]:
    """
    Perform readiness checks

    Returns:
        Dictionary of check names to boolean results
    """
    checks = {}

    # Check if observer is in ready state
    checks["observer_ready"] = status_tracker.is_ready()

    # Check if asset directory exists
    try:
        checks["asset_dir_exists"] = os.path.exists(observer_asset_dir())
    except Exception:
        checks["asset_dir_exists"] = False

    # Check if log directory exists and is writable
    try:
        checks["log_dir_writable"] = os.path.exists(observer_log_dir) and os.access(observer_log_dir, os.W_OK)
    except Exception:
        checks["log_dir_writable"] = False

    # Check system resources
    try:
        memory = psutil.virtual_memory()
        checks["memory_available"] = memory.percent < 95  # Less than 95% used
    except Exception:
        checks["memory_available"] = False

    try:
        disk = psutil.disk_usage('/')
        checks["disk_available"] = disk.percent < 95  # Less than 95% used
    except Exception:
        checks["disk_available"] = False

    return checks


@app.get("/", response_model=Dict[str, Any])
async def root():
    """
    Root endpoint - API information

    Returns:
        API metadata and available endpoints
    """
    return {
        "service": "Observer API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "readiness": "/ready",
            "status": "/status",
            "metrics": "/metrics",
            "observer_metrics": "/metrics/observer",
            "documentation": "/docs"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Liveness probe endpoint

    This endpoint is used by Kubernetes to determine if the container is alive.
    It returns a simple health status without performing expensive checks.

    Returns:
        Health status information
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        uptime_seconds=status_tracker.get_uptime()
    )


@app.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    """
    Readiness probe endpoint

    This endpoint is used by Kubernetes to determine if the container is ready
    to accept traffic. It performs various checks to ensure the service is
    fully operational.

    Returns:
        Readiness status and check results
    """
    checks = perform_readiness_checks()
    ready = all(checks.values())

    return ReadinessResponse(
        ready=ready,
        status="ready" if ready else "not_ready",
        timestamp=datetime.utcnow().isoformat(),
        checks=checks
    )


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Detailed status endpoint

    Returns comprehensive status information about the observer application
    including state, uptime, system resources, and configuration.

    Returns:
        Detailed status information
    """
    system_metrics = get_system_metrics()

    return StatusResponse(
        status="running",
        timestamp=datetime.utcnow().isoformat(),
        uptime_seconds=status_tracker.get_uptime(),
        observer_state=status_tracker.get_state(),
        last_update=status_tracker.get_last_update().isoformat(),
        system=system_metrics,
        paths={
            "asset_dir": str(observer_asset_dir()),
            "log_dir": str(observer_log_dir())
        }
    )


@app.get("/metrics", response_class=PlainTextResponse)
async def get_prometheus_metrics():
    """
    Prometheus metrics endpoint

    Returns metrics in Prometheus text exposition format for scraping
    by Prometheus or compatible monitoring systems.

    Returns:
        Metrics in Prometheus format
    """
    metrics_lines = []

    # Application metrics
    uptime = status_tracker.get_uptime()
    metrics_lines.append(f"# HELP observer_uptime_seconds Application uptime in seconds")
    metrics_lines.append(f"# TYPE observer_uptime_seconds gauge")
    metrics_lines.append(f"observer_uptime_seconds {uptime}")

    # State metrics
    state = status_tracker.get_state()
    ready = 1 if status_tracker.is_ready() else 0
    metrics_lines.append(f"# HELP observer_ready Observer readiness status")
    metrics_lines.append(f"# TYPE observer_ready gauge")
    metrics_lines.append(f'observer_ready{{state="{state}"}} {ready}')

    # Error metrics
    error_count = status_tracker.get_error_count()
    metrics_lines.append(f"# HELP observer_errors_total Total number of errors")
    metrics_lines.append(f"# TYPE observer_errors_total counter")
    metrics_lines.append(f"observer_errors_total {error_count}")

    # System metrics
    system_metrics = get_system_metrics()

    metrics_lines.append(f"# HELP system_cpu_percent CPU usage percentage")
    metrics_lines.append(f"# TYPE system_cpu_percent gauge")
    metrics_lines.append(f"system_cpu_percent {system_metrics.get('cpu_percent', 0)}")

    if "memory" in system_metrics and "percent" in system_metrics["memory"]:
        metrics_lines.append(f"# HELP system_memory_percent Memory usage percentage")
        metrics_lines.append(f"# TYPE system_memory_percent gauge")
        metrics_lines.append(f"system_memory_percent {system_metrics['memory']['percent']}")

    if "disk" in system_metrics and "percent" in system_metrics["disk"]:
        metrics_lines.append(f"# HELP system_disk_percent Disk usage percentage")
        metrics_lines.append(f"# TYPE system_disk_percent gauge")
        metrics_lines.append(f"system_disk_percent {system_metrics['disk']['percent']}")

    # Observer-specific metrics from performance_metrics module
    try:
        metrics_obj = get_metrics()
        observer_metrics = metrics_obj.get_metrics_summary()

        # Counters -> Prometheus counters
        for key, value in observer_metrics.get("counters", {}).items():
            safe_key = key.replace(" ", "_").replace("-", "_").lower()
            metrics_lines.append(f"# HELP observer_{safe_key}_total Observer counter: {key}")
            metrics_lines.append(f"# TYPE observer_{safe_key}_total counter")
            metrics_lines.append(f"observer_{safe_key}_total {value}")

        # Gauges -> Prometheus gauges
        for key, value in observer_metrics.get("gauges", {}).items():
            safe_key = key.replace(" ", "_").replace("-", "_").lower()
            metrics_lines.append(f"# HELP observer_{safe_key} Observer gauge: {key}")
            metrics_lines.append(f"# TYPE observer_{safe_key} gauge")
            metrics_lines.append(f"observer_{safe_key} {value}")

        # Timing stats (export avg_ms as gauge)
        for key, stats in observer_metrics.get("timing_stats", {}).items():
            safe_key = key.replace(" ", "_").replace("-", "_").lower()
            if "avg_ms" in stats:
                metrics_lines.append(f"# HELP observer_{safe_key}_avg_ms Observer timing avg for {key}")
                metrics_lines.append(f"# TYPE observer_{safe_key}_avg_ms gauge")
                metrics_lines.append(f"observer_{safe_key}_avg_ms {stats['avg_ms']}")
    except Exception as e:
        logger.error(f"Error collecting observer metrics: {e}")

    return "\n".join(metrics_lines) + "\n"


@app.get("/metrics/observer", response_model=MetricsResponse)
async def get_observer_metrics():
    """
    Observer-specific metrics endpoint

    Returns detailed metrics in JSON format specific to the observer application.
    This includes both observer metrics and system metrics.

    Returns:
        Observer and system metrics in JSON format
    """
    observer_metrics: Dict[str, Any] = {}
    try:
        observer_metrics = get_metrics().get_metrics_summary()
    except Exception as e:
        logger.error(f"Error collecting observer metrics: {e}")
        observer_metrics = {"error": str(e)}

    system_metrics = get_system_metrics()

    # Add status tracker metrics
    observer_metrics.update({
        "state": status_tracker.get_state(),
        "ready": status_tracker.is_ready(),
        "error_count": status_tracker.get_error_count(),
        "last_error": status_tracker.get_last_error()
    })

    return MetricsResponse(
        timestamp=datetime.utcnow().isoformat(),
        uptime_seconds=status_tracker.get_uptime(),
        observer=observer_metrics,
        system=system_metrics
    )


def run_api_server(host: str = "0.0.0.0", port: int = 8000, log_level: str = "info"):
    """
    Run the FastAPI server

    This function starts the uvicorn server synchronously. It blocks until
    the server is stopped.

    Args:
        host: Host to bind to (default: 0.0.0.0)
        port: Port to bind to (default: 8000)
        log_level: Logging level (default: info)
    """
    logger.info(f"Starting API server on {host}:{port}")
    status_tracker.update_state("running", ready=True)

    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=log_level,
            access_log=True
        )
    except Exception as e:
        logger.error(f"Error running API server: {e}")
        status_tracker.record_error(str(e))
        status_tracker.update_state("error", ready=False)
        raise


def start_api_server_background(host: str = "0.0.0.0", port: int = 8000, log_level: str = "info") -> threading.Thread:
    """
    Start the FastAPI server in a background thread

    This function starts the uvicorn server in a separate daemon thread,
    allowing the main application to continue running.

    Args:
        host: Host to bind to (default: 0.0.0.0)
        port: Port to bind to (default: 8000)
        log_level: Logging level (default: info)

    Returns:
        The thread object running the server
    """
    logger.info(f"Starting API server in background on {host}:{port}")

    def run_server():
        run_api_server(host=host, port=port, log_level=log_level)

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()

    logger.info("API server thread started")
    return thread


if __name__ == "__main__":
    # Run the server directly when the module is executed
    run_api_server()
