"""
Prometheus Metrics Collection Module

Purpose:
- Collect system performance metrics
- Export metrics in Prometheus format
- Track Universe, Track A/B, Token, Gap, Rate Limiting metrics

Metrics Categories:
1. Universe Metrics - Universe size, create/delete rate
2. Track A/B Metrics - Collection speed, success rate
3. Slot Metrics - Usage, allocation, trigger count
4. Token Metrics - Refresh rate, validity
5. Gap Metrics - Detection rate, severity distribution
6. Rate Limiting Metrics - Token consumption, delay distribution
7. API Metrics - Call count, latency, error rate
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from shared.timezone import ZoneInfo

log = logging.getLogger("PrometheusMetrics")


@dataclass
class MetricCounter:
    """Counter metric (monotonically increasing)"""
    name: str
    help_text: str
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)
    
    def increment(self, amount: float = 1.0) -> None:
        """Increment counter"""
        self.value += amount
    
    def get_prometheus_format(self) -> str:
        """Get Prometheus text format"""
        labels_str = ""
        if self.labels:
            items = [f'{k}="{v}"' for k, v in self.labels.items()]
            labels_str = f"{{{','.join(items)}}}"
        
        return f"{self.name}{labels_str} {self.value}"


@dataclass
class MetricGauge:
    """Gauge metric (can increase or decrease)"""
    name: str
    help_text: str
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)
    
    def set(self, value: float) -> None:
        """Set gauge value"""
        self.value = value
    
    def increment(self, amount: float = 1.0) -> None:
        """Increment gauge"""
        self.value += amount
    
    def decrement(self, amount: float = 1.0) -> None:
        """Decrement gauge"""
        self.value -= amount
    
    def get_prometheus_format(self) -> str:
        """Get Prometheus text format"""
        labels_str = ""
        if self.labels:
            items = [f'{k}="{v}"' for k, v in self.labels.items()]
            labels_str = f"{{{','.join(items)}}}"
        
        return f"{self.name}{labels_str} {self.value}"


@dataclass
class MetricHistogram:
    """Histogram metric (distribution tracking)"""
    name: str
    help_text: str
    buckets: List[float] = field(default_factory=lambda: [0.001, 0.01, 0.1, 1.0, 10.0])
    bucket_counts: Dict[float, int] = field(default_factory=dict)
    sum_value: float = 0.0
    count: int = 0
    labels: Dict[str, str] = field(default_factory=dict)
    
    def observe(self, value: float) -> None:
        """Record observation"""
        self.sum_value += value
        self.count += 1
        
        for bucket in self.buckets:
            if value <= bucket:
                self.bucket_counts[bucket] = self.bucket_counts.get(bucket, 0) + 1
    
    def get_prometheus_format(self) -> List[str]:
        """Get Prometheus text format"""
        labels_str = ""
        if self.labels:
            items = [f'{k}="{v}"' for k, v in self.labels.items()]
            labels_str = f"{{{','.join(items)}}}"
        
        lines = []
        
        # Buckets
        for bucket in sorted(self.buckets):
            count = self.bucket_counts.get(bucket, 0)
            le_labels = f'{{{",".join(list(self.labels.items()) + [("le", str(bucket))])}'  if self.labels else f'{{le="{bucket}"}}'
            lines.append(f"{self.name}_bucket{le_labels} {count}")
        
        # +Inf bucket
        inf_labels = "{le=\"+Inf\"}" if not self.labels else f'{{{",".join(self.labels.items()) + [("le", "+Inf")]}'
        lines.append(f"{self.name}_bucket{inf_labels} {self.count}")
        
        # Sum and count
        lines.append(f"{self.name}_sum{labels_str} {self.sum_value}")
        lines.append(f"{self.name}_count{labels_str} {self.count}")
        
        return lines


class PrometheusMetricsCollector:
    """
    Prometheus metrics collection and export
    
    Tracks:
    - Universe metrics (size, operations)
    - Track A/B collection metrics
    - Slot utilization and operations
    - Token lifecycle metrics
    - Gap detection metrics
    - Rate limiting metrics
    - API call metrics
    """
    
    def __init__(self) -> None:
        self._tz = ZoneInfo("Asia/Seoul") if ZoneInfo else None
        self._start_time = time.time()
        self._metrics: Dict[str, Any] = {}
        
        self._init_metrics()
    
    def _init_metrics(self) -> None:
        """Initialize all metrics"""
        
        # Universe Metrics
        self._metrics["universe_size"] = MetricGauge(
            "observer_universe_size",
            "Current universe size (number of symbols)"
        )
        
        self._metrics["universe_created_total"] = MetricCounter(
            "observer_universe_created_total",
            "Total symbols created"
        )
        
        self._metrics["universe_deleted_total"] = MetricCounter(
            "observer_universe_deleted_total",
            "Total symbols deleted"
        )
        
        # Track A Metrics
        self._metrics["track_a_snapshots_total"] = MetricCounter(
            "observer_track_a_snapshots_total",
            "Total Track A snapshots collected"
        )
        
        self._metrics["track_a_collection_duration_seconds"] = MetricHistogram(
            "observer_track_a_collection_duration_seconds",
            "Track A collection operation duration"
        )
        
        # Track B Metrics
        self._metrics["track_b_slots_total"] = MetricGauge(
            "observer_track_b_slots_total",
            "Total Track B WebSocket slots"
        )
        
        self._metrics["track_b_slots_allocated"] = MetricGauge(
            "observer_track_b_slots_allocated",
            "Allocated Track B slots"
        )
        
        self._metrics["track_b_triggers_total"] = MetricCounter(
            "observer_track_b_triggers_total",
            "Total Track B trigger events"
        )
        
        self._metrics["track_b_collection_speed"] = MetricGauge(
            "observer_track_b_collection_speed",
            "Track B collection speed (items/sec)"
        )
        
        # Token Metrics
        self._metrics["token_refreshes_total"] = MetricCounter(
            "observer_token_refreshes_total",
            "Total token refreshes"
        )
        
        self._metrics["token_validity_seconds"] = MetricGauge(
            "observer_token_validity_seconds",
            "Current token validity (seconds remaining)"
        )
        
        # Gap Detection Metrics
        self._metrics["gaps_detected_total"] = MetricCounter(
            "observer_gaps_detected_total",
            "Total gaps detected"
        )
        
        self._metrics["gaps_by_severity"] = {
            "low": MetricCounter("observer_gaps_low_total", "Low severity gaps"),
            "medium": MetricCounter("observer_gaps_medium_total", "Medium severity gaps"),
            "high": MetricCounter("observer_gaps_high_total", "High severity gaps"),
        }
        
        self._metrics["gap_detection_duration_seconds"] = MetricHistogram(
            "observer_gap_detection_duration_seconds",
            "Gap detection operation duration"
        )
        
        # Rate Limiting Metrics
        self._metrics["rate_limit_tokens_total"] = MetricCounter(
            "observer_rate_limit_tokens_total",
            "Total tokens consumed"
        )
        
        self._metrics["rate_limit_delays_total"] = MetricCounter(
            "observer_rate_limit_delays_total",
            "Total rate limit delays"
        )
        
        self._metrics["rate_limit_delay_duration_seconds"] = MetricHistogram(
            "observer_rate_limit_delay_duration_seconds",
            "Rate limit delay duration"
        )
        
        # API Metrics
        self._metrics["api_requests_total"] = MetricCounter(
            "observer_api_requests_total",
            "Total API requests"
        )
        
        self._metrics["api_request_duration_seconds"] = MetricHistogram(
            "observer_api_request_duration_seconds",
            "API request duration"
        )
        
        self._metrics["api_errors_total"] = MetricCounter(
            "observer_api_errors_total",
            "Total API errors"
        )
        
        # System Metrics
        self._metrics["system_uptime_seconds"] = MetricGauge(
            "observer_system_uptime_seconds",
            "System uptime"
        )
    
    # =====================================================================
    # Universe Metrics
    # =====================================================================
    
    def record_universe_size(self, size: int) -> None:
        """Record current universe size"""
        self._metrics["universe_size"].set(float(size))
    
    def increment_universe_created(self, count: int = 1) -> None:
        """Record symbol creation"""
        self._metrics["universe_created_total"].increment(count)
    
    def increment_universe_deleted(self, count: int = 1) -> None:
        """Record symbol deletion"""
        self._metrics["universe_deleted_total"].increment(count)
    
    # =====================================================================
    # Track A Metrics
    # =====================================================================
    
    def record_track_a_snapshot(self) -> None:
        """Record Track A snapshot collection"""
        self._metrics["track_a_snapshots_total"].increment()
    
    def record_track_a_collection_duration(self, duration_seconds: float) -> None:
        """Record Track A collection duration"""
        self._metrics["track_a_collection_duration_seconds"].observe(duration_seconds)
    
    # =====================================================================
    # Track B Metrics
    # =====================================================================
    
    def record_track_b_slots(self, total: int, allocated: int) -> None:
        """Record Track B slot status"""
        self._metrics["track_b_slots_total"].set(float(total))
        self._metrics["track_b_slots_allocated"].set(float(allocated))
    
    def record_track_b_trigger(self) -> None:
        """Record Track B trigger event"""
        self._metrics["track_b_triggers_total"].increment()
    
    def record_track_b_collection_speed(self, items_per_sec: float) -> None:
        """Record Track B collection speed"""
        self._metrics["track_b_collection_speed"].set(items_per_sec)
    
    # =====================================================================
    # Token Metrics
    # =====================================================================
    
    def record_token_refresh(self) -> None:
        """Record token refresh"""
        self._metrics["token_refreshes_total"].increment()
    
    def record_token_validity(self, seconds_remaining: float) -> None:
        """Record token validity"""
        self._metrics["token_validity_seconds"].set(seconds_remaining)
    
    # =====================================================================
    # Gap Detection Metrics
    # =====================================================================
    
    def record_gap_detected(self, severity: str) -> None:
        """Record gap detection"""
        self._metrics["gaps_detected_total"].increment()
        
        if severity in self._metrics["gaps_by_severity"]:
            self._metrics["gaps_by_severity"][severity].increment()
    
    def record_gap_detection_duration(self, duration_seconds: float) -> None:
        """Record gap detection duration"""
        self._metrics["gap_detection_duration_seconds"].observe(duration_seconds)
    
    # =====================================================================
    # Rate Limiting Metrics
    # =====================================================================
    
    def record_rate_limit_token_consumption(self, tokens: float) -> None:
        """Record token consumption"""
        self._metrics["rate_limit_tokens_total"].increment(tokens)
    
    def record_rate_limit_delay(self, delay_seconds: float) -> None:
        """Record rate limit delay"""
        self._metrics["rate_limit_delays_total"].increment()
        self._metrics["rate_limit_delay_duration_seconds"].observe(delay_seconds)
    
    # =====================================================================
    # API Metrics
    # =====================================================================
    
    def record_api_request(self, duration_seconds: float, error: bool = False) -> None:
        """Record API request"""
        self._metrics["api_requests_total"].increment()
        self._metrics["api_request_duration_seconds"].observe(duration_seconds)
        
        if error:
            self._metrics["api_errors_total"].increment()
    
    # =====================================================================
    # System Metrics
    # =====================================================================
    
    def update_uptime(self) -> None:
        """Update system uptime"""
        uptime = time.time() - self._start_time
        self._metrics["system_uptime_seconds"].set(uptime)
    
    # =====================================================================
    # Export Metrics
    # =====================================================================
    
    def export_prometheus_text(self) -> str:
        """
        Export all metrics in Prometheus text format
        
        Returns:
            Text format suitable for Prometheus scraping
        """
        lines = []
        
        # Update system metrics
        self.update_uptime()
        
        lines.append("# HELP observer_universe_size Current universe size (number of symbols)")
        lines.append("# TYPE observer_universe_size gauge")
        
        for name, metric in self._metrics.items():
            if isinstance(metric, MetricCounter):
                lines.append(f"# HELP {metric.name} {metric.help_text}")
                lines.append(f"# TYPE {metric.name} counter")
                lines.append(metric.get_prometheus_format())
            
            elif isinstance(metric, MetricGauge):
                lines.append(f"# HELP {metric.name} {metric.help_text}")
                lines.append(f"# TYPE {metric.name} gauge")
                lines.append(metric.get_prometheus_format())
            
            elif isinstance(metric, MetricHistogram):
                lines.append(f"# HELP {metric.name} {metric.help_text}")
                lines.append(f"# TYPE {metric.name} histogram")
                for line in metric.get_prometheus_format():
                    lines.append(line)
            
            elif isinstance(metric, dict):  # gaps_by_severity, etc.
                for sub_name, sub_metric in metric.items():
                    if isinstance(sub_metric, (MetricCounter, MetricGauge)):
                        lines.append(f"# HELP {sub_metric.name} {sub_metric.help_text}")
                        lines.append(f"# TYPE {sub_metric.name} counter")
                        lines.append(sub_metric.get_prometheus_format())
        
        return "\n".join(lines)
    
    def export_json(self) -> Dict[str, Any]:
        """
        Export metrics as JSON
        
        Returns:
            Dictionary with all metric values
        """
        self.update_uptime()
        
        data = {
            "timestamp": datetime.now(self._tz).isoformat() if self._tz else datetime.now().isoformat(),
            "metrics": {}
        }
        
        for name, metric in self._metrics.items():
            if isinstance(metric, (MetricCounter, MetricGauge)):
                data["metrics"][metric.name] = metric.value
            elif isinstance(metric, MetricHistogram):
                data["metrics"][metric.name] = {
                    "count": metric.count,
                    "sum": metric.sum_value,
                    "avg": metric.sum_value / metric.count if metric.count > 0 else 0,
                    "buckets": metric.bucket_counts
                }
            elif isinstance(metric, dict):
                for sub_name, sub_metric in metric.items():
                    if isinstance(sub_metric, (MetricCounter, MetricGauge)):
                        data["metrics"][sub_metric.name] = sub_metric.value
        
        return data
    
    def save_to_file(self, filepath: Path, format_type: str = "prometheus") -> None:
        """Save metrics to file"""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        if format_type == "prometheus":
            content = self.export_prometheus_text()
        else:  # json
            content = json.dumps(self.export_json(), indent=2, ensure_ascii=False)
        
        filepath.write_text(content, encoding="utf-8")
        log.info(f"✓ Metrics saved to {filepath}")
    
    def get_metric_summary(self) -> Dict[str, Any]:
        """Get metrics summary for dashboard"""
        self.update_uptime()
        
        return {
            "timestamp": datetime.now(self._tz).isoformat() if self._tz else datetime.now().isoformat(),
            "universe": {
                "current_size": int(self._metrics["universe_size"].value),
                "total_created": int(self._metrics["universe_created_total"].value),
                "total_deleted": int(self._metrics["universe_deleted_total"].value),
            },
            "track_a": {
                "snapshots_collected": int(self._metrics["track_a_snapshots_total"].value),
                "avg_collection_duration_ms": (
                    self._metrics["track_a_collection_duration_seconds"].sum_value /
                    self._metrics["track_a_collection_duration_seconds"].count * 1000
                ) if self._metrics["track_a_collection_duration_seconds"].count > 0 else 0,
            },
            "track_b": {
                "total_slots": int(self._metrics["track_b_slots_total"].value),
                "allocated_slots": int(self._metrics["track_b_slots_allocated"].value),
                "available_slots": int(
                    self._metrics["track_b_slots_total"].value -
                    self._metrics["track_b_slots_allocated"].value
                ),
                "triggers": int(self._metrics["track_b_triggers_total"].value),
                "collection_speed": self._metrics["track_b_collection_speed"].value,
            },
            "token": {
                "refreshes": int(self._metrics["token_refreshes_total"].value),
                "validity_seconds": int(self._metrics["token_validity_seconds"].value),
            },
            "gaps": {
                "total_detected": int(self._metrics["gaps_detected_total"].value),
                "low_severity": int(self._metrics["gaps_by_severity"]["low"].value),
                "medium_severity": int(self._metrics["gaps_by_severity"]["medium"].value),
                "high_severity": int(self._metrics["gaps_by_severity"]["high"].value),
                "avg_detection_duration_ms": (
                    self._metrics["gap_detection_duration_seconds"].sum_value /
                    self._metrics["gap_detection_duration_seconds"].count * 1000
                ) if self._metrics["gap_detection_duration_seconds"].count > 0 else 0,
            },
            "rate_limiting": {
                "tokens_consumed": int(self._metrics["rate_limit_tokens_total"].value),
                "total_delays": int(self._metrics["rate_limit_delays_total"].value),
                "avg_delay_duration_ms": (
                    self._metrics["rate_limit_delay_duration_seconds"].sum_value /
                    self._metrics["rate_limit_delay_duration_seconds"].count * 1000
                ) if self._metrics["rate_limit_delay_duration_seconds"].count > 0 else 0,
            },
            "api": {
                "total_requests": int(self._metrics["api_requests_total"].value),
                "total_errors": int(self._metrics["api_errors_total"].value),
                "error_rate": (
                    self._metrics["api_errors_total"].value /
                    self._metrics["api_requests_total"].value
                ) if self._metrics["api_requests_total"].value > 0 else 0,
                "avg_request_duration_ms": (
                    self._metrics["api_request_duration_seconds"].sum_value /
                    self._metrics["api_request_duration_seconds"].count * 1000
                ) if self._metrics["api_request_duration_seconds"].count > 0 else 0,
            },
            "system": {
                "uptime_seconds": int(self._metrics["system_uptime_seconds"].value),
            }
        }


# ---- CLI Entry Point ----

async def main():
    """Test metrics collector"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    print("\n🧪 Prometheus Metrics Collector Test\n")
    
    collector = PrometheusMetricsCollector()
    
    # Simulate some metric collection
    print("📊 Recording sample metrics...")
    
    # Universe metrics
    collector.record_universe_size(2050)
    collector.increment_universe_created(5)
    
    # Track A metrics
    collector.record_track_a_snapshot()
    collector.record_track_a_collection_duration(0.234)
    
    # Track B metrics
    collector.record_track_b_slots(41, 5)
    collector.record_track_b_trigger()
    collector.record_track_b_trigger()
    collector.record_track_b_collection_speed(125.5)
    
    # Token metrics
    collector.record_token_refresh()
    collector.record_token_validity(86400)
    
    # Gap metrics
    collector.record_gap_detected("low")
    collector.record_gap_detected("medium")
    collector.record_gap_detected("high")
    collector.record_gap_detected("high")
    collector.record_gap_detection_duration(0.045)
    
    # Rate limiting metrics
    collector.record_rate_limit_token_consumption(50)
    collector.record_rate_limit_delay(0.012)
    
    # API metrics
    collector.record_api_request(0.125)
    collector.record_api_request(0.089, error=False)
    collector.record_api_request(0.456, error=True)
    
    # Export and display
    print("\n" + "=" * 80)
    print("PROMETHEUS METRICS EXPORT")
    print("=" * 80)
    
    prometheus_text = collector.export_prometheus_text()
    print(prometheus_text[:1000])  # Print first 1000 chars
    print("\n... [truncated] ...\n")
    
    # Export summary
    print("=" * 80)
    print("METRICS SUMMARY")
    print("=" * 80)
    
    summary = collector.get_metric_summary()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    # Save to files
    results_dir = Path("d:/development/prj_obs/docs/test_monitoring")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    collector.save_to_file(results_dir / "metrics_prometheus.txt", format_type="prometheus")
    collector.save_to_file(results_dir / "metrics_summary.json", format_type="json")
    
    print("\n✅ Metrics collector test complete!")


if __name__ == "__main__":
    asyncio.run(main())
