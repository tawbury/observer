from __future__ import annotations

import hashlib
from pathlib import Path


def calculate_sha256(path: Path) -> str:
    """
    Calculate SHA-256 checksum for a file.

    Skeleton implementation assumes small files.
    """
    sha256 = hashlib.sha256()

    with path.open("rb") as f:
        sha256.update(f.read())

    return sha256.hexdigest()
