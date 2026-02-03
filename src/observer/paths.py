"""
paths.py

Observer project-wide canonical path resolver.

This module defines the single source of truth for all filesystem paths
used across the Observer project, including:
- execution (observer.py)
- observer / runtime modules
- pytest
- local scripts

Design principles:
- Resilient to folder restructuring
- No relative depth assumptions (no parents[n])
- Project-level, not package-level

Path Management Strategy:
- Observer-generated JSON / JSONL files live under data/assets (scalp, swing, system).
- config/ is for operational config only; logs/ for all log files.
- Observer assets MUST be resolved via observer_asset_dir(); logs via observer_log_dir().
- Supports standalone Docker deployment with /app as project root.
"""

from pathlib import Path
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)



# ============================================================
# Project Root Resolver
# ============================================================

def _resolve_project_root(start: Optional[Path] = None) -> Path:
    """
    Resolve Observer project root directory.

    Resolution rules (first match wins):
    1. Directory containing '.git' (local development)
    2. Directory containing 'pyproject.toml' (local development)
    3. Directory containing both 'src' and 'tests' (local development)
    4. Current working directory (fallback for production/standalone)
    """

    # 1️⃣ Normal Observer project resolution (local development)
    current = start.resolve() if start else Path(__file__).resolve()

    for parent in [current] + list(current.parents):
        # Skip app/observer so we resolve to repo root, not a nested app folder
        if parent.name == "observer" and parent.parent.name == "app":
            continue
        if (parent / ".git").exists():
            return parent
        if (parent / "pyproject.toml").exists():
            return parent
        if (parent / "src").exists() and (parent / "tests").exists():
            return parent

    # 2️⃣ Fallback: Return current working directory (safe for container environments)
    return Path.cwd()


# ============================================================
# Canonical Observer Paths (Single Source of Truth)
# ============================================================

def project_root() -> Path:
    """Observer project root directory"""
    return _resolve_project_root()


# ------------------------------------------------------------
# Core directories
# ------------------------------------------------------------

def src_dir() -> Path:
    return project_root() / "src"


def ops_dir() -> Path:
    return src_dir() / "ops"


def runtime_dir() -> Path:
    """
    Canonical runtime engine directory.
    (Non-ops execution core)
    """
    return src_dir() / "runtime"


def tests_dir() -> Path:
    return project_root() / "tests"


def data_dir() -> Path:
    """
    Canonical data root directory.

    Environment variable: OBSERVER_DATA_DIR
    Default: {project_root}/data
    """
    env_path = os.environ.get("OBSERVER_DATA_DIR")
    if env_path:
        path = Path(env_path)
    else:
        path = project_root() / "data"

    path = path.resolve()
    # In read-only filesystem, mkdir might fail if the path is not a volume mount.
    # We attempt it but catch exceptions if it's already present or read-only.
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.debug(f"Could not create data_dir {path} (might be read-only): {e}")
    return path


def config_dir() -> Path:
    """
    Canonical config root directory.

    Resolution order:
    1. OBSERVER_CONFIG_DIR environment variable
    2. {project_root}/config
    """
    if os.environ.get("OBSERVER_CONFIG_DIR"):
        path = Path(os.environ["OBSERVER_CONFIG_DIR"])
    else:
        path = project_root() / "config"
    
    path = path.resolve()
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.debug(f"Could not create config_dir {path}: {e}")
    return path


# ------------------------------------------------------------
# Ops subdomains
# ------------------------------------------------------------

def ops_observer_dir() -> Path:
    return ops_dir() / "observer"


def ops_decision_pipeline_dir() -> Path:
    return ops_dir() / "decision_pipeline"


def ops_retention_dir() -> Path:
    return ops_dir() / "retention"


def ops_runtime_dir() -> Path:
    """
    Runtime bridge / runner layer under ops.
    """
    return ops_dir() / "runtime"


def ops_backup_dir() -> Path:
    return ops_dir() / "backup"


# ------------------------------------------------------------
# Observer-specific canonical paths
# ------------------------------------------------------------

def observer_asset_dir() -> Path:
    """
    Canonical Observer ASSET directory for JSON/JSONL artifacts.

    All observer-generated JSON/JSONL files MUST be placed here
    (not under config/). Log files go to observer_log_dir().

    Structure:
        data/assets/scalp/*.jsonl   - Track B real-time data
        data/assets/swing/*.jsonl   - Track A interval data
        data/assets/system/*.jsonl  - Gap/overflow logs
    """
    path = data_dir() / "assets"
    path.mkdir(parents=True, exist_ok=True)
    return path


def observer_asset_file(filename: str) -> Path:
    """
    Resolve a canonical observer asset file path.
    """
    return observer_asset_dir() / filename


def observer_data_dir() -> Path:
    """
    Observer runtime data directory.

    Structure (simplified):
        data/scalp/   - Ephemeral scalp data
        data/swing/   - Ephemeral swing data
    """
    # Return data_dir() directly (no /observer subdirectory)
    return data_dir()


def observer_log_dir() -> Path:
    """
    Canonical Observer log directory.

    Returns the log directory for Observer system.
    Uses log_dir() as base.
    """
    return log_dir()


# ------------------------------------------------------------
# Test-related paths (read-only usage)
# ------------------------------------------------------------

def tests_ops_dir() -> Path:
    return tests_dir() / "ops"


def tests_ops_e2e_dir() -> Path:
    return tests_ops_dir() / "e2e"


def tests_ops_decision_dir() -> Path:
    return tests_ops_dir() / "decision"


def tests_ops_observation_dir() -> Path:
    return tests_ops_dir() / "observation"


# ============================================================
# Schema / Asset canonical paths
# ============================================================

def schema_dir() -> Path:
    """
    Canonical schema root directory.

    This directory contains:
    - structural schemas
    - json definitions
    - external interface assets
    - secrets (non-versioned)

    This directory itself is NOT auto-created.
    """
    return project_root() / "schema"


def schema_secrets_dir() -> Path:
    """
    Canonical secrets directory under schema.

    This directory contains non-versioned secret assets
    such as credentials, tokens, and private keys.

    IMPORTANT:
    - This directory MUST NOT be auto-created.
    - Existence is considered an operational responsibility.
    """
    return schema_dir() / "secrets"


# ------------------------------------------------------------
# External service credentials (read-only, no auto-create)
# ------------------------------------------------------------

def google_credentials_path() -> Path:
    """
    Canonical Google API credentials path.

    Expected location:
    schema/secrets/google_credentials.json

    This function DOES NOT validate existence.
    Validation is responsibility of the consumer.
    """
    return schema_secrets_dir() / "google_credentials.json"


# ============================================================
# Docker-compatible paths (Environment variable overrides)
# ============================================================



def log_dir() -> Path:
    """
    Canonical log root directory.

    Environment variable: OBSERVER_LOG_DIR
    Default: {project_root}/logs
    """
    env_path = os.environ.get("OBSERVER_LOG_DIR")
    if env_path:
        path = Path(env_path)
    else:
        path = project_root() / "logs"
    
    path = path.resolve()
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.debug(f"Could not create log_dir {path}: {e}")
    return path


def system_log_dir() -> Path:
    """
    System log directory for gap detector and slot overflow.

    Environment variable: OBSERVER_SYSTEM_LOG_DIR
    Default: {log_dir}/system
    """
    env_path = os.environ.get("OBSERVER_SYSTEM_LOG_DIR")
    if env_path:
        path = Path(env_path)
    else:
        path = log_dir() / "system"
    path = path.resolve()
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.debug(f"Could not create system_log_dir {path}: {e}")
    return path


def maintenance_log_dir() -> Path:
    """
    Maintenance log directory.

    Environment variable: OBSERVER_MAINTENANCE_LOG_DIR
    Default: {log_dir}/maintenance
    """
    env_path = os.environ.get("OBSERVER_MAINTENANCE_LOG_DIR")
    if env_path:
        path = Path(env_path)
    else:
        path = log_dir() / "maintenance"
    path = path.resolve()
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.debug(f"Could not create maintenance_log_dir {path}: {e}")
    return path


def snapshot_dir() -> Path:
    """
    Canonical Universe/Symbol snapshot directory.

    Environment variable: OBSERVER_SNAPSHOT_DIR
    Default: {data_dir}/universe
    """
    env_path = os.environ.get("OBSERVER_SNAPSHOT_DIR")
    if env_path:
        path = Path(env_path)
    else:
        path = data_dir() / "universe"
    path = path.resolve()
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.debug(f"Could not create snapshot_dir {path}: {e}")
    return path


def kis_token_cache_dir() -> Path:
    """
    KIS API token cache directory.
    """
    env_path = os.environ.get("KIS_TOKEN_CACHE_DIR")
    if env_path:
        path = Path(env_path)
    else:
        path = data_dir() / "cache"
    path = path.resolve()
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.debug(f"Could not create kis_token_cache_dir {path}: {e}")
    return path


def env_file_path() -> Path:
    """
    Get .env file path.

    Environment variable: OBSERVER_ENV_FILE
    Default: searches common locations

    Resolution order:
    1. OBSERVER_ENV_FILE environment variable
    2. {project_root}/.env
    3. {project_root}/secrets/.env (Docker)
    """
    if env_path := os.environ.get("OBSERVER_ENV_FILE"):
        return Path(env_path)

    # Check common locations
    candidates = [
        project_root() / ".env",
        project_root() / "secrets" / ".env",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    # Default (even if not exists)
    return project_root() / ".env"
