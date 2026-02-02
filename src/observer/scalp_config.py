"""
scalp_config.py

Scalp Extension Configuration Management for Observer.

ROLE & BOUNDARY DECLARATION:
- THIS IS NOT Observer-Core component
- Layer: Configuration management (supports Observer but not part of Core)
- Ownership: Ops/Observer configuration module
- Access: Observer internal components ONLY
- Must NOT be accessed: External decision systems, strategy engines

This module provides configuration management for scalp extension features
while maintaining existing Observer configuration structure and boundaries.

NON-PERSISTENCE DECLARATION:
- Configuration is loaded at startup only
- No runtime configuration reloading
- Configuration changes require process restart

SAFETY CONFIRMATION:
- Configuration does NOT affect Observer responsibilities
- Configuration does NOT introduce decision logic
- Configuration does NOT alter Snapshot/PatternRecord
- Configuration does NOT enable Scalp adaptive behavior

Constraints from Observer_Architecture.md:
- Observer receives configuration for session ID, runtime mode, EventBus sink
- Observer does NOT load strategy configurations
- Observer does NOT access trading parameters

Constraints from observer_scalp_task_07_configuration_management.md:
- Additive changes only
- No strategy-specific configuration parameters
- No decision logic configuration
- Backward-compatible defaults required
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HybridTriggerConfig:
    """Configuration for hybrid trigger mode."""
    enabled: bool = False
    tick_source: str = "websocket"
    min_interval_ms: float = 10.0
    max_interval_ms: float = 1000.0


@dataclass(frozen=True)
class BufferConfig:
    """Configuration for time-based buffering."""
    flush_interval_ms: float = 1000.0
    max_buffer_size: int = 10000
    enable_buffering: bool = True


@dataclass(frozen=True)
class RotationConfig:
    """Configuration for log rotation."""
    enabled: bool = False
    window_ms: int = 3600000  # 1 hour
    max_files: int = 24


@dataclass(frozen=True)
class PerformanceConfig:
    """Configuration for performance monitoring."""
    enabled: bool = True
    metrics_history_size: int = 1000


@dataclass(frozen=True)
class ScalpExtensionConfig:
    """
    Main configuration container for scalp extension features.
    
    This configuration is additive-only and does NOT modify existing
    Observer behavior or responsibilities.
    """
    hybrid_trigger: HybridTriggerConfig = field(default_factory=HybridTriggerConfig)
    buffer: BufferConfig = field(default_factory=BufferConfig)
    rotation: RotationConfig = field(default_factory=RotationConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)


class ConfigValidator:
    """Validator for scalp extension configuration parameters."""
    
    @staticmethod
    def validate_hybrid_trigger(config: HybridTriggerConfig) -> None:
        """Validate hybrid trigger configuration."""
        if config.min_interval_ms <= 0:
            raise ValueError("hybrid_trigger.min_interval_ms must be positive")
        
        if config.max_interval_ms <= config.min_interval_ms:
            raise ValueError("hybrid_trigger.max_interval_ms must be greater than min_interval_ms")
        
        if config.tick_source not in ["websocket", "rest", "simulation"]:
            logger.warning(f"Unknown tick_source: {config.tick_source}")
    
    @staticmethod
    def validate_buffer(config: BufferConfig) -> None:
        """Validate buffer configuration."""
        if config.flush_interval_ms <= 0:
            raise ValueError("buffer.flush_interval_ms must be positive")
        
        if config.max_buffer_size <= 0:
            raise ValueError("buffer.max_buffer_size must be positive")
    
    @staticmethod
    def validate_rotation(config: RotationConfig) -> None:
        """Validate rotation configuration."""
        if config.enabled and config.window_ms <= 0:
            raise ValueError("rotation.window_ms must be positive when enabled")
        
        if config.max_files <= 0:
            raise ValueError("rotation.max_files must be positive")
    
    @staticmethod
    def validate_performance(config: PerformanceConfig) -> None:
        """Validate performance configuration."""
        if config.metrics_history_size <= 0:
            raise ValueError("performance.metrics_history_size must be positive")
    
    @classmethod
    def validate_all(cls, config: ScalpExtensionConfig) -> None:
        """Validate all configuration sections."""
        try:
            cls.validate_hybrid_trigger(config.hybrid_trigger)
            cls.validate_buffer(config.buffer)
            cls.validate_rotation(config.rotation)
            cls.validate_performance(config.performance)
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise


def load_config_from_dict(config_dict: Optional[Dict[str, Any]] = None) -> ScalpExtensionConfig:
    """
    Load scalp extension configuration from dictionary.
    
    Args:
        config_dict: Configuration dictionary, None for defaults
        
    Returns:
        Validated ScalpExtensionConfig instance
    """
    if config_dict is None:
        config_dict = {}
    
    # Extract configuration sections with defaults
    hybrid_dict = config_dict.get("hybrid_trigger", {})
    buffer_dict = config_dict.get("buffer", {})
    rotation_dict = config_dict.get("rotation", {})
    performance_dict = config_dict.get("performance", {})
    
    # Create configuration objects
    hybrid_config = HybridTriggerConfig(
        enabled=hybrid_dict.get("enabled", False),
        tick_source=hybrid_dict.get("tick_source", "websocket"),
        min_interval_ms=hybrid_dict.get("min_interval_ms", 10.0),
        max_interval_ms=hybrid_dict.get("max_interval_ms", 1000.0),
    )
    
    buffer_config = BufferConfig(
        flush_interval_ms=buffer_dict.get("flush_interval_ms", 1000.0),
        max_buffer_size=buffer_dict.get("max_buffer_size", 10000),
        enable_buffering=buffer_dict.get("enable_buffering", True),
    )
    
    rotation_config = RotationConfig(
        enabled=rotation_dict.get("enabled", False),
        window_ms=rotation_dict.get("window_ms", 3600000),
        max_files=rotation_dict.get("max_files", 24),
    )
    
    performance_config = PerformanceConfig(
        enabled=performance_dict.get("enabled", True),
        metrics_history_size=performance_dict.get("metrics_history_size", 1000),
    )
    
    # Create main configuration
    config = ScalpExtensionConfig(
        hybrid_trigger=hybrid_config,
        buffer=buffer_config,
        rotation=rotation_config,
        performance=performance_config,
    )
    
    # Validate configuration
    ConfigValidator.validate_all(config)
    
    logger.info("Scalp extension configuration loaded and validated")
    return config


def get_default_config() -> ScalpExtensionConfig:
    """Get default scalp extension configuration."""
    return load_config_from_dict()
