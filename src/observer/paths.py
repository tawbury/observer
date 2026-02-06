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
# Environment Loader (RUN_MODE-based)
# ============================================================

def load_env_by_run_mode() -> dict:
    """
    RUN_MODE 환경변수를 기반으로 .env 파일을 레이어링 로드.

    로딩 순서 (override=False, 즉 먼저 로드된 값이 우선):
      1. OS 환경변수 (항상 최우선 — load_dotenv가 덮어쓰지 않음)
      2. config/.env.{RUN_MODE}  (환경별 경로/설정)
      3. config/.env.shared       (공통 설정)
      4. config/.env              (시크릿, local 모드만)

    RUN_MODE 값:
      "local"     → .env.local + .env.shared + config/.env (기본값)
      "container" → .env.container + .env.shared

    Returns:
        dict with keys: run_mode, files_loaded, files_skipped
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        logger.warning("python-dotenv not installed; skipping .env file loading")
        return {"run_mode": os.environ.get("RUN_MODE", "local"), "files_loaded": [], "files_skipped": []}

    run_mode = os.environ.get("RUN_MODE", "local")
    config_base = _resolve_project_root() / "config"

    result = {"run_mode": run_mode, "files_loaded": [], "files_skipped": []}

    # 레이어 순서: 환경별 → 공통 → 시크릿 (override=False이므로 먼저 로드된 값 우선)
    layers = [
        config_base / f".env.{run_mode}",   # 환경별 (경로, DB_HOST 등)
        config_base / ".env.shared",         # 공통 (TZ, MARKET_CODE 등)
    ]

    # local 모드: 시크릿 파일도 로드
    if run_mode == "local":
        secrets_file = config_base / ".env"
        if secrets_file.exists():
            layers.append(secrets_file)

    for env_file in layers:
        if env_file.exists():
            load_dotenv(env_file, override=False)
            result["files_loaded"].append(str(env_file))
        else:
            result["files_skipped"].append(str(env_file))

    # [로컬 모드] 상대 경로를 절대 경로로 변환
    if run_mode == "local":
        project_root = _resolve_project_root()
        path_vars = [
            "OBSERVER_DATA_DIR",
            "OBSERVER_LOG_DIR",
            "OBSERVER_SYSTEM_LOG_DIR",
            "OBSERVER_MAINTENANCE_LOG_DIR",
            "OBSERVER_CONFIG_DIR",
            "OBSERVER_SNAPSHOT_DIR",
            "KIS_TOKEN_CACHE_DIR",
        ]
        
        for var in path_vars:
            value = os.environ.get(var)
            if value and value.startswith("./"):
                # 상대 경로를 절대 경로로 변환
                abs_path = (project_root / value[2:]).resolve()
                os.environ[var] = str(abs_path)
                # 디렉토리 생성
                abs_path.mkdir(parents=True, exist_ok=True)

    logger.info(
        "Environment loaded: RUN_MODE=%s | loaded=%s | skipped=%s",
        run_mode, result["files_loaded"], result["files_skipped"],
    )
    return result


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
    Default: /opt/platform/runtime/observer/data
    """
    env_path = os.environ.get("OBSERVER_DATA_DIR")
    if env_path:
        path = Path(env_path)
    else:
        # K8S native mount point as default to avoid Read-only filesystem error
        path = Path("/opt/platform/runtime/observer/data")

    return path.resolve()


def config_dir() -> Path:
    """
    Canonical config root directory.

    Resolution order:
    1. OBSERVER_CONFIG_DIR environment variable
    2. /opt/platform/runtime/observer/config
    """
    if os.environ.get("OBSERVER_CONFIG_DIR"):
        path = Path(os.environ["OBSERVER_CONFIG_DIR"])
    else:
        path = Path("/opt/platform/runtime/observer/config")
    
    return path.resolve()


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
    return data_dir() / "assets"


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
    Default: /opt/platform/runtime/observer/logs
    """
    env_path = os.environ.get("OBSERVER_LOG_DIR")
    if env_path:
        path = Path(env_path)
    else:
        path = Path("/opt/platform/runtime/observer/logs")
    
    return path.resolve()


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
    return path.resolve()


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
    return path.resolve()


def snapshot_dir() -> Path:
    """
    Canonical Universe/Symbol snapshot directory.

    Resolution:
    1. OBSERVER_SNAPSHOT_DIR env
    2. {data_dir()}/universe
    """
    env_path = os.environ.get("OBSERVER_SNAPSHOT_DIR")
    if env_path:
        path = Path(env_path)
    else:
        path = Path("/opt/platform/runtime/observer/universe")
    
    return path.resolve()


def kis_token_cache_dir() -> Path:
    """
    KIS API token cache directory.
    """
    env_path = os.environ.get("KIS_TOKEN_CACHE_DIR")
    if env_path:
        path = Path(env_path)
    else:
        path = data_dir() / "cache"
    return path.resolve()


def env_file_path() -> Path:
    """
    Get .env file path (legacy).

    .. deprecated::
        Use load_env_by_run_mode() instead for layered env loading.

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


# ============================================================
# Execution Contract Validator
# ============================================================

def validate_execution_contract() -> None:
    """
    Validate execution contract at app startup (call once).

    Must be called AFTER logging setup is complete.
    Verifies all mount points exist and are writable, then creates
    required subdirectories.

    Failure: logging.critical() -> RuntimeError -> process exit
    -> Pod CrashLoopBackOff -> cause visible in logs + kubectl describe.
    """
    # Step 1: Mount point existence check (K8s must provide these)
    mount_points = {
        "data": data_dir(),
        "logs": log_dir(),
        "config": config_dir(),
        "universe": snapshot_dir(),
    }
    for name, path in mount_points.items():
        if not path.exists():
            msg = (
                f"FATAL: Mount point '{name}' not found at {path}. "
                f"K8s volumeMount misconfiguration."
            )
            logger.critical(msg)
            raise RuntimeError(msg)

    # Step 2: Write probe test (actual file write/delete per mount point)
    for name, path in mount_points.items():
        probe_file = path / ".write_probe"
        try:
            probe_file.write_text("probe")
            probe_file.unlink()
        except OSError as e:
            msg = (
                f"FATAL: Mount point '{name}' at {path} is not writable. "
                f"Write probe failed: {e}. Check fsGroup/securityContext."
            )
            logger.critical(msg)
            raise RuntimeError(msg) from e

    # Step 3: Create required subdirectories (fatal on failure)
    subdirs = [
        system_log_dir(),
        maintenance_log_dir(),
        kis_token_cache_dir(),
        observer_asset_dir(),
    ]
    for subdir in subdirs:
        try:
            subdir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            msg = f"FATAL: Cannot create subdirectory {subdir}: {e}"
            logger.critical(msg)
            raise RuntimeError(msg) from e

    logger.info("Execution contract validated: all mount points exist and writable")
