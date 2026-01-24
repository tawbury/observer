"""
config_manager.py

Configuration management interface for Observer scalp extensions.

ROLE & BOUNDARY DECLARATION:
- THIS IS NOT Observer-Core component
- Layer: Configuration management interface
- Ownership: Ops/Observer configuration module
- Access: Observer internal components ONLY
- Must NOT be accessed: External decision systems, strategy engines

This module provides a centralized interface for accessing scalp extension
configuration while maintaining separation from Observer-Core responsibilities.

NON-PERSISTENCE DECLARATION:
- Configuration is loaded at startup only
- No runtime configuration reloading
- Configuration changes require process restart

SAFETY CONFIRMATION:
- Configuration manager does NOT affect Observer behavior
- Configuration manager does NOT introduce decision logic
- Configuration manager does NOT alter data flow
- Configuration manager is read-only after initialization

Constraints from Observer_Architecture.md:
- Observer receives configuration for session ID, runtime mode, EventBus sink
- Configuration loading is external to Observer-Core

Constraints from observer_scalp_task_07_configuration_management.md:
- Additive changes only
- Backward-compatible defaults
- Configuration loading is robust and error-handled
"""

from typing import Optional, Dict, Any
import logging
from .scalp_config import ScalpExtensionConfig, load_config_from_dict

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Centralized configuration manager for Observer scalp extensions.
    
    ROLE & BOUNDARY:
    - NOT part of Observer-Core
    - Layer: Configuration management interface
    - Access: Observer internal components ONLY
    - Must NOT be used for: Runtime configuration changes
    
    This manager provides read-only access to configuration after initialization.
    """
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dict: Configuration dictionary, None for defaults
        """
        self._config: Optional[ScalpExtensionConfig] = None
        self._load_config(config_dict)
    
    def _load_config(self, config_dict: Optional[Dict[str, Any]] = None) -> None:
        """Load and validate configuration."""
        try:
            self._config = load_config_from_dict(config_dict)
            logger.info("Configuration manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Fall back to defaults on error
            self._config = load_config_from_dict()
            logger.warning("Using default configuration due to loading error")
    
    def get_config(self) -> ScalpExtensionConfig:
        """
        Get current configuration.
        
        Returns:
            Current ScalpExtensionConfig (read-only)
        """
        if self._config is None:
            raise RuntimeError("Configuration not initialized")
        return self._config
    
    def is_hybrid_trigger_enabled(self) -> bool:
        """Check if hybrid trigger mode is enabled."""
        return self.get_config().hybrid_trigger.enabled
    
    def is_performance_monitoring_enabled(self) -> bool:
        """Check if performance monitoring is enabled."""
        return self.get_config().performance.enabled
    
    def is_buffer_enabled(self) -> bool:
        """Check if buffering is enabled."""
        return self.get_config().buffer.enable_buffering
    
    def is_rotation_enabled(self) -> bool:
        """Check if log rotation is enabled."""
        return self.get_config().rotation.enabled


# Global configuration manager instance
_global_config_manager: Optional[ConfigManager] = None


def initialize_config(config_dict: Optional[Dict[str, Any]] = None) -> None:
    """
    Initialize global configuration manager.
    
    Args:
        config_dict: Configuration dictionary, None for defaults
    """
    global _global_config_manager
    _global_config_manager = ConfigManager(config_dict)


def get_config_manager() -> ConfigManager:
    """
    Get global configuration manager.
    
    Returns:
        Global ConfigManager instance
        
    Raises:
        RuntimeError: If configuration not initialized
    """
    if _global_config_manager is None:
        raise RuntimeError("Configuration manager not initialized")
    return _global_config_manager


def get_config() -> ScalpExtensionConfig:
    """
    Get current scalp extension configuration.
    
    Returns:
        Current ScalpExtensionConfig
    """
    return get_config_manager().get_config()
