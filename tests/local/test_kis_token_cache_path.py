#!/usr/bin/env python3
"""
KIS token cache path test: ensure token is created under project_root/secrets/.kis_cache

Run from project root:
  python tests/local/test_kis_token_cache_path.py
  or: PYTHONPATH=src python tests/local/test_kis_token_cache_path.py
"""
import asyncio
import os
import sys
from pathlib import Path

# Resolve project root same as paths.py: skip app/observer, then .git or (src and tests)
def _find_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if parent.name == "observer" and parent.parent.name == "app":
            continue
        if (parent / ".git").exists():
            return parent
        if (parent / "pyproject.toml").exists():
            return parent
        if (parent / "src").exists() and (parent / "tests").exists():
            return parent
    return current.parents[2]  # fallback: parent of tests/

PROJECT_ROOT = _find_project_root()
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

# Force project root so cache goes to root/secrets/.kis_cache (override .env)
os.environ["OBSERVER_PROJECT_ROOT"] = str(PROJECT_ROOT)

from observer.paths import project_root, kis_token_cache_dir


async def main():
    from provider.kis.kis_auth import KISAuth

    root = project_root()
    cache_dir = kis_token_cache_dir()
    expected_file = cache_dir / "token_real.json"

    print("=" * 60)
    print("KIS token cache path test")
    print("=" * 60)
    print(f"OBSERVER_PROJECT_ROOT: {os.environ.get('OBSERVER_PROJECT_ROOT')}")
    print(f"project_root():         {root}")
    print(f"kis_token_cache_dir(): {cache_dir}")
    print(f"expected token file:   {expected_file}")
    under_root = root in cache_dir.resolve().parents or cache_dir.resolve() == root
    under_secrets = "secrets" in cache_dir.parts and ".kis_cache" in cache_dir.parts
    print(f"cache under root:       {under_root}")
    print(f"cache under secrets:   {under_secrets}")
    print()

    auth = KISAuth(is_virtual=False)
    try:
        await auth.ensure_token()
        path = auth._token_cache_path
        print(f"KISAuth _token_cache_path: {path}")
        print(f"path.resolve():            {path.resolve()}")
        print(f"exists:                   {path.exists()}")
        if path.exists():
            print(f"size:                     {path.stat().st_size} bytes")
        print()

        # Require cache under project root / secrets (no app/observer in path)
        path_resolved = path.resolve()
        assert root in path_resolved.parents or path_resolved == root, (
            f"Token cache should be under project root; got {path_resolved}"
        )
        assert "secrets" in path.parts or "secrets" in str(path), (
            f"Token cache should be under secrets/; got {path}"
        )
        assert path.exists(), f"Token file should exist: {path}"
        print("OK: token cache at root/secrets/.kis_cache and file created")
    finally:
        await auth.close()


if __name__ == "__main__":
    asyncio.run(main())
