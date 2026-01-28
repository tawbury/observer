"""
Track B standalone test (no Track A dependency)

This test ensures TrackBCollector uses bootstrap symbols to allocate slots
and subscribe without reading Track A swing logs.
"""
import asyncio
import sys
from pathlib import Path

# Ensure app/observer/src is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app" / "observer" / "src"))

from collector.track_b_collector import TrackBCollector, TrackBConfig


class FakeEngine:
    """Minimal engine stub for unit testing."""

    def __init__(self) -> None:
        self.subscribed: list[str] = []
        self.unsubscribed: list[str] = []
        self.on_price_update = None

    async def start_stream(self) -> bool:  # pragma: no cover - not used here
        return True

    async def stop_stream(self) -> None:  # pragma: no cover - not used here
        return None

    async def subscribe(self, symbol: str) -> bool:
        self.subscribed.append(symbol)
        return True

    async def unsubscribe(self, symbol: str) -> bool:
        self.unsubscribed.append(symbol)
        return True

    async def close(self) -> None:  # pragma: no cover - not used here
        return None


def test_track_b_bootstrap_assigns_slots_without_track_a():
    """Bootstrap symbols should allocate slots and trigger overflow handling."""

    engine = FakeEngine()
    cfg = TrackBConfig(max_slots=2, bootstrap_symbols=["AAA001", "BBB002", "CCC003"], bootstrap_priority=0.9)
    collector = TrackBCollector(engine=engine, trigger_engine=None, config=cfg)

    asyncio.run(collector._check_triggers())

    assert set(engine.subscribed) == {"AAA001", "BBB002"}

    stats = collector.slot_manager.get_stats()
    assert stats["total_allocations"] == 2
    assert stats["total_overflows"] >= 1


if __name__ == "__main__":
    # Allow ad-hoc run without pytest
    try:
        test_track_b_bootstrap_assigns_slots_without_track_a()
        print("✅ Test passed")
    except AssertionError as exc:  # pragma: no cover - manual run helper
        print(f"❌ Test failed: {exc}")
        raise
