"""
runtime package

Runtime execution engines and orchestrators.

This package provides runner implementations for different execution scenarios:
- ObserverRunner: Runs Observer with market data providers
- Phase15Runner: Phase 15 execution orchestrator
- MaintenanceRunner: Maintenance and cleanup operations
- RealTickRunner: Real-time tick event handling

Each runner is designed to be plugged into the deployment mode system
and provides specific execution logic for different use cases.

Example:
    from runtime.observer_runner import ObserverRunner
    from ops.observer.inputs import MockMarketDataProvider

    provider = MockMarketDataProvider()
    runner = ObserverRunner(provider)
    runner.run()
"""

from __future__ import annotations

__all__ = [
    "ObserverRunner",
    "Phase15Runner",
    "MaintenanceRunner",
    "RealTickRunner",
]
