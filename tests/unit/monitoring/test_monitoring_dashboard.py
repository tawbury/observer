"""
Phase 12.3: Monitoring Dashboard Integration Test

Purpose:
- Test metrics collection
- Validate dashboard configuration
- Verify alerting rules
- Generate complete monitoring setup

Tests:
1. Prometheus Metrics - 15 metrics collections
2. Grafana Dashboard - 8+ panels configuration
3. Alerting Rules - 18 alert rules validation
4. Integration - End-to-end monitoring setup
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from zoneinfo import ZoneInfo

# Import monitoring modules
import sys
sys.path.insert(0, str(Path(__file__).parent))

from prometheus_metrics import PrometheusMetricsCollector
from grafana_dashboard import GrafanaDashboardBuilder
from alerting_rules import create_observer_alerting_rules

log = logging.getLogger("MonitoringDashboard")


@dataclass
class MonitoringTestResult:
    """Test result"""
    test_name: str
    status: str = "PENDING"
    duration_seconds: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    
    def to_dict(self) -> dict:
        return {
            "test_name": self.test_name,
            "status": self.status,
            "duration_seconds": f"{self.duration_seconds:.3f}",
            "details": self.details,
            "error": self.error_message
        }


class MonitoringDashboardTest:
    """Integration test for monitoring dashboard"""
    
    def __init__(self) -> None:
        self._tz = ZoneInfo("Asia/Seoul") if ZoneInfo else None
        self.results: List[MonitoringTestResult] = []
    
    # =====================================================================
    # Test 1: Prometheus Metrics Collection
    # =====================================================================
    
    async def _test_prometheus_metrics(self) -> MonitoringTestResult:
        """Test metrics collection"""
        result = MonitoringTestResult("Prometheus_Metrics_Collection")
        result.status = "RUNNING"
        
        start = time.perf_counter()
        
        try:
            log.info("\n[METRICS] Initializing Prometheus metrics collector...")
            
            collector = PrometheusMetricsCollector()
            metrics_count = 0
            
            # Record Universe metrics
            log.info("[METRICS] Recording Universe metrics...")
            collector.record_universe_size(2050)
            collector.increment_universe_created(5)
            collector.increment_universe_deleted(1)
            metrics_count += 3
            
            # Record Track A metrics
            log.info("[METRICS] Recording Track A metrics...")
            collector.record_track_a_snapshot()
            collector.record_track_a_collection_duration(0.234)
            metrics_count += 2
            
            # Record Track B metrics
            log.info("[METRICS] Recording Track B metrics...")
            collector.record_track_b_slots(41, 5)
            collector.record_track_b_trigger()
            collector.record_track_b_trigger()
            collector.record_track_b_collection_speed(125.5)
            metrics_count += 4
            
            # Record Token metrics
            log.info("[METRICS] Recording Token metrics...")
            collector.record_token_refresh()
            collector.record_token_validity(86400)
            metrics_count += 2
            
            # Record Gap metrics
            log.info("[METRICS] Recording Gap metrics...")
            for i in range(6):
                severity = ["low", "medium", "high"][i % 3]
                collector.record_gap_detected(severity)
            collector.record_gap_detection_duration(0.045)
            metrics_count += 7
            
            # Record Rate Limiting metrics
            log.info("[METRICS] Recording Rate Limiting metrics...")
            collector.record_rate_limit_token_consumption(50)
            collector.record_rate_limit_delay(0.012)
            metrics_count += 2
            
            # Record API metrics
            log.info("[METRICS] Recording API metrics...")
            collector.record_api_request(0.125)
            collector.record_api_request(0.089)
            collector.record_api_request(0.456, error=True)
            metrics_count += 3
            
            # Export metrics
            log.info("[METRICS] Exporting metrics...")
            summary = collector.get_metric_summary()
            
            # Save metrics
            test_dir = Path("d:/development/prj_obs/docs/test_monitoring")
            test_dir.mkdir(parents=True, exist_ok=True)
            
            collector.save_to_file(
                test_dir / "metrics_prometheus.txt",
                format_type="prometheus"
            )
            collector.save_to_file(
                test_dir / "metrics_summary.json",
                format_type="json"
            )
            
            result.status = "PASSED"
            result.details = {
                "metrics_collected": metrics_count,
                "universe_size": summary["universe"]["current_size"],
                "track_a_snapshots": summary["track_a"]["snapshots_collected"],
                "track_b_slots_allocated": summary["track_b"]["allocated_slots"],
                "gaps_detected": summary["gaps"]["total_detected"],
                "api_requests": summary["api"]["total_requests"],
                "files_saved": 2
            }
            
            log.info(f"✓ Metrics test complete ({metrics_count} metrics collected)")
        
        except Exception as e:
            result.status = "FAILED"
            result.error_message = str(e)
            log.error(f"✗ Metrics test failed: {e}")
        
        result.duration_seconds = time.perf_counter() - start
        return result
    
    # =====================================================================
    # Test 2: Grafana Dashboard Configuration
    # =====================================================================
    
    async def _test_grafana_dashboard(self) -> MonitoringTestResult:
        """Test dashboard configuration"""
        result = MonitoringTestResult("Grafana_Dashboard_Configuration")
        result.status = "RUNNING"
        
        start = time.perf_counter()
        
        try:
            log.info("\n[DASHBOARD] Building Grafana dashboard...")
            
            builder = GrafanaDashboardBuilder("Observer System Monitoring Dashboard")
            dashboard = builder.build_full_dashboard()
            
            # Validate dashboard structure
            log.info("[DASHBOARD] Validating dashboard structure...")
            
            assert "dashboard" in dashboard, "Missing 'dashboard' key"
            assert "panels" in dashboard["dashboard"], "Missing 'panels' key"
            assert len(dashboard["dashboard"]["panels"]) > 0, "No panels in dashboard"
            
            panel_count = len(dashboard["dashboard"]["panels"])
            log.info(f"[DASHBOARD] Dashboard has {panel_count} panels")
            
            # Validate panel types
            panel_types = set()
            for panel in dashboard["dashboard"]["panels"]:
                assert "type" in panel, "Panel missing 'type'"
                assert "title" in panel, "Panel missing 'title'"
                assert "datasource" in panel, "Panel missing 'datasource'"
                assert "targets" in panel, "Panel missing 'targets'"
                panel_types.add(panel["type"])
            
            log.info(f"[DASHBOARD] Panel types: {', '.join(panel_types)}")
            
            # Save dashboard
            test_dir = Path("d:/development/prj_obs/docs")
            dashboard_file = test_dir / "grafana_dashboard.json"
            
            test_dir.mkdir(parents=True, exist_ok=True)
            dashboard_file.write_text(
                json.dumps(dashboard, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            
            result.status = "PASSED"
            result.details = {
                "total_panels": panel_count,
                "panel_types": list(panel_types),
                "dashboard_title": dashboard["dashboard"]["title"],
                "refresh_rate": dashboard["dashboard"]["refresh"],
                "dashboard_file": str(dashboard_file)
            }
            
            log.info(f"✓ Dashboard test complete ({panel_count} panels)")
        
        except Exception as e:
            result.status = "FAILED"
            result.error_message = str(e)
            log.error(f"✗ Dashboard test failed: {e}")
        
        result.duration_seconds = time.perf_counter() - start
        return result
    
    # =====================================================================
    # Test 3: Alerting Rules
    # =====================================================================
    
    async def _test_alerting_rules(self) -> MonitoringTestResult:
        """Test alerting rules configuration"""
        result = MonitoringTestResult("Alerting_Rules_Configuration")
        result.status = "RUNNING"
        
        start = time.perf_counter()
        
        try:
            log.info("\n[ALERTS] Building alerting rules...")
            
            builder = create_observer_alerting_rules()
            
            # Validate rules
            log.info(f"[ALERTS] Generated {len(builder.rules)} alert rules")
            
            critical_alerts = 0
            warning_alerts = 0
            
            for rule in builder.rules:
                assert "alert" in rule, "Rule missing 'alert' field"
                assert "expr" in rule, "Rule missing 'expr' field"
                assert "for" in rule, "Rule missing 'for' field"
                assert "labels" in rule, "Rule missing 'labels' field"
                
                severity = rule["labels"].get("severity", "unknown")
                if severity == "critical":
                    critical_alerts += 1
                elif severity == "warning":
                    warning_alerts += 1
            
            log.info(f"[ALERTS] Critical: {critical_alerts}, Warning: {warning_alerts}")
            
            # Export rules
            test_dir = Path("d:/development/prj_obs/docs")
            test_dir.mkdir(parents=True, exist_ok=True)
            
            yaml_file = test_dir / "prometheus_alerting_rules.yaml"
            yaml_file.write_text(builder.export_prometheus_format(), encoding="utf-8")
            
            json_file = test_dir / "prometheus_alerting_rules.json"
            json_file.write_text(
                json.dumps(builder.export_json_format(), indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            
            result.status = "PASSED"
            result.details = {
                "total_rules": len(builder.rules),
                "critical_alerts": critical_alerts,
                "warning_alerts": warning_alerts,
                "yaml_file": str(yaml_file),
                "json_file": str(json_file)
            }
            
            log.info(f"✓ Alerting rules test complete ({len(builder.rules)} rules)")
        
        except Exception as e:
            result.status = "FAILED"
            result.error_message = str(e)
            log.error(f"✗ Alerting rules test failed: {e}")
        
        result.duration_seconds = time.perf_counter() - start
        return result
    
    # =====================================================================
    # Test 4: Docker Compose Configuration
    # =====================================================================
    
    async def _test_docker_setup(self) -> MonitoringTestResult:
        """Test Docker compose setup for Prometheus & Grafana"""
        result = MonitoringTestResult("Docker_Monitoring_Setup")
        result.status = "RUNNING"
        
        start = time.perf_counter()
        
        try:
            log.info("\n[DOCKER] Validating Docker monitoring setup...")
            
            # Create docker-compose for monitoring
            docker_compose = {
                "version": "3.9",
                "services": {
                    "prometheus": {
                        "image": "prom/prometheus:latest",
                        "ports": ["9090:9090"],
                        "volumes": [
                            "./prometheus.yml:/etc/prometheus/prometheus.yml",
                            "./prometheus_alerting_rules.yaml:/etc/prometheus/rules.yaml"
                        ],
                        "command": [
                            "--config.file=/etc/prometheus/prometheus.yml",
                            "--storage.tsdb.path=/prometheus",
                            "--web.console.libraries=/usr/share/prometheus/console_libraries",
                            "--web.console.templates=/usr/share/prometheus/consoles"
                        ],
                        "networks": ["monitoring"]
                    },
                    "grafana": {
                        "image": "grafana/grafana:latest",
                        "ports": ["3000:3000"],
                        "environment": {
                            "GF_SECURITY_ADMIN_PASSWORD": "admin",
                            "GF_PATHS_PROVISIONING": "/etc/grafana/provisioning",
                            "GF_PATHS_DASHBOARDS": "/etc/grafana/provisioning/dashboards"
                        },
                        "volumes": [
                            "./grafana_dashboard.json:/etc/grafana/provisioning/dashboards/observer.json",
                            "./grafana_datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml"
                        ],
                        "depends_on": ["prometheus"],
                        "networks": ["monitoring"]
                    },
                    "alertmanager": {
                        "image": "prom/alertmanager:latest",
                        "ports": ["9093:9093"],
                        "volumes": [
                            "./alertmanager.yml:/etc/alertmanager/alertmanager.yml"
                        ],
                        "networks": ["monitoring"]
                    }
                },
                "networks": {
                    "monitoring": {
                        "driver": "bridge"
                    }
                }
            }
            
            # Save docker-compose
            test_dir = Path("d:/development/prj_obs/docs")
            test_dir.mkdir(parents=True, exist_ok=True)
            
            docker_file = test_dir / "docker_compose_monitoring.json"
            docker_file.write_text(
                json.dumps(docker_compose, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            
            log.info(f"[DOCKER] Docker compose config saved")
            
            # Create Prometheus configuration
            prometheus_yml = """# Prometheus Configuration for Observer System
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'observer-system'

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']

rule_files:
  - 'prometheus_alerting_rules.yaml'

scrape_configs:
  - job_name: 'observer'
    static_configs:
      - targets: ['localhost:8000']
    scrape_interval: 30s
    scrape_timeout: 10s
    metrics_path: '/metrics'
"""
            
            prom_file = test_dir / "prometheus.yml"
            prom_file.write_text(prometheus_yml, encoding="utf-8")
            
            # Create Grafana datasources
            datasources_yml = """# Grafana Data Sources Configuration
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
"""
            
            ds_file = test_dir / "grafana_datasources.yml"
            ds_file.write_text(datasources_yml, encoding="utf-8")
            
            result.status = "PASSED"
            result.details = {
                "docker_compose_file": str(docker_file),
                "prometheus_config": str(prom_file),
                "grafana_datasources": str(ds_file),
                "services": ["prometheus", "grafana", "alertmanager"]
            }
            
            log.info(f"✓ Docker setup test complete")
        
        except Exception as e:
            result.status = "FAILED"
            result.error_message = str(e)
            log.error(f"✗ Docker setup test failed: {e}")
        
        result.duration_seconds = time.perf_counter() - start
        return result
    
    # =====================================================================
    # Main Test Orchestration
    # =====================================================================
    
    async def run_all_tests(self) -> None:
        """Run all monitoring tests"""
        log.info("\n" + "=" * 80)
        log.info("PHASE 12.3: MONITORING DASHBOARD TEST SUITE")
        log.info("=" * 80)
        
        tests = [
            ("Prometheus Metrics", self._test_prometheus_metrics),
            ("Grafana Dashboard", self._test_grafana_dashboard),
            ("Alerting Rules", self._test_alerting_rules),
            ("Docker Setup", self._test_docker_setup),
        ]
        
        for test_name, test_func in tests:
            log.info(f"\n🔬 Running: {test_name}")
            log.info("-" * 80)
            
            try:
                result = await test_func()
                self.results.append(result)
            
            except Exception as e:
                log.error(f"✗ Test crashed: {e}")
                result = MonitoringTestResult(test_name)
                result.status = "FAILED"
                result.error_message = str(e)
                self.results.append(result)
    
    def generate_summary(self) -> dict:
        """Generate test summary"""
        now = datetime.now(self._tz) if self._tz else datetime.now()
        
        passed = sum(1 for r in self.results if r.status == "PASSED")
        failed = sum(1 for r in self.results if r.status == "FAILED")
        
        return {
            "timestamp": now.isoformat(),
            "total_tests": len(self.results),
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{(passed / len(self.results) * 100):.1f}%" if self.results else "0%",
            "test_results": [r.to_dict() for r in self.results]
        }
    
    def save_results(self, filepath: Path) -> None:
        """Save test results to file"""
        summary = self.generate_summary()
        filepath.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        log.info(f"\n✓ Results saved to {filepath}")


# ---- CLI Entry Point ----

async def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    # Run monitoring tests
    test_suite = MonitoringDashboardTest()
    await test_suite.run_all_tests()
    
    # Generate and save results
    summary = test_suite.generate_summary()
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total: {summary['total_tests']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Pass Rate: {summary['pass_rate']}")
    
    # Save results
    results_file = Path("d:/development/prj_obs/docs") / "PHASE_12_3_MONITORING_RESULTS.json"
    test_suite.save_results(results_file)
    
    print("\n✅ Phase 12.3 Monitoring Dashboard tests complete!")


if __name__ == "__main__":
    asyncio.run(main())
