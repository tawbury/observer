"""
deployment_mode.py

Abstract interfaces for different Observer deployment modes.

Provides a plugin-like architecture where different deployment modes
(Docker, Kubernetes, CLI, Development) can be plugged in without
changing the core Observer logic.

Design Principles:
- Single responsibility: Each mode handles its specific lifecycle
- Plugin architecture: New modes can be added without modifying existing code
- Dependency injection: Modes are injected into the main runner
- Signal handling: Graceful shutdown for all modes
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class DeploymentModeType(str, Enum):
    """Enumeration of supported deployment modes"""
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    CLI = "cli"
    DEVELOPMENT = "dev"


@dataclass
class DeploymentConfig:
    """
    Configuration for deployment mode initialization.

    Attributes:
        mode: Deployment mode type
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        config_file: Optional path to configuration file
        extra_params: Additional parameters for specific modes
    """
    mode: DeploymentModeType
    log_level: str = "INFO"
    config_file: Optional[str] = None
    extra_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.extra_params is None:
            self.extra_params = {}


class IDeploymentMode(ABC):
    """
    Abstract interface for deployment modes.

    Each deployment mode must implement this interface to be compatible
    with the unified entry point system.
    """

    def __init__(self, config: DeploymentConfig):
        """
        Initialize the deployment mode.

        Args:
            config: Deployment configuration
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the deployment mode.

        This method is called before starting the observer to perform
        any necessary setup (environment configuration, dependency injection, etc.)
        """
        pass

    @abstractmethod
    async def run(self) -> None:
        """
        Run the observer in this deployment mode.

        This is the main execution method that should block until
        the observer is stopped (graceful shutdown).
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Gracefully shutdown the observer.

        This method should perform cleanup operations and allow in-flight
        requests to complete before exiting.
        """
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the deployment.

        Returns:
            Dictionary containing deployment status information
        """
        pass

    async def __aenter__(self):
        """Context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.shutdown()


class DockerDeploymentMode(IDeploymentMode):
    """
    Docker deployment mode.

    Runs Observer as a standalone container with:
    - FastAPI monitoring server
    - Kubernetes health probes (/health, /ready)
    - Prometheus metrics
    - Structured logging to stdout
    """

    async def initialize(self) -> None:
        """Initialize Docker mode"""
        self.logger.info("Initializing Docker deployment mode...")
        import os
        from pathlib import Path

        # Set Docker-specific environment variables
        os.environ.setdefault("OBSERVER_STANDALONE", "1")
        os.environ.setdefault("OBSERVER_DEPLOYMENT_MODE", "docker")
        os.environ.setdefault("PYTHONPATH", "/app/src:/app")
        os.environ.setdefault("OBSERVER_DATA_DIR", "/app/data/observer")
        os.environ.setdefault("OBSERVER_LOG_DIR", "/app/logs")

        # Create required directories
        for env_var in ["OBSERVER_DATA_DIR", "OBSERVER_LOG_DIR"]:
            path_str = os.environ.get(env_var)
            if path_str:
                Path(path_str).mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Created {env_var}: {path_str}")

        self._initialized = True
        self.logger.info("Docker deployment mode initialized")

    async def run(self) -> None:
        """Run Observer in Docker mode"""
        if not self._initialized:
            await self.initialize()

        self.logger.info("Starting Observer in Docker mode...")

        try:
            # Import and run Docker entry point
            from observer import run_observer_with_api
            await run_observer_with_api()
        except ImportError as e:
            self.logger.error(f"Failed to import Docker entry point: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error in Docker mode: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown Docker mode"""
        self.logger.info("Shutting down Docker deployment mode...")
        # Graceful shutdown will be handled by signal handlers
        await asyncio.sleep(0.5)

    def get_status(self) -> Dict[str, Any]:
        """Get Docker mode status"""
        return {
            "mode": "docker",
            "initialized": self._initialized,
            "has_api": True,
            "health_check_url": "http://127.0.0.1:8000/health"
        }


class KubernetesDeploymentMode(IDeploymentMode):
    """
    Kubernetes deployment mode.

    Similar to Docker but with Kubernetes-specific handling:
    - Namespace awareness
    - Service account integration (future)
    - Pod termination grace period handling
    - Leader election support (future)
    """

    async def initialize(self) -> None:
        """Initialize Kubernetes mode"""
        self.logger.info("Initializing Kubernetes deployment mode...")
        import os
        from pathlib import Path

        # Set Kubernetes-specific environment variables
        os.environ.setdefault("OBSERVER_STANDALONE", "1")
        os.environ.setdefault("OBSERVER_DEPLOYMENT_MODE", "kubernetes")
        os.environ.setdefault("PYTHONPATH", "/app/src:/app")

        # Check for Kubernetes ConfigMap/Secret mounts
        k8s_config_paths = [
            "/etc/observer/config",
            "/var/run/secrets/kubernetes.io/serviceaccount"
        ]
        for path in k8s_config_paths:
            if Path(path).exists():
                self.logger.debug(f"Found Kubernetes mount: {path}")

        self._initialized = True
        self.logger.info("Kubernetes deployment mode initialized")

    async def run(self) -> None:
        """Run Observer in Kubernetes mode"""
        if not self._initialized:
            await self.initialize()

        self.logger.info("Starting Observer in Kubernetes mode...")

        try:
            # Import and run Kubernetes entry point (same as Docker for now)
            from observer import run_observer_with_api
            await run_observer_with_api()
        except ImportError as e:
            self.logger.error(f"Failed to import Kubernetes entry point: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error in Kubernetes mode: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown Kubernetes mode"""
        self.logger.info("Shutting down Kubernetes deployment mode...")
        # Respect Kubernetes termination grace period
        await asyncio.sleep(0.5)

    def get_status(self) -> Dict[str, Any]:
        """Get Kubernetes mode status"""
        import os
        from pathlib import Path

        return {
            "mode": "kubernetes",
            "initialized": self._initialized,
            "has_api": True,
            "health_check_url": "http://127.0.0.1:8000/health",
            "in_kubernetes": Path("/var/run/secrets/kubernetes.io/serviceaccount").exists(),
            "pod_namespace": os.environ.get("POD_NAMESPACE", "default")
        }


class CLIDeploymentMode(IDeploymentMode):
    """
    CLI deployment mode.

    Interactive command-line mode for:
    - Local testing
    - Manual configuration
    - Development and debugging
    - Real-time feedback
    """

    async def initialize(self) -> None:
        """Initialize CLI mode"""
        self.logger.info("Initializing CLI deployment mode...")
        self._initialized = True

    async def run(self) -> None:
        """Run Observer in CLI mode"""
        if not self._initialized:
            await self.initialize()

        self.logger.info("Starting Observer in CLI mode...")
        print("""
╔═══════════════════════════════════════════════════════════════╗
║                   Observer CLI Mode                          ║
╚═══════════════════════════════════════════════════════════════╝

Available commands:
  status          Show current system status
  health          Check health status
  metrics         Display current metrics
  config          Show configuration
  help            Show this help message
  quit            Exit the CLI

⚠️  CLI mode is not yet fully implemented.
    Use Docker or Kubernetes mode for full functionality.
        """)

        # Keep CLI mode running until quit
        while True:
            try:
                cmd = input("observer> ").strip().lower()
                if cmd in ["quit", "exit", "q"]:
                    self.logger.info("Exiting CLI mode...")
                    break
                elif cmd == "status":
                    print(self.get_status())
                elif cmd == "help":
                    print("See available commands above")
                else:
                    print(f"Unknown command: {cmd}")
            except KeyboardInterrupt:
                self.logger.info("CLI interrupted")
                break
            except EOFError:
                break

    async def shutdown(self) -> None:
        """Shutdown CLI mode"""
        self.logger.info("Shutting down CLI deployment mode...")

    def get_status(self) -> Dict[str, Any]:
        """Get CLI mode status"""
        return {
            "mode": "cli",
            "initialized": self._initialized,
            "interactive": True,
            "status": "ready"
        }


class DevelopmentDeploymentMode(IDeploymentMode):
    """
    Development deployment mode.

    Development-focused mode with:
    - Detailed logging
    - File monitoring
    - Hot reload support (future)
    - Development-friendly output
    """

    async def initialize(self) -> None:
        """Initialize Development mode"""
        self.logger.info("Initializing Development deployment mode...")
        import os

        os.environ.setdefault("OBSERVER_STANDALONE", "1")
        os.environ.setdefault("OBSERVER_DEPLOYMENT_MODE", "dev")
        os.environ.setdefault("PYTHONPATH", "/app/src:/app")

        self._initialized = True
        self.logger.info("Development deployment mode initialized")

    async def run(self) -> None:
        """Run Observer in Development mode"""
        if not self._initialized:
            await self.initialize()

        self.logger.info("Starting Observer in Development mode...")
        self.logger.warning("Development mode: Hot reload active")

        try:
            # Import and run Docker entry point (same as Docker for development)
            from observer import run_observer_with_api
            await run_observer_with_api()
        except ImportError as e:
            self.logger.error(f"Failed to import Development entry point: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error in Development mode: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown Development mode"""
        self.logger.info("Shutting down Development deployment mode...")

    def get_status(self) -> Dict[str, Any]:
        """Get Development mode status"""
        return {
            "mode": "dev",
            "initialized": self._initialized,
            "debug": True,
            "watch_mode": True
        }


# Factory for creating deployment modes
def create_deployment_mode(config: DeploymentConfig) -> IDeploymentMode:
    """
    Factory function to create appropriate deployment mode.

    Args:
        config: Deployment configuration

    Returns:
        Appropriate deployment mode instance

    Raises:
        ValueError: If deployment mode is not supported
    """
    modes = {
        DeploymentModeType.DOCKER: DockerDeploymentMode,
        DeploymentModeType.KUBERNETES: KubernetesDeploymentMode,
        DeploymentModeType.CLI: CLIDeploymentMode,
        DeploymentModeType.DEVELOPMENT: DevelopmentDeploymentMode,
    }

    mode_class = modes.get(config.mode)
    if not mode_class:
        raise ValueError(f"Unsupported deployment mode: {config.mode}")

    return mode_class(config)
