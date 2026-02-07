#!/usr/bin/env python3
"""
Observer Entry Point - Unified Main Module

This module provides a unified entry point for all Observer deployment modes:
- Docker: Standalone container deployment with FastAPI server
- Kubernetes: Pod deployment with health probes
- CLI: Direct command-line invocation
- Development: Local testing and debugging

Usage:
    # Docker/Kubernetes deployment
    python -m observer

    # Specific deployment mode
    python -m observer --mode docker
    python -m observer --mode kubernetes
    python -m observer --mode cli

    # With configuration file
    python -m observer --config /path/to/config.yaml

    # With specific log level
    python -m observer --log-level debug
"""

from __future__ import annotations

import sys
import argparse
import logging
import asyncio
from pathlib import Path
from typing import Optional, List

# Add src (parent of observer package) to path for imports
_src_root = Path(__file__).resolve().parent.parent
if str(_src_root) not in sys.path:
    sys.path.insert(0, str(_src_root))

# Import deployment mode interfaces (observer package is src/observer)
from observer.deployment_mode import (
    DeploymentModeType,
    DeploymentConfig,
    create_deployment_mode,
)


def setup_logging(log_level: str = "INFO", mode: DeploymentModeType = DeploymentModeType.DOCKER):
    """
    Configure logging based on deployment mode.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        mode: Deployment mode
    """
    from observer.paths import system_log_dir
    from shared.hourly_handler import HourlyRotatingFileHandler
    
    level = getattr(logging, log_level.upper(), logging.INFO)

    handlers: List[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if mode == DeploymentModeType.DOCKER or mode == DeploymentModeType.KUBERNETES:
        # Docker/Kubernetes: structured logging to stdout + system file logging
        format_string = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        
        # Add system log file handler
        try:
            _system_log_dir = system_log_dir()
            file_handler = HourlyRotatingFileHandler(_system_log_dir)
            file_handler.setFormatter(logging.Formatter(format_string))
            file_handler.setLevel(level)
            handlers.append(file_handler)
        except Exception as e:
            print(f"Failed to setup system log file handler: {e}", file=sys.stderr)
    else:
        # CLI/Development: human-readable format
        format_string = "%(levelname)-8s | %(name)s | %(message)s"

    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=handlers,
        force=True
    )

    return logging.getLogger(__name__)


async def run_deployment_mode(config: DeploymentConfig):
    """
    Run Observer in specified deployment mode using the unified interface.

    Args:
        config: Deployment configuration
    """
    logger = logging.getLogger(__name__)

    try:
        # Create appropriate deployment mode instance
        deployment = create_deployment_mode(config)
        logger.info(f"Deployment mode created: {config.mode.value}")

        # Run with context manager for proper initialization/shutdown
        async with deployment as mode:
            await mode.run()

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error in deployment mode: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Observer - Standalone monitoring system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m observer                    # Docker mode (default)
  python -m observer --mode kubernetes  # Kubernetes mode
  python -m observer --mode cli         # CLI mode
  python -m observer --log-level debug  # Debug logging
  python -m observer --config conf.yaml # Custom config
        """
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=[m.value for m in DeploymentModeType],
        default=DeploymentModeType.DOCKER.value,
        help="Deployment mode (default: docker)"
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)"
    )

    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration file"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )

    return parser


def main():
    """Main entry point."""
    # Load environment FIRST (before logging — LOG_LEVEL comes from .env)
    from observer.paths import load_env_by_run_mode
    load_env_by_run_mode()

    # Parse arguments
    parser = create_argument_parser()
    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(
        log_level=args.log_level,
        mode=DeploymentModeType(args.mode),
    )

    logger.info(f"Observer v1.0.0 starting in {args.mode.upper()} mode")
    logger.debug(f"Python: {sys.version}")
    logger.debug(f"CWD: {Path.cwd()}")

    try:
        mode = DeploymentModeType(args.mode)

        # Create deployment configuration
        config = DeploymentConfig(
            mode=mode,
            log_level=args.log_level,
            config_file=args.config
        )

        # Run the unified deployment mode handler
        asyncio.run(run_deployment_mode(config))

    except KeyboardInterrupt:
        logger.info("Observer stopped by user (SIGINT)")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
