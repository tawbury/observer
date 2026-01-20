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
- Observer-generated JSON / JSONL files are treated as CONFIG ASSETS.
- data/ directory is reserved for ephemeral runtime-only artifacts.
- Observer assets MUST be resolved via observer_asset_dir().
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
    1. Observer standalone mode (forced)
    2. Directory containing '.git'
    3. Directory containing 'pyproject.toml'
    4. Directory containing both 'src' and 'tests'
    """

    # 1️⃣ Observer standalone mode (explicit opt-in)
    if os.environ.get("OBSERVER_STANDALONE") == "1":
        return Path(__file__).resolve().parent

    # 2️⃣ Normal Observer project resolution
    current = start.resolve() if start else Path(__file__).resolve()

    for parent in [current] + list(current.parents):
        if (parent / ".git").exists():
            return parent
        if (parent / "pyproject.toml").exists():
            return parent
        if (parent / "src").exists() and (parent / "tests").exists():
            return parent

    raise RuntimeError("Observer project root could not be resolved")


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

    Policy:
    - This directory is reserved for ephemeral / runtime-only artifacts.
    - Long-lived JSON / JSONL assets MUST NOT be placed here.
    """
    return project_root() / "data"


def config_dir() -> Path:
    """
    Canonical config root directory.

    Policy:
    - Long-lived operational assets live here.
    """
    path = project_root() / "config"
    path.mkdir(parents=True, exist_ok=True)
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
    Canonical Observer ASSET directory.

    All observer-generated JSON / JSONL artifacts
    MUST be placed here.

    Example:
        config/observer/*.jsonl
    """
    path = config_dir() / "observer"
    path.mkdir(parents=True, exist_ok=True)
    return path


def observer_asset_file(filename: str) -> Path:
    """
    Resolve a canonical observer asset file path.
    """
    return observer_asset_dir() / filename


def observer_data_dir() -> Path:
    """
    DEPRECATED.

    Legacy observer runtime data directory.
    This path should NOT be used for new artifacts.

    Kept for backward compatibility only.
    """
    logger.warning(
        "observer_data_dir() is deprecated. "
        "Use observer_asset_dir() instead."
    )
    path = data_dir() / "observer"
    path.mkdir(parents=True, exist_ok=True)
    return path


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
