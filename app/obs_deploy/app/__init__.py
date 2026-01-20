"""
Observer Application Package

Standalone Observer deployment package with FastAPI monitoring server.

This is the main application entry point for containerized deployment.

Usage:
    # As Docker container entry point
    python observer.py

    # As Python module
    python -m observer

    # With specific mode
    python -m observer --mode docker
    python -m observer --mode kubernetes

Modules:
- __main__: Unified entry point with deployment mode support
- src/observer: Core observation engine
- src/runtime: Execution orchestrators
- paths: Canonical path resolver

Environment Variables:
    OBSERVER_STANDALONE: Enable standalone mode (docker/kubernetes)
    OBSERVER_DEPLOYMENT_MODE: Deployment mode (docker/kubernetes)
    OBSERVER_DATA_DIR: Data directory (/app/data/observer)
    OBSERVER_LOG_DIR: Log directory (/app/logs)
    PYTHONPATH: Python import paths (/app/src:/app)

API Endpoints (when running):
    GET /health              - Kubernetes liveness probe
    GET /ready               - Kubernetes readiness probe
    GET /status              - System status
    GET /metrics             - Prometheus metrics
    GET /metrics/observer    - JSON metrics
    GET /docs               - API documentation
"""

from __future__ import annotations

__version__ = "1.0.0"
__author__ = "Observer Team"
__license__ = "MIT"

__all__ = [
    "__version__",
    "paths",
]
