#!/usr/bin/env python3
"""
Track B Docker Integration Test

이 테스트는 Docker 컨테이너 환경에서 Track B가 정상적으로 동작하는지 검증합니다:
1. WebSocket 연결 및 실시간 데이터 수신
2. 부트스트랩 심볼 기반 슬롯 할당
3. 스켈프 데이터 로깅 (config/observer/scalp/YYYYMMDD.jsonl)
4. 오버플로우 기록 (config/system/overflow_YYYYMMDD.jsonl)
5. 슬롯 관리 및 동적 교체
"""
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


class DockerIntegrationTest:
    def __init__(self, container_name: str = "observer"):
        self.container = container_name
    
    def _docker_exec(self, cmd: str) -> str:
        """Execute command in Docker container"""
        result = subprocess.run(
            f'docker exec {self.container} {cmd}',
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    
    def _docker_cp(self, container_path: str, local_path: str) -> bool:
        """Copy file from container to local"""
        result = subprocess.run(
            f'docker cp {self.container}:{container_path} {local_path}',
            shell=True,
            capture_output=True
        )
        return result.returncode == 0
    
    def test_container_health(self) -> bool:
        """Test 1: Container is running and healthy"""
        print("\n" + "="*70)
        print("Test 1: Container Health Check")
        print("="*70)
        
        # Check if container is running
        result = subprocess.run(
            'docker ps --filter "name=observer" --format "{{.Status}}"',
            shell=True,
            capture_output=True,
            text=True
        )
        
        status = result.stdout.strip()
        print(f"📊 Container status: {status}")
        
        is_healthy = "Up" in status and "healthy" in status
        print(f"{'✅' if is_healthy else '❌'} Container health: {'healthy' if is_healthy else 'not healthy'}")
        
        return is_healthy
    
    def test_websocket_connection(self) -> bool:
        """Test 2: WebSocket connection and data reception"""
        print("\n" + "="*70)
        print("Test 2: WebSocket Connection & Real-time Data")
        print("="*70)
        
        # Check for WebSocket connection log
        logs = self._docker_exec("tail -200 /var/log/observer/system/*.log 2>/dev/null || echo 'no logs'")
        
        has_websocket = "WebSocket connected" in logs or "WS connected" in logs
        print(f"{'✅' if has_websocket else '⚠️'} WebSocket connection: {'connected' if has_websocket else 'not yet'}")
        
        # Check for price update logs
        has_updates = "price update" in logs.lower() or "callback fired" in logs.lower()
        print(f"{'✅' if has_updates else '⚠️'} Price updates: {'received' if has_updates else 'none yet'}")
        
        return has_websocket
    
    def test_scalp_log_creation(self) -> bool:
        """Test 3: Scalp log file creation and content"""
        print("\n" + "="*70)
        print("Test 3: Scalp Log File Creation")
        print("="*70)
        
        today = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d")
        log_path = f"/app/config/observer/scalp/{today}.jsonl"
        
        # Check if file exists
        result = self._docker_exec(f"ls -la {log_path}")
        exists = "No such file" not in result
        print(f"{'✅' if exists else '❌'} Scalp log exists: {log_path}")
        
        if exists:
            # Get file size
            size = self._docker_exec(f"stat -c '%s' {log_path}")
            print(f"📏 File size: {size} bytes")
            
            # Count lines
            line_count = self._docker_exec(f"wc -l < {log_path}")
            print(f"📊 Total lines: {line_count}")
            
            # Show sample entries
            sample = self._docker_exec(f"head -1 {log_path}")
            if sample:
                try:
                    data = json.loads(sample)
                    print(f"\n📝 Sample scalp log entry:")
                    print(f"  Symbol: {data.get('symbol')}")
                    print(f"  Price: {data.get('price', {}).get('current')}")
                    print(f"  Volume: {data.get('volume', {})}")
                    print(f"  Source: {data.get('source')}")
                except:
                    pass
        
        return exists
    
    def test_overflow_ledger(self) -> bool:
        """Test 4: Overflow ledger creation and content"""
        print("\n" + "="*70)
        print("Test 4: Overflow Ledger (SlotManager)")
        print("="*70)
        
        today = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d")
        overflow_path = f"/app/config/system/overflow_{today}.jsonl"
        
        # Check if file exists
        result = self._docker_exec(f"ls -la {overflow_path}")
        exists = "No such file" not in result
        print(f"{'✅' if exists else '⚠️'} Overflow ledger exists: {overflow_path}")
        
        if exists:
            # Get file size
            size = self._docker_exec(f"stat -c '%s' {overflow_path}")
            print(f"📏 File size: {size} bytes")
            
            # Count overflow events
            line_count = self._docker_exec(f"wc -l < {overflow_path}")
            print(f"📊 Overflow events recorded: {line_count}")
            
            # Show sample overflow event
            sample = self._docker_exec(f"tail -1 {overflow_path}")
            if sample:
                try:
                    data = json.loads(sample)
                    print(f"\n📝 Latest overflow event:")
                    print(f"  Symbol: {data.get('symbol')}")
                    print(f"  Trigger: {data.get('trigger_type')}")
                    print(f"  Priority: {data.get('priority_score')}")
                    print(f"  Reason: {data.get('reason')}")
                except:
                    pass
        
        return exists
    
    def test_slot_management(self) -> bool:
        """Test 5: Slot management and active subscriptions"""
        print("\n" + "="*70)
        print("Test 5: Slot Management & Dynamic Subscription")
        print("="*70)
        
        # Check container logs for slot allocation messages
        logs = self._docker_exec("tail -100 /var/log/observer/system/*.log 2>/dev/null || journalctl -u observer -n 100 2>/dev/null || echo 'logs not available'")
        
        has_slot_allocation = "Slot" in logs and ("allocated" in logs or "assigned" in logs)
        print(f"{'✅' if has_slot_allocation else '⚠️'} Slot allocation: {'active' if has_slot_allocation else 'none detected'}")
        
        # Check for bootstrap triggers
        has_bootstrap = "bootstrap" in logs.lower()
        print(f"{'✅' if has_bootstrap else '⚠️'} Bootstrap triggers: {'detected' if has_bootstrap else 'none'}")
        
        # Check for WebSocket subscriptions
        has_subscriptions = "subscrib" in logs.lower()
        print(f"{'✅' if has_subscriptions else '⚠️'} WebSocket subscriptions: {'active' if has_subscriptions else 'pending'}")
        
        return has_slot_allocation or has_subscriptions
    
    def test_database_connection(self) -> bool:
        """Test 6: Database connectivity (PostgreSQL)"""
        print("\n" + "="*70)
        print("Test 6: Database Connection")
        print("="*70)
        
        # Check PostgreSQL container
        result = subprocess.run(
            'docker ps --filter "name=observer-postgres" --format "{{.Status}}"',
            shell=True,
            capture_output=True,
            text=True
        )
        
        pg_status = result.stdout.strip()
        print(f"📊 PostgreSQL status: {pg_status}")
        
        is_healthy = "healthy" in pg_status.lower()
        print(f"{'✅' if is_healthy else '❌'} Database health: {'healthy' if is_healthy else 'not healthy'}")
        
        return is_healthy
    
    def run_all_tests(self) -> dict:
        """Run all integration tests"""
        print("\n" + "🚀 "*35)
        print("Track B Docker Integration Test Suite")
        print("🚀 "*35)
        
        results = {}
        
        # Run tests
        results['container_health'] = self.test_container_health()
        results['websocket'] = self.test_websocket_connection()
        results['scalp_log'] = self.test_scalp_log_creation()
        results['overflow'] = self.test_overflow_ledger()
        results['slots'] = self.test_slot_management()
        results['database'] = self.test_database_connection()
        
        # Summary
        print("\n" + "="*70)
        print("📊 Test Summary")
        print("="*70)
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {test_name.replace('_', ' ').title()}")
        
        passed_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        
        print(f"\n📈 Results: {passed_count}/{total_count} tests passed")
        
        # Final verdict
        print("="*70)
        if passed_count >= 4:  # At least 4/6 critical tests
            print("✅ Integration Test PASSED - Track B is operational in Docker")
            return results
        else:
            print("⚠️ Integration Test INCOMPLETE - Some checks pending")
            return results


def main():
    test = DockerIntegrationTest(container_name="observer")
    
    try:
        results = test.run_all_tests()
        
        # Wait for more logs
        print("\n⏳ Waiting 30 seconds for more logs...")
        time.sleep(30)
        
        # Re-check critical tests
        print("\n" + "="*70)
        print("📊 Re-validation (after 30s wait)")
        print("="*70)
        
        scalp_ok = test.test_scalp_log_creation()
        overflow_ok = test.test_overflow_ledger()
        
        print(f"\n{'✅' if scalp_ok and overflow_ok else '⚠️'} Critical files validated")
        
        return 0 if (scalp_ok or overflow_ok) else 1
    
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
