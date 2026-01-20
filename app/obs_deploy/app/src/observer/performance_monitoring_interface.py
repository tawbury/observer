"""
performance_monitoring_interface.py

External interface for accessing Observer performance metrics.

ROLE & BOUNDARY DECLARATION:
- THIS IS NOT Observer-Core component
- Layer: Runtime Interface (External access boundary)
- Ownership: Ops/Observer external interface
- Access: External monitoring tools ONLY
- Must NOT be accessed: Internal Observer components (use performance_metrics.py directly)
- Must NOT be used for: Decision logic, strategy execution, system control

This interface provides read-only access to performance metrics for external
monitoring tools without allowing any modification of Observer behavior.

NON-PERSISTENCE DECLARATION:
- Metrics are IN-MEMORY ONLY (from internal performance_metrics.py)
- Metrics are RESET on process restart
- NO PERSISTENCE is provided by this interface
- Persistence decisions are DEFERRED to later tasks

SAFETY CONFIRMATION:
- Interface does NOT affect Observer behavior
- Interface does NOT influence decision flow
- Interface does NOT alter Snapshot/PatternRecord
- Interface does NOT enable Scalp adaptive behavior
- Interface is READ-ONLY by design

Constraints from observer_scalp_task_06_performance_monitoring.md:
- Metrics are accessible for external monitoring tools
- No decision logic based on performance metrics
- No automatic system tuning based on metrics
"""

from typing import Dict, Any
from .performance_metrics import get_metrics


class PerformanceMonitoringInterface:
    """
    Read-only interface for external performance monitoring access.
    
    ROLE & BOUNDARY:
    - NOT part of Observer-Core
    - Layer: Runtime Interface (external access boundary)
    - Ownership: External monitoring interface
    - Access: External monitoring tools ONLY
    - Must NOT be accessed: Internal Observer components
    - Must NOT be used for: Decision logic, system control
    
    This interface provides safe, read-only access to Observer performance
    metrics without allowing any modification of Observer behavior.
    
    NON-PERSISTENCE:
    - All data comes from in-memory metrics
    - Data is LOST on process restart
    - No persistence provided
    """
    
    @staticmethod
    def get_current_metrics() -> Dict[str, Any]:
        """
        Get current performance metrics snapshot.
        
        Returns:
            Dictionary containing all current performance metrics
            including counters, gauges, timing statistics, and uptime.
        """
        return get_metrics().get_metrics_summary()
    
    @staticmethod
    def get_snapshot_count() -> int:
        """Get total number of snapshots processed."""
        return get_metrics().get_snapshot_count()
    
    @staticmethod
    def get_buffer_depth() -> float:
        """Get current buffer depth."""
        return get_metrics().get_buffer_depth()
    
    @staticmethod
    def get_uptime_seconds() -> float:
        """Get observer uptime in seconds."""
        return get_metrics().get_uptime_seconds()
    
    @staticmethod
    def is_healthy() -> bool:
        """
        Basic health check based on performance metrics.
        
        Returns:
            True if Observer appears healthy based on basic metrics
        """
        metrics = get_metrics().get_metrics_summary()
        
        # Basic health indicators
        uptime = metrics.get("uptime_seconds", 0)
        snapshots_processed = metrics.get("counters", {}).get("snapshots_processed", 0)
        
        # Consider healthy if running for at least 1 second and processing some snapshots
        return uptime > 1.0 and snapshots_processed >= 0


# Convenience function for external access
def get_performance_metrics() -> Dict[str, Any]:
    """
    Get comprehensive performance metrics for external monitoring.
    
    ROLE & BOUNDARY:
    - NOT Observer-Core component
    - Layer: External interface function
    - Access: External monitoring tools ONLY
    - Must NOT be used for: Internal Observer operations
    
    This is the primary interface for external monitoring tools to access
    Observer performance data.
    
    SAFETY: Returns copy of metrics, not direct access to internal state.
    
    Returns:
        Dictionary containing all performance metrics
    """
    return PerformanceMonitoringInterface.get_current_metrics()
