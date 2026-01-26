"""
deployment_paths.py

Observer deployment-specific path resolver for /app structure.

This module provides path resolution specifically for Observer deployment
in containerized environments with /app structure.
"""

import os
from pathlib import Path
from typing import Optional

# ============================================================
# Deployment-specific Constants
# ============================================================

DEPLOYMENT_ROOT = Path("/app")
DATA_ROOT = DEPLOYMENT_ROOT / "data"
LOG_ROOT = DEPLOYMENT_ROOT / "logs"
CONFIG_ROOT = DEPLOYMENT_ROOT / "config"

# ============================================================
# Observer Asset Paths
# ============================================================

def observer_asset_dir() -> Path:
    """
    Get Observer asset directory for deployment.
    
    In deployment structure:
    - Observer data is stored in /app/data/observer
    - This is mounted as volume in Docker
    
    In local development:
    - Observer data is stored in app/observer/config/observer
    """
    if os.environ.get("OBSERVER_DATA_DIR"):
        return Path(os.environ["OBSERVER_DATA_DIR"])
    
    # Check if running in deployment environment
    if os.environ.get("OBSERVER_STANDALONE") == "1" or Path("/app").exists():
        return DATA_ROOT / "observer"
    
    # Local development - use relative path to config/observer
    # This path is relative to the project root
    return Path("app/observer/config/observer")

def observer_asset_file(filename: str) -> Path:
    """Get full path to Observer asset file."""
    return observer_asset_dir() / filename

def observer_log_dir() -> Path:
    """Get Observer log directory."""
    if os.environ.get("OBSERVER_LOG_DIR"):
        return Path(os.environ["OBSERVER_LOG_DIR"])
    
    return LOG_ROOT

def observer_config_dir() -> Path:
    """Get Observer configuration directory."""
    if os.environ.get("OBSERVER_CONFIG_DIR"):
        return Path(os.environ["OBSERVER_CONFIG_DIR"])
    
    return CONFIG_ROOT

# ============================================================
# Runtime Paths
# ============================================================

def runtime_socket_dir() -> Optional[Path]:
    """Get runtime socket directory (if needed)."""
    socket_dir = DEPLOYMENT_ROOT / "run"
    socket_dir.mkdir(exist_ok=True)
    return socket_dir

def temp_dir() -> Path:
    """Get temporary directory for Observer operations."""
    temp_path = DEPLOYMENT_ROOT / "tmp"
    temp_path.mkdir(exist_ok=True)
    return temp_path

# ============================================================
# Path Validation
# ============================================================

def validate_deployment_paths() -> bool:
    """Validate that all required directories exist or can be created."""
    required_dirs = [
        observer_asset_dir(),
        observer_log_dir(),
        observer_config_dir(),
    ]
    
    for dir_path in required_dirs:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Failed to create directory {dir_path}: {e}")
            return False
    
    return True

# ============================================================
# Environment Detection
# ============================================================

def is_deployment_environment() -> bool:
    """Check if running in deployment environment."""
    return (
        os.environ.get("OBSERVER_STANDALONE") == "1" or
        DEPLOYMENT_ROOT.exists()
    )

def get_deployment_info() -> dict:
    """Get deployment environment information."""
    return {
        "deployment_root": str(DEPLOYMENT_ROOT),
        "data_root": str(DATA_ROOT),
        "log_root": str(LOG_ROOT),
        "config_root": str(CONFIG_ROOT),
        "observer_data_dir": str(observer_asset_dir()),
        "observer_log_dir": str(observer_log_dir()),
        "is_deployment": is_deployment_environment(),
        "paths_valid": validate_deployment_paths(),
    }
