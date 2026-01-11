from __future__ import annotations

import time
from typing import Optional
from uuid import uuid4

from ops.observer.inputs import (
    IMarketDataProvider,
    MarketDataContract,
)
from ops.observer.tick_events import ITickEventProvider, TickEvent
from ops.observer.event_bus import EventBus, JsonlFileSink
from ops.observer.buffered_sink import BufferedJsonlFileSink
from ops.observer.observer import Observer
from ops.observer.snapshot import (
    ObservationSnapshot,
    build_snapshot,
    utc_now_ms,
)
from ops.observer.usage_metrics import (
    UsageMetricsCollector,
    create_default_usage_metrics,
)


class ObserverRunner:
    """
    ObserverRunner (Phase F)

    - MarketDataProvider(Mock / Replay)를 받아 Observer를 실행한다.
    - Observer 출력은 EventBus + Sink를 통해서만 이루어진다.
    - Runner는 파일 경로를 알지 못한다.
    - Supports hybrid trigger mode with optional tick event provider.
    - Collects usage metrics for cost observability (Task 05).
    """

    def __init__(
        self,
        provider: IMarketDataProvider,
        *,
        interval_sec: float = 1.0,
        max_iterations: Optional[int] = None,
        mode: str = "observation",
        session_id: Optional[str] = None,
        sink_filename: str = "market_observation.jsonl",
        tick_provider: Optional[ITickEventProvider] = None,
        hybrid_mode: bool = False,
        # Buffer configuration (Task 03)
        enable_buffering: bool = True,
        flush_interval_ms: float = 1000.0,
        max_buffer_size: int = 10000,
        # Usage metrics configuration (Task 05)
        enable_usage_metrics: bool = True,
        metrics_window_ms: int = 60_000,
    ) -> None:
        self._provider = provider
        self._interval = interval_sec
        self._max_iterations = max_iterations

        self._session_id = session_id or str(uuid4())
        self._mode = mode
        self._hybrid_mode = hybrid_mode
        self._tick_provider = tick_provider
        
        # Buffer configuration
        self._enable_buffering = enable_buffering
        self._flush_interval_ms = flush_interval_ms
        self._max_buffer_size = max_buffer_size

        # Create sink (buffered or traditional)
        if enable_buffering:
            sink = BufferedJsonlFileSink(
                sink_filename,
                flush_interval_ms=flush_interval_ms,
                max_buffer_size=max_buffer_size,
                enable_buffering=True,
            )
        else:
            sink = JsonlFileSink(sink_filename)
        
        bus = EventBus(sinks=[sink])

        self._observer = Observer(
            session_id=self._session_id,
            mode=self._mode,
            event_bus=bus,
        )
        
        # Extended meta fields tracking
        self._iteration_counter = 0
        self._last_loop_time = 0.0
        
        # Usage metrics collection (Task 05)
        self._enable_usage_metrics = enable_usage_metrics
        if enable_usage_metrics:
            self._metrics_collector = create_default_usage_metrics()
            # Override window size if specified
            if metrics_window_ms != 60_000:
                from ops.observer.usage_metrics import create_usage_metrics_collector
                self._metrics_collector = create_usage_metrics_collector(
                    window_ms=metrics_window_ms,
                    enable_metrics=True,
                )
        else:
            self._metrics_collector = None

    def run(self, auto_generate_test_ticks: bool = False) -> None:
        iteration = 0

        self._observer.start()
        
        # Start buffered sink if enabled
        if self._enable_buffering and hasattr(self._observer._event_bus._sinks[0], 'start'):
            self._observer._event_bus._sinks[0].start()
            # Set metrics collector in buffered sink
            if self._metrics_collector and hasattr(self._observer._event_bus._sinks[0], 'set_metrics_collector'):
                self._observer._event_bus._sinks[0].set_metrics_collector(self._metrics_collector)

        # Initialize tick provider if hybrid mode is enabled
        if self._hybrid_mode and self._tick_provider:
            self._tick_provider.set_callback(self._on_tick_event)
            self._tick_provider.start()

        try:
            while True:
                if self._max_iterations is not None and iteration >= self._max_iterations:
                    break

                contract: Optional[MarketDataContract] = self._provider.fetch()

                if contract is None:
                    break

                snapshot = self._build_snapshot(contract, is_tick=False)
                if snapshot is None:
                    time.sleep(self._interval)
                    continue

                self._observer.on_snapshot(snapshot)

                # Generate test ticks during run if requested (for testing only)
                if auto_generate_test_ticks and self._hybrid_mode and self._tick_provider:
                    if hasattr(self._tick_provider, 'auto_generate_ticks'):
                        self._tick_provider.auto_generate_ticks(2, 10.0)  # 2 ticks, 10ms apart

                iteration += 1
                time.sleep(self._interval)

        finally:
            # Finalize metrics collection
            if self._metrics_collector:
                self._metrics_collector.finalize()
            
            # Stop tick provider if it was started
            if self._tick_provider:
                self._tick_provider.stop()
            
            # Stop buffered sink if enabled
            if self._enable_buffering and hasattr(self._observer._event_bus._sinks[0], 'stop'):
                self._observer._event_bus._sinks[0].stop()
            
            self._observer.stop()
            try:
                self._provider.close()
            except Exception:
                pass

    def _on_tick_event(self, tick_event: TickEvent) -> None:
        """
        Handle tick events for supplemental snapshot generation.
        
        Tick-triggered snapshots are supplemental to loop snapshots
        and never replace them. No filtering or interpretation is applied.
        """
        if not self._hybrid_mode:
            return
        
        # Convert tick event to MarketDataContract format
        contract = self._tick_event_to_contract(tick_event)
        if contract is None:
            return
        
        # Build snapshot from tick event (same as loop snapshots)
        snapshot = self._build_snapshot(contract, is_tick=True)
        if snapshot is not None:
            self._observer.on_snapshot(snapshot)

    def _tick_event_to_contract(self, tick_event: TickEvent) -> Optional[MarketDataContract]:
        """Convert tick event to MarketDataContract format."""
        try:
            # Tick events should have the same structure as MarketDataContract
            return tick_event
        except Exception:
            return None

    def _build_snapshot(
        self, contract: MarketDataContract, is_tick: bool = False
    ) -> Optional[ObservationSnapshot]:
        try:
            start_time = utc_now_ms()
            
            meta = contract.get("meta", {})
            instruments = contract.get("instruments", [])

            if not instruments:
                return None

            inst = instruments[0]

            inputs = {
                "price": {
                    "open": inst["price"]["open"],
                    "high": inst["price"]["high"],
                    "low": inst["price"]["low"],
                    "close": inst["price"]["close"],
                },
                "volume": inst["volume"],
                "timestamp": inst["timestamp"],
            }

            # Calculate latency for this snapshot
            end_time = utc_now_ms()
            latency_ms = end_time - start_time

            # Record usage metrics (Task 05)
            if self._metrics_collector:
                self._metrics_collector.record_snapshot(
                    is_tick=is_tick,
                    latency_ms=latency_ms
                )

            # Determine tick source
            tick_source = None
            if is_tick:
                tick_source = meta.get("source", "tick")
            else:
                tick_source = "loop"

            # Increment iteration counter for loop snapshots
            if not is_tick:
                self._iteration_counter += 1
                self._last_loop_time = end_time

            return build_snapshot(
                session_id=self._session_id,
                mode=self._mode,
                source=meta.get("source", "market"),
                stage="raw",
                inputs=inputs,
                computed={},
                state={},
                symbol=inst.get("symbol"),
                market=meta.get("market"),
                # Extended meta fields (Scalp Extension E2)
                iteration_id=self._iteration_counter if not is_tick else None,
                loop_interval_ms=self._interval * 1000.0 if not is_tick else None,
                latency_ms=latency_ms,
                tick_source=tick_source,
                buffer_depth=None,  # Placeholder for now
                flush_reason=None,  # Placeholder for now
            )

        except Exception:
            return None

    def get_buffer_stats(self) -> dict:
        """Get buffer statistics for monitoring."""
        if not self._enable_buffering:
            return {"buffering_enabled": False}
        
        if hasattr(self._observer._event_bus._sinks[0], 'get_buffer_stats'):
            stats = self._observer._event_bus._sinks[0].get_buffer_stats()
            stats["buffering_enabled"] = True
            return stats
        
        return {"buffering_enabled": True, "stats_unavailable": True}
    
    def get_usage_metrics(self) -> dict:
        """Get current usage metrics for cost observability (Task 05)."""
        if not self._enable_usage_metrics or self._metrics_collector is None:
            return {"usage_metrics_enabled": False}
        
        return self._metrics_collector.get_current_metrics()
