"""
Prometheus Alerting Rules for Observer System

Purpose:
- Define alert rules for critical conditions
- Set thresholds for various metrics
- Configure alert severity levels
- Integrate with notification channels

Alert Categories:
1. System Health - Uptime, error rate
2. Universe - Size anomalies
3. Track A/B - Collection delays
4. Token - Validity warnings
5. Gaps - High severity gap detection
6. Rate Limiting - Token starvation
7. API - High latency, error spike
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Any


class AlertingRuleBuilder:
    """Build Prometheus alerting rules"""
    
    def __init__(self) -> None:
        self.rules: List[Dict[str, Any]] = []
    
    def add_rule(
        self,
        alert_name: str,
        expr: str,
        duration: str = "5m",
        severity: str = "warning",
        description: str = "",
        runbook_url: str = "",
        dashboard_url: str = ""
    ) -> None:
        """Add alerting rule"""
        
        rule = {
            "alert": alert_name,
            "expr": expr,
            "for": duration,
            "labels": {
                "severity": severity,
                "service": "observer"
            },
            "annotations": {
                "summary": f"{alert_name} triggered",
                "description": description,
                "runbook_url": runbook_url,
                "dashboard_url": dashboard_url
            }
        }
        
        self.rules.append(rule)
    
    def build_rules_group(self, group_name: str) -> Dict[str, Any]:
        """Build rules group for Prometheus configuration"""
        
        return {
            "name": group_name,
            "interval": "30s",
            "rules": self.rules
        }
    
    def export_prometheus_format(self) -> str:
        """Export as Prometheus YAML rules file"""
        
        yaml_content = """# Observer System Alerting Rules
# This file contains alerting rules for monitoring the Observer system

groups:
"""
        
        yaml_content += f"""  - name: observer_system_alerts
    interval: 30s
    rules:
"""
        
        for rule in self.rules:
            yaml_content += f"""
      - alert: {rule['alert']}
        expr: {rule['expr']}
        for: {rule['for']}
        labels:
          severity: {rule['labels']['severity']}
          service: {rule['labels']['service']}
        annotations:
          summary: {rule['annotations']['summary']}
          description: {rule['annotations']['description']}
"""
        
        return yaml_content
    
    def export_json_format(self) -> Dict[str, Any]:
        """Export as JSON"""
        
        return {
            "groups": [
                self.build_rules_group("observer_system_alerts")
            ]
        }


def create_observer_alerting_rules() -> AlertingRuleBuilder:
    """Create alerting rules for Observer system"""
    
    builder = AlertingRuleBuilder()
    
    # =====================================================================
    # System Health Alerts
    # =====================================================================
    
    builder.add_rule(
        alert_name="HighAPIErrorRate",
        expr="(rate(observer_api_errors_total[5m]) / rate(observer_api_requests_total[5m])) > 0.05",
        duration="5m",
        severity="critical",
        description="API error rate exceeds 5%",
        runbook_url="https://docs.example.com/runbook/api-errors",
        dashboard_url="https://grafana.example.com/d/observer-system"
    )
    
    builder.add_rule(
        alert_name="SystemDowntime",
        expr="observer_system_uptime_seconds < 60",
        duration="2m",
        severity="critical",
        description="System has been running for less than 1 minute",
        runbook_url="https://docs.example.com/runbook/system-restart"
    )
    
    # =====================================================================
    # Universe Alerts
    # =====================================================================
    
    builder.add_rule(
        alert_name="UniverseSizeAnomaly",
        expr="abs(observer_universe_size - avg_over_time(observer_universe_size[1h])) > avg_over_time(observer_universe_size[1h]) * 0.5",
        duration="10m",
        severity="warning",
        description="Universe size deviates significantly from average",
        runbook_url="https://docs.example.com/runbook/universe-anomaly"
    )
    
    builder.add_rule(
        alert_name="RapidUniverseExpansion",
        expr="rate(observer_universe_created_total[5m]) > 100",
        duration="5m",
        severity="warning",
        description="Universe expansion rate exceeds 100 symbols/sec",
        runbook_url="https://docs.example.com/runbook/universe-expansion"
    )
    
    # =====================================================================
    # Track A Alerts
    # =====================================================================
    
    builder.add_rule(
        alert_name="TrackACollectionDelayed",
        expr="histogram_quantile(0.99, rate(observer_track_a_collection_duration_seconds_bucket[5m])) > 1.0",
        duration="10m",
        severity="warning",
        description="Track A collection p99 latency exceeds 1 second",
        runbook_url="https://docs.example.com/runbook/track-a-latency"
    )
    
    builder.add_rule(
        alert_name="TrackANoSnapshots",
        expr="rate(observer_track_a_snapshots_total[5m]) < 0.1",
        duration="5m",
        severity="critical",
        description="Track A snapshot collection has stopped or is too slow",
        runbook_url="https://docs.example.com/runbook/track-a-stopped"
    )
    
    # =====================================================================
    # Track B Alerts
    # =====================================================================
    
    builder.add_rule(
        alert_name="TrackBSlotStarvation",
        expr="(observer_track_b_slots_allocated / observer_track_b_slots_total) > 0.95",
        duration="5m",
        severity="critical",
        description="Track B slot utilization exceeds 95%",
        runbook_url="https://docs.example.com/runbook/track-b-slots"
    )
    
    builder.add_rule(
        alert_name="TrackBCollectionSlow",
        expr="observer_track_b_collection_speed < 50",
        duration="10m",
        severity="warning",
        description="Track B collection speed drops below 50 items/sec",
        runbook_url="https://docs.example.com/runbook/track-b-speed"
    )
    
    # =====================================================================
    # Token Alerts
    # =====================================================================
    
    builder.add_rule(
        alert_name="TokenValidityLow",
        expr="observer_token_validity_seconds < 3600",
        duration="1m",
        severity="warning",
        description="Token validity less than 1 hour remaining",
        runbook_url="https://docs.example.com/runbook/token-refresh"
    )
    
    builder.add_rule(
        alert_name="TokenExpired",
        expr="observer_token_validity_seconds < 0",
        duration="1m",
        severity="critical",
        description="Token has expired",
        runbook_url="https://docs.example.com/runbook/token-expired"
    )
    
    builder.add_rule(
        alert_name="TokenRefreshFailure",
        expr="rate(observer_token_refreshes_total[1h]) < 1",
        duration="30m",
        severity="critical",
        description="Token refresh rate is abnormally low",
        runbook_url="https://docs.example.com/runbook/token-refresh-failed"
    )
    
    # =====================================================================
    # Gap Detection Alerts
    # =====================================================================
    
    builder.add_rule(
        alert_name="HighGapDetectionRate",
        expr="rate(observer_gaps_detected_total[5m]) > 10",
        duration="5m",
        severity="warning",
        description="Gap detection rate exceeds 10 gaps/sec",
        runbook_url="https://docs.example.com/runbook/gap-detection"
    )
    
    builder.add_rule(
        alert_name="HighSeverityGapsDetected",
        expr="rate(observer_gaps_high_total[5m]) > 1",
        duration="5m",
        severity="critical",
        description="High severity gaps being detected",
        runbook_url="https://docs.example.com/runbook/gap-severity"
    )
    
    builder.add_rule(
        alert_name="GapDetectionLatency",
        expr="histogram_quantile(0.99, rate(observer_gap_detection_duration_seconds_bucket[5m])) > 0.5",
        duration="10m",
        severity="warning",
        description="Gap detection p99 latency exceeds 500ms",
        runbook_url="https://docs.example.com/runbook/gap-latency"
    )
    
    # =====================================================================
    # Rate Limiting Alerts
    # =====================================================================
    
    builder.add_rule(
        alert_name="RateLimitTokenStarvation",
        expr="rate(observer_rate_limit_delays_total[5m]) > 10",
        duration="5m",
        severity="warning",
        description="High rate limiter delay rate (>10 delays/sec)",
        runbook_url="https://docs.example.com/runbook/rate-limit"
    )
    
    builder.add_rule(
        alert_name="RateLimitHighDelay",
        expr="histogram_quantile(0.99, rate(observer_rate_limit_delay_duration_seconds_bucket[5m])) > 0.1",
        duration="5m",
        severity="warning",
        description="Rate limiter p99 delay exceeds 100ms",
        runbook_url="https://docs.example.com/runbook/rate-limit-delay"
    )
    
    # =====================================================================
    # API Alerts
    # =====================================================================
    
    builder.add_rule(
        alert_name="APILatencyHigh",
        expr="histogram_quantile(0.99, rate(observer_api_request_duration_seconds_bucket[5m])) > 2.0",
        duration="10m",
        severity="warning",
        description="API request p99 latency exceeds 2 seconds",
        runbook_url="https://docs.example.com/runbook/api-latency"
    )
    
    builder.add_rule(
        alert_name="APIUnresponsive",
        expr="rate(observer_api_requests_total[5m]) < 1",
        duration="5m",
        severity="critical",
        description="API requests dropped below 1 per second",
        runbook_url="https://docs.example.com/runbook/api-unresponsive"
    )
    
    builder.add_rule(
        alert_name="APICatastrophicErrors",
        expr="(rate(observer_api_errors_total[1m]) / rate(observer_api_requests_total[1m])) > 0.5",
        duration="2m",
        severity="critical",
        description="API error rate exceeds 50% (critical condition)",
        runbook_url="https://docs.example.com/runbook/api-critical"
    )
    
    return builder


# ---- CLI Entry Point ----

def main():
    """Generate alerting rules"""
    print("\n🚨 Prometheus Alerting Rules Generator\n")
    
    builder = create_observer_alerting_rules()
    
    print(f"Generated {len(builder.rules)} alerting rules")
    print()
    
    # Display rules summary
    print("Alerting Rules Summary:")
    print("=" * 80)
    
    for rule in builder.rules:
        severity = rule['labels']['severity']
        severity_icon = "🔴" if severity == "critical" else "🟠" if severity == "warning" else "🟡"
        print(f"{severity_icon} {rule['alert']:<40} [{severity}]")
    
    # Export formats
    from observer.paths import project_root
    results_dir = project_root() / "docs"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Export YAML format
    yaml_file = results_dir / "prometheus_alerting_rules.yaml"
    yaml_file.write_text(builder.export_prometheus_format(), encoding="utf-8")
    print(f"\n✓ YAML rules exported to {yaml_file}")
    
    # Export JSON format
    json_file = results_dir / "prometheus_alerting_rules.json"
    json_file.write_text(
        json.dumps(builder.export_json_format(), indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"✓ JSON rules exported to {json_file}")
    
    print("\n✅ Alerting rules generation complete!")
    print(f"\nTo use these rules:")
    print(f"  1. Copy {yaml_file} to your Prometheus rules directory")
    print(f"  2. Update prometheus.yml to include:")
    print(f"     rule_files:")
    print(f"       - 'prometheus_alerting_rules.yaml'")
    print(f"  3. Reload Prometheus configuration")


if __name__ == "__main__":
    main()
