"""Pytest conftest: add app/observer and app/observer/src to path for test discovery."""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
_src = _root / "app" / "observer" / "src"
_observer = _root / "app" / "observer"
for p in (_src, _observer):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
