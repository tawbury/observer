"""
src package

Observer system - Standalone monitoring and observation engine.

Main Components:
- observer: Core observation engine with FastAPI server
- runtime: Execution engines and orchestrators
- backup: Backup and archival operations
- retention: Data retention policies and cleanup
- maintenance: System maintenance and monitoring

Quick Start:
    import asyncio
    from observer import Observer, EventBus, JsonlFileSink

    async def main():
        event_bus = EventBus([JsonlFileSink("observer.jsonl")])
        observer = Observer(session_id="test", event_bus=event_bus)
        await observer.start()

    asyncio.run(main())
"""

from __future__ import annotations

__all__ = [
    "observer",
    "runtime",
    "backup",
    "retention",
    "maintenance",
]
