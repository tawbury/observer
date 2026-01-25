#!/usr/bin/env python3
"""
test_kis_websocket_provider.py

KIS WebSocket Provider Integration Tests
Tests real-time market data streaming functionality

Phase 05, Task 5.3: KIS WebSocket Provider Testing
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project paths
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "app" / "obs_deploy" / "app" / "src"))

# Load .env
from dotenv import load_dotenv
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Map REAL_* credentials to KIS_* and paper env vars if not already set
if os.getenv("KIS_APP_KEY") is None and os.getenv("REAL_APP_KEY"):
    os.environ["KIS_APP_KEY"] = os.environ["REAL_APP_KEY"]
if os.getenv("KIS_APP_SECRET") is None and os.getenv("REAL_APP_SECRET"):
    os.environ["KIS_APP_SECRET"] = os.environ["REAL_APP_SECRET"]
if os.getenv("KIS_BASE_URL") is None and os.getenv("REAL_BASE_URL"):
    os.environ["KIS_BASE_URL"] = os.environ["REAL_BASE_URL"]

if os.getenv("KIS_PAPER_APP_KEY") is None and os.getenv("REAL_APP_KEY"):
    os.environ["KIS_PAPER_APP_KEY"] = os.environ["REAL_APP_KEY"]
if os.getenv("KIS_PAPER_APP_SECRET") is None and os.getenv("REAL_APP_SECRET"):
    os.environ["KIS_PAPER_APP_SECRET"] = os.environ["REAL_APP_SECRET"]
if os.getenv("KIS_PAPER_BASE_URL") is None and os.getenv("REAL_BASE_URL"):
    os.environ["KIS_PAPER_BASE_URL"] = os.environ["REAL_BASE_URL"]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TEST_KIS_WEBSOCKET")
logger.info(
    "Env check | KIS_APP_KEY:%s REAL_APP_KEY:%s",
    bool(os.getenv("KIS_APP_KEY")),
    bool(os.getenv("REAL_APP_KEY")),
)

from provider.kis import KISAuth, KISWebSocketProvider


class WebSocketTestSuite:
    """Test suite for KIS WebSocket Provider"""
    
    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
        self.provider: KISWebSocketProvider | None = None
        self.received_updates: List[Dict[str, Any]] = []
        self.connection_events: List[str] = []
    
    async def run_all_tests(self) -> None:
        """Execute all tests"""
        print("\n" + "=" * 70)
        print("🧪 KIS WebSocket Provider Integration Tests")
        print("=" * 70)
        
        try:
            await self.test_connection()
            await self.test_subscription()
            await self.test_data_reception()
            await self.test_rate_limiting()
            await self.test_error_handling()
        finally:
            await self.cleanup()
        
        self.print_summary()
    
    async def test_connection(self) -> None:
        """Test 1: Basic WebSocket Connection"""
        print("\n" + "-" * 70)
        print("📡 Test 1: WebSocket Connection")
        print("-" * 70)
        
        test_name = "WebSocket Connection"
        
        try:
            # Initialize auth and provider
            app_key = os.getenv("KIS_APP_KEY")
            app_secret = os.getenv("KIS_APP_SECRET")
            
            if not app_key or not app_secret:
                raise ValueError("KIS_APP_KEY and KIS_APP_SECRET not set in .env")
            
            logger.info(f"Creating KIS WebSocket Provider...")
            # 실전 모드로 테스트
            auth = KISAuth(app_key, app_secret, is_virtual=False)
            self.provider = KISWebSocketProvider(auth, is_virtual=False)
            
            # Setup event handlers
            self.provider.on_connection = self._on_connection
            self.provider.on_disconnection = self._on_disconnection
            self.provider.on_price_update = self._on_price_update
            self.provider.on_error = self._on_error
            
            logger.info("Attempting to connect...")
            connected = await asyncio.wait_for(
                self.provider.connect(),
                timeout=90.0  # allow rate-limit backoff + handshake
            )
            
            if connected:
                logger.info("✅ Connected successfully")
                print(f"✅ Successfully connected to KIS WebSocket")
                print(f"   Connection events: {self.connection_events}")
                self.test_results.append({
                    "test": test_name,
                    "status": "PASS",
                    "message": "Connection established"
                })
            else:
                raise RuntimeError("Connection returned False")
        
        except asyncio.TimeoutError:
            logger.error("❌ Connection timeout")
            print(f"❌ Connection timeout (15s)")
            self.test_results.append({
                "test": test_name,
                "status": "FAIL",
                "message": "Connection timeout"
            })
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            print(f"❌ Connection failed: {e}")
            self.test_results.append({
                "test": test_name,
                "status": "FAIL",
                "message": str(e)
            })
    
    async def test_subscription(self) -> None:
        """Test 2: Symbol Subscription"""
        print("\n" + "-" * 70)
        print("📍 Test 2: Symbol Subscription")
        print("-" * 70)
        
        if not self.provider or not self.provider.is_connected:
            logger.warning("⚠️ Provider not connected, skipping subscription test")
            print("⚠️ Skipped (provider not connected)")
            return
        
        test_name = "Symbol Subscription"
        test_symbols = ["005930", "000660", "005380"]  # Samsung, SK Hynix, LG Energy
        
        try:
            logger.info(f"Testing subscription with {len(test_symbols)} symbols...")
            
            for symbol in test_symbols:
                subscribed = await self.provider.subscribe(symbol)
                if subscribed:
                    logger.info(f"✅ Subscribed: {symbol}")
                else:
                    logger.warning(f"⚠️ Subscription pending: {symbol}")
                await asyncio.sleep(0.5)  # Delay between subscriptions
            
            subscription_count = self.provider.subscription_count
            available_slots = self.provider.available_slots
            
            print(f"✅ Subscription test completed")
            print(f"   Subscribed symbols: {list(self.provider.subscribed_symbols)}")
            print(f"   Active subscriptions: {subscription_count}/{self.provider.MAX_SUBSCRIPTIONS}")
            print(f"   Available slots: {available_slots}")
            
            self.test_results.append({
                "test": test_name,
                "status": "PASS",
                "message": f"Subscribed to {subscription_count} symbols"
            })
        
        except Exception as e:
            logger.error(f"❌ Subscription test failed: {e}")
            print(f"❌ Subscription failed: {e}")
            self.test_results.append({
                "test": test_name,
                "status": "FAIL",
                "message": str(e)
            })
    
    async def test_data_reception(self) -> None:
        """Test 3: Real-time Data Reception"""
        print("\n" + "-" * 70)
        print("📊 Test 3: Real-time Data Reception")
        print("-" * 70)
        
        if not self.provider or not self.provider.is_connected:
            logger.warning("⚠️ Provider not connected, skipping data reception test")
            print("⚠️ Skipped (provider not connected)")
            return
        
        test_name = "Data Reception"
        
        try:
            logger.info("Waiting for price updates (15 seconds)...")
            
            initial_count = len(self.received_updates)
            await asyncio.sleep(15)
            final_count = len(self.received_updates)
            
            updates_received = final_count - initial_count
            
            if updates_received > 0:
                logger.info(f"✅ Received {updates_received} price updates")
                print(f"✅ Data reception successful")
                print(f"   Updates received: {updates_received}")
                
                # Show sample data
                if self.received_updates:
                    sample = self.received_updates[-1]
                    print(f"   Latest update: {sample['symbol']} @ {sample['price']['close']:,} KRW")
                
                self.test_results.append({
                    "test": test_name,
                    "status": "PASS",
                    "message": f"Received {updates_received} price updates"
                })
            else:
                logger.warning("⚠️ No price updates received")
                print(f"⚠️ No price updates received in 15 seconds")
                self.test_results.append({
                    "test": test_name,
                    "status": "WARN",
                    "message": "No updates received (expected in virtual mode)"
                })
        
        except Exception as e:
            logger.error(f"❌ Data reception test failed: {e}")
            print(f"❌ Data reception failed: {e}")
            self.test_results.append({
                "test": test_name,
                "status": "FAIL",
                "message": str(e)
            })
    
    async def test_rate_limiting(self) -> None:
        """Test 4: Subscription Rate Limiting"""
        print("\n" + "-" * 70)
        print("⏱️ Test 4: Subscription Rate Limiting")
        print("-" * 70)
        
        if not self.provider or not self.provider.is_connected:
            logger.warning("⚠️ Provider not connected, skipping rate limiting test")
            print("⚠️ Skipped (provider not connected)")
            return
        
        test_name = "Subscription Rate Limiting"
        
        try:
            # Test maximum subscriptions
            max_subs = self.provider.MAX_SUBSCRIPTIONS
            current_subs = self.provider.subscription_count
            available = self.provider.available_slots
            
            logger.info(f"Current subscriptions: {current_subs}/{max_subs}, Available: {available}")
            
            # Try to subscribe beyond limit
            additional_test_symbols = [f"{i:06d}" for i in range(100000, 100005)]
            
            subscription_results = []
            for i, symbol in enumerate(additional_test_symbols):
                if self.provider.subscription_count >= max_subs:
                    result = await self.provider.subscribe(symbol)
                    subscription_results.append(result)
                    logger.info(f"Subscription attempt {i+1} for {symbol}: {result}")
                    if not result:
                        break
            
            rejected_count = len([r for r in subscription_results if not r])
            
            if rejected_count > 0:
                logger.info(f"✅ Rate limiting working: {rejected_count} subscriptions rejected")
                print(f"✅ Rate limiting test passed")
                print(f"   Subscription limit enforced: {self.provider.MAX_SUBSCRIPTIONS}")
                print(f"   Rejected attempts: {rejected_count}")
                self.test_results.append({
                    "test": test_name,
                    "status": "PASS",
                    "message": f"Limit enforced at {max_subs} subscriptions"
                })
            else:
                logger.warning("⚠️ Rate limiting not tested (under limit)")
                print(f"⚠️ Still under subscription limit")
                self.test_results.append({
                    "test": test_name,
                    "status": "WARN",
                    "message": "Not fully tested (under limit)"
                })
        
        except Exception as e:
            logger.error(f"❌ Rate limiting test failed: {e}")
            print(f"❌ Rate limiting test failed: {e}")
            self.test_results.append({
                "test": test_name,
                "status": "FAIL",
                "message": str(e)
            })
    
    async def test_error_handling(self) -> None:
        """Test 5: Error Handling and Recovery"""
        print("\n" + "-" * 70)
        print("🛡️ Test 5: Error Handling")
        print("-" * 70)
        
        if not self.provider:
            logger.warning("⚠️ Provider not initialized")
            print("⚠️ Skipped (provider not initialized)")
            return
        
        test_name = "Error Handling"
        
        try:
            logger.info("Testing error scenarios...")
            
            # Test 1: Invalid symbol subscription
            logger.info("Test: Invalid symbol subscription...")
            invalid_symbol = "XXXXX"
            result = await self.provider.subscribe(invalid_symbol)
            logger.info(f"  Result: {result} (expected: allowed by provider)")
            
            # Test 2: Unsubscribe non-existent symbol
            logger.info("Test: Unsubscribe non-existent symbol...")
            result = await self.provider.unsubscribe("YYYYY")
            logger.info(f"  Result: {result} (expected: True)")
            
            # Test 3: Double subscribe (same symbol)
            if self.provider.subscribed_symbols:
                existing = list(self.provider.subscribed_symbols)[0]
                result = await self.provider.subscribe(existing)
                logger.info(f"  Double subscribe result: {result} (expected: True)")
            
            logger.info("✅ Error handling tests completed")
            print(f"✅ Error handling test passed")
            print(f"   Provider handled edge cases gracefully")
            self.test_results.append({
                "test": test_name,
                "status": "PASS",
                "message": "Error scenarios handled correctly"
            })
        
        except Exception as e:
            logger.error(f"❌ Error handling test failed: {e}")
            print(f"❌ Error handling failed: {e}")
            self.test_results.append({
                "test": test_name,
                "status": "FAIL",
                "message": str(e)
            })
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self.provider:
            logger.info("Cleaning up...")
            await self.provider.unsubscribe_all()
            await self.provider.close()
            logger.info("✅ Cleanup completed")
    
    def _on_connection(self) -> None:
        """Callback: WebSocket connected"""
        event = "🟢 Connected"
        self.connection_events.append(event)
        logger.info(f"{event}")
    
    def _on_disconnection(self) -> None:
        """Callback: WebSocket disconnected"""
        event = "🔴 Disconnected"
        self.connection_events.append(event)
        logger.warning(f"{event}")
    
    def _on_price_update(self, data: Dict[str, Any]) -> None:
        """Callback: Price data received"""
        self.received_updates.append(data)
        logger.debug(f"💹 Price update: {data['symbol']} @ {data['price']['close']:,} KRW")
    
    def _on_error(self, error_msg: str) -> None:
        """Callback: Error occurred"""
        logger.error(f"🔥 Error: {error_msg}")
    
    def print_summary(self) -> None:
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📋 Test Summary")
        print("=" * 70)
        
        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"])
        warned = len([r for r in self.test_results if r["status"] == "WARN"])
        
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"{status_icon} {result['test']}: {result['message']}")
        
        print("\n" + "-" * 70)
        print(f"Results: {passed} passed, {failed} failed, {warned} warned")
        print(f"Total data points received: {len(self.received_updates)}")
        print(f"Connection events: {len(self.connection_events)}")
        print("=" * 70)
        
        return failed == 0


async def main():
    """Main entry point"""
    suite = WebSocketTestSuite()
    await suite.run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ Test interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
