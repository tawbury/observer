"""
Grafana Dashboard Configuration for Observer System

Purpose:
- Define Grafana dashboard in JSON format
- Configure panels for each monitoring category
- Set up visualization and alerting
- Export as importable dashboard JSON

Panels:
1. Universe - Size, creation rate, deletion rate
2. Track A - Snapshot collection speed and latency
3. Track B - Slot utilization, collection speed, triggers
4. Token - Refresh rate, validity countdown
5. Gaps - Detection rate, severity distribution
6. Rate Limiting - Token consumption, delays
7. API - Request rate, error rate, latency
8. System - Uptime, health status
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from zoneinfo import ZoneInfo


@dataclass
class DashboardPanel:
    """Grafana panel configuration"""
    title: str
    datasource: str = "Prometheus"
    type: str = "graph"  # graph, stat, table, timeseries
    x: int = 0
    y: int = 0
    width: int = 12
    height: int = 8
    queries: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Grafana panel format"""
        if self.queries is None:
            self.queries = []
        
        return {
            "type": self.type,
            "title": self.title,
            "datasource": self.datasource,
            "targets": self.queries,
            "gridPos": {
                "x": self.x,
                "y": self.y,
                "w": self.width,
                "h": self.height
            }
        }


class GrafanaDashboardBuilder:
    """Build Grafana dashboard JSON configuration"""
    
    def __init__(self, title: str = "Observer System Monitoring") -> None:
        self._tz = ZoneInfo("Asia/Seoul") if ZoneInfo else None
        self.title = title
        self.panels: List[Dict[str, Any]] = []
        self._next_y = 0
    
    # =====================================================================
    # Panel Builders
    # =====================================================================
    
    def add_universe_panels(self) -> None:
        """Add Universe monitoring panels"""
        
        # Panel 1: Universe Size (Gauge)
        self.panels.append({
            "type": "stat",
            "title": "Universe Size",
            "datasource": "Prometheus",
            "gridPos": {"x": 0, "y": self._next_y, "w": 6, "h": 8},
            "targets": [
                {
                    "expr": "observer_universe_size",
                    "legendFormat": "Current Size",
                    "refId": "A"
                }
            ],
            "options": {
                "graphMode": "area",
                "orientation": "auto",
                "textMode": "auto",
                "colorMode": "value",
                "unit": "short"
            }
        })
        
        # Panel 2: Creation/Deletion Rate (Graph)
        self.panels.append({
            "type": "timeseries",
            "title": "Universe Operations Rate",
            "datasource": "Prometheus",
            "gridPos": {"x": 6, "y": self._next_y, "w": 12, "h": 8},
            "targets": [
                {
                    "expr": "rate(observer_universe_created_total[5m])",
                    "legendFormat": "Created/sec",
                    "refId": "A"
                },
                {
                    "expr": "rate(observer_universe_deleted_total[5m])",
                    "legendFormat": "Deleted/sec",
                    "refId": "B"
                }
            ]
        })
        
        self._next_y += 8
    
    def add_track_a_panels(self) -> None:
        """Add Track A monitoring panels"""
        
        # Panel 1: Snapshot Collection Count
        self.panels.append({
            "type": "stat",
            "title": "Track A Snapshots",
            "datasource": "Prometheus",
            "gridPos": {"x": 0, "y": self._next_y, "w": 6, "h": 8},
            "targets": [
                {
                    "expr": "observer_track_a_snapshots_total",
                    "legendFormat": "Total Snapshots",
                    "refId": "A"
                }
            ],
            "options": {
                "graphMode": "area",
                "orientation": "auto",
                "textMode": "auto",
                "colorMode": "value"
            }
        })
        
        # Panel 2: Collection Duration Histogram
        self.panels.append({
            "type": "histogram",
            "title": "Track A Collection Duration",
            "datasource": "Prometheus",
            "gridPos": {"x": 6, "y": self._next_y, "w": 12, "h": 8},
            "targets": [
                {
                    "expr": "rate(observer_track_a_collection_duration_seconds_bucket[5m])",
                    "legendFormat": "{{le}}",
                    "refId": "A"
                }
            ]
        })
        
        self._next_y += 8
    
    def add_track_b_panels(self) -> None:
        """Add Track B monitoring panels"""
        
        # Panel 1: Slot Utilization (Gauge)
        self.panels.append({
            "type": "stat",
            "title": "Track B Slot Utilization",
            "datasource": "Prometheus",
            "gridPos": {"x": 0, "y": self._next_y, "w": 6, "h": 8},
            "targets": [
                {
                    "expr": "observer_track_b_slots_allocated / observer_track_b_slots_total",
                    "legendFormat": "Utilization",
                    "refId": "A"
                }
            ],
            "options": {
                "graphMode": "area",
                "colorMode": "value",
                "unit": "percentunit"
            }
        })
        
        # Panel 2: Slots Used vs Available
        self.panels.append({
            "type": "timeseries",
            "title": "Track B Slots Status",
            "datasource": "Prometheus",
            "gridPos": {"x": 6, "y": self._next_y, "w": 12, "h": 8},
            "targets": [
                {
                    "expr": "observer_track_b_slots_allocated",
                    "legendFormat": "Allocated",
                    "refId": "A"
                },
                {
                    "expr": "observer_track_b_slots_total - observer_track_b_slots_allocated",
                    "legendFormat": "Available",
                    "refId": "B"
                }
            ]
        })
        
        self._next_y += 8
        
        # Panel 3: Trigger Count and Collection Speed
        self.panels.append({
            "type": "timeseries",
            "title": "Track B Triggers and Collection Speed",
            "datasource": "Prometheus",
            "gridPos": {"x": 0, "y": self._next_y, "w": 18, "h": 8},
            "targets": [
                {
                    "expr": "rate(observer_track_b_triggers_total[5m])",
                    "legendFormat": "Triggers/sec",
                    "refId": "A"
                },
                {
                    "expr": "observer_track_b_collection_speed",
                    "legendFormat": "Collection Speed (items/sec)",
                    "refId": "B"
                }
            ]
        })
        
        self._next_y += 8
    
    def add_gap_panels(self) -> None:
        """Add Gap detection monitoring panels"""
        
        # Panel 1: Total Gaps Detected
        self.panels.append({
            "type": "stat",
            "title": "Gaps Detected (Total)",
            "datasource": "Prometheus",
            "gridPos": {"x": 0, "y": self._next_y, "w": 6, "h": 8},
            "targets": [
                {
                    "expr": "observer_gaps_detected_total",
                    "legendFormat": "Total Gaps",
                    "refId": "A"
                }
            ],
            "options": {
                "graphMode": "area",
                "colorMode": "value"
            }
        })
        
        # Panel 2: Gaps by Severity
        self.panels.append({
            "type": "piechart",
            "title": "Gaps by Severity Distribution",
            "datasource": "Prometheus",
            "gridPos": {"x": 6, "y": self._next_y, "w": 6, "h": 8},
            "targets": [
                {
                    "expr": "observer_gaps_low_total",
                    "legendFormat": "Low Severity",
                    "refId": "A"
                },
                {
                    "expr": "observer_gaps_medium_total",
                    "legendFormat": "Medium Severity",
                    "refId": "B"
                },
                {
                    "expr": "observer_gaps_high_total",
                    "legendFormat": "High Severity",
                    "refId": "C"
                }
            ]
        })
        
        # Panel 3: Gap Detection Duration
        self.panels.append({
            "type": "timeseries",
            "title": "Gap Detection Duration (Histogram)",
            "datasource": "Prometheus",
            "gridPos": {"x": 12, "y": self._next_y, "w": 6, "h": 8},
            "targets": [
                {
                    "expr": "histogram_quantile(0.99, rate(observer_gap_detection_duration_seconds_bucket[5m]))",
                    "legendFormat": "p99",
                    "refId": "A"
                },
                {
                    "expr": "histogram_quantile(0.95, rate(observer_gap_detection_duration_seconds_bucket[5m]))",
                    "legendFormat": "p95",
                    "refId": "B"
                }
            ]
        })
        
        self._next_y += 8
    
    def add_rate_limiting_panels(self) -> None:
        """Add Rate Limiting monitoring panels"""
        
        # Panel 1: Token Consumption Rate
        self.panels.append({
            "type": "stat",
            "title": "Rate Limit Tokens Used",
            "datasource": "Prometheus",
            "gridPos": {"x": 0, "y": self._next_y, "w": 6, "h": 8},
            "targets": [
                {
                    "expr": "rate(observer_rate_limit_tokens_total[5m])",
                    "legendFormat": "Tokens/sec",
                    "refId": "A"
                }
            ],
            "options": {
                "graphMode": "area",
                "colorMode": "value"
            }
        })
        
        # Panel 2: Rate Limit Delays
        self.panels.append({
            "type": "timeseries",
            "title": "Rate Limit Delays",
            "datasource": "Prometheus",
            "gridPos": {"x": 6, "y": self._next_y, "w": 12, "h": 8},
            "targets": [
                {
                    "expr": "rate(observer_rate_limit_delays_total[5m])",
                    "legendFormat": "Delays/sec",
                    "refId": "A"
                },
                {
                    "expr": "histogram_quantile(0.99, rate(observer_rate_limit_delay_duration_seconds_bucket[5m]))",
                    "legendFormat": "p99 Delay (ms)",
                    "refId": "B"
                }
            ]
        })
        
        self._next_y += 8
    
    def add_api_panels(self) -> None:
        """Add API monitoring panels"""
        
        # Panel 1: API Request Rate
        self.panels.append({
            "type": "stat",
            "title": "API Requests/sec",
            "datasource": "Prometheus",
            "gridPos": {"x": 0, "y": self._next_y, "w": 6, "h": 8},
            "targets": [
                {
                    "expr": "rate(observer_api_requests_total[5m])",
                    "legendFormat": "Requests/sec",
                    "refId": "A"
                }
            ],
            "options": {
                "graphMode": "area",
                "colorMode": "value"
            }
        })
        
        # Panel 2: API Error Rate
        self.panels.append({
            "type": "stat",
            "title": "API Error Rate",
            "datasource": "Prometheus",
            "gridPos": {"x": 6, "y": self._next_y, "w": 6, "h": 8},
            "targets": [
                {
                    "expr": "rate(observer_api_errors_total[5m]) / rate(observer_api_requests_total[5m])",
                    "legendFormat": "Error Rate",
                    "refId": "A"
                }
            ],
            "options": {
                "graphMode": "area",
                "colorMode": "value",
                "unit": "percentunit"
            }
        })
        
        # Panel 3: API Latency
        self.panels.append({
            "type": "timeseries",
            "title": "API Request Latency",
            "datasource": "Prometheus",
            "gridPos": {"x": 12, "y": self._next_y, "w": 6, "h": 8},
            "targets": [
                {
                    "expr": "histogram_quantile(0.99, rate(observer_api_request_duration_seconds_bucket[5m]))",
                    "legendFormat": "p99",
                    "refId": "A"
                },
                {
                    "expr": "histogram_quantile(0.95, rate(observer_api_request_duration_seconds_bucket[5m]))",
                    "legendFormat": "p95",
                    "refId": "B"
                },
                {
                    "expr": "histogram_quantile(0.50, rate(observer_api_request_duration_seconds_bucket[5m]))",
                    "legendFormat": "p50",
                    "refId": "C"
                }
            ]
        })
        
        self._next_y += 8
    
    def add_token_panels(self) -> None:
        """Add Token monitoring panels"""
        
        # Panel 1: Token Validity Countdown
        self.panels.append({
            "type": "stat",
            "title": "Token Validity (seconds)",
            "datasource": "Prometheus",
            "gridPos": {"x": 0, "y": self._next_y, "w": 6, "h": 8},
            "targets": [
                {
                    "expr": "observer_token_validity_seconds",
                    "legendFormat": "Seconds Remaining",
                    "refId": "A"
                }
            ],
            "options": {
                "graphMode": "area",
                "colorMode": "value",
                "unit": "short",
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "red", "value": 0},
                        {"color": "yellow", "value": 3600},
                        {"color": "green", "value": 86400}
                    ]
                }
            }
        })
        
        # Panel 2: Token Refresh Rate
        self.panels.append({
            "type": "timeseries",
            "title": "Token Refresh Rate",
            "datasource": "Prometheus",
            "gridPos": {"x": 6, "y": self._next_y, "w": 12, "h": 8},
            "targets": [
                {
                    "expr": "rate(observer_token_refreshes_total[1h])",
                    "legendFormat": "Refreshes/hour",
                    "refId": "A"
                }
            ]
        })
        
        self._next_y += 8
    
    def add_system_panels(self) -> None:
        """Add System monitoring panels"""
        
        # Panel 1: System Uptime
        self.panels.append({
            "type": "stat",
            "title": "System Uptime",
            "datasource": "Prometheus",
            "gridPos": {"x": 0, "y": self._next_y, "w": 8, "h": 6},
            "targets": [
                {
                    "expr": "observer_system_uptime_seconds",
                    "legendFormat": "Uptime",
                    "refId": "A"
                }
            ],
            "options": {
                "graphMode": "area",
                "colorMode": "value",
                "unit": "s"
            }
        })
        
        # Panel 2: Health Summary (single stat)
        self.panels.append({
            "type": "stat",
            "title": "System Health",
            "datasource": "Prometheus",
            "gridPos": {"x": 8, "y": self._next_y, "w": 10, "h": 6},
            "targets": [
                {
                    "expr": "(observer_api_errors_total / observer_api_requests_total) < 0.05",
                    "legendFormat": "Healthy",
                    "refId": "A"
                }
            ],
            "options": {
                "colorMode": "value",
                "graphMode": "area",
                "unit": "percentunit"
            }
        })
        
        self._next_y += 6
    
    # =====================================================================
    # Dashboard Generation
    # =====================================================================
    
    def build_dashboard(self) -> Dict[str, Any]:
        """Build complete dashboard JSON"""
        
        return {
            "dashboard": {
                "title": self.title,
                "timezone": "Asia/Seoul",
                "panels": self.panels,
                "refresh": "30s",
                "time": {
                    "from": "now-6h",
                    "to": "now"
                },
                "templating": {
                    "list": []
                },
                "annotations": {
                    "list": []
                },
                "schemaVersion": 38,
                "version": 1,
                "gnetId": None,
                "uid": "observer-system-monitoring"
            },
            "overwrite": True
        }
    
    def build_full_dashboard(self) -> Dict[str, Any]:
        """Build dashboard with all panels"""
        
        # Add all monitoring panels
        self.add_universe_panels()
        self.add_track_a_panels()
        self.add_track_b_panels()
        self.add_gap_panels()
        self.add_rate_limiting_panels()
        self.add_api_panels()
        self.add_token_panels()
        self.add_system_panels()
        
        return self.build_dashboard()
    
    def save_dashboard(self, filepath: Path) -> None:
        """Save dashboard JSON to file"""
        dashboard_json = self.build_full_dashboard()
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(
            json.dumps(dashboard_json, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        
        print(f"✓ Dashboard saved to {filepath}")


# ---- CLI Entry Point ----

def main():
    """Generate Grafana dashboard"""
    print("\n🎨 Grafana Dashboard Builder\n")
    
    builder = GrafanaDashboardBuilder("Observer System Monitoring Dashboard")
    dashboard = builder.build_full_dashboard()
    
    # Print dashboard info
    print(f"Dashboard Title: {dashboard['dashboard']['title']}")
    print(f"Total Panels: {len(dashboard['dashboard']['panels'])}")
    print(f"Refresh Rate: {dashboard['dashboard']['refresh']}")
    
    # Save dashboard
    from observer.paths import project_root
    dashboard_file = project_root() / "docs" / "grafana_dashboard.json"
    builder.save_dashboard(dashboard_file)
    
    print("\n✅ Dashboard generation complete!")
    print(f"📊 Import this dashboard in Grafana:")
    print(f"   Configuration → Dashboards → New → Import → Upload JSON file")
    print(f"   Select: {dashboard_file}")


if __name__ == "__main__":
    main()
