"""
Token Lifecycle Manager - Proactive token refresh and session management

Key Responsibilities:
- Daily 08:30 KST pre-market token refresh
- Proactive refresh before 24-hour expiration (23-hour threshold)
- Emergency refresh on 401 errors
- WebSocket graceful shutdown and restart
- Slot state preservation across token refreshes
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Optional, Callable, Dict, Any
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore

# Ensure paths are importable
import sys
APP_ROOT = str(Path(__file__).resolve().parents[2])
if APP_ROOT not in sys.path:
    sys.path.append(APP_ROOT)

from provider import KISAuth, ProviderEngine

log = logging.getLogger("TokenLifecycleManager")


@dataclass
class TokenLifecycleConfig:
    tz_name: str = "Asia/Seoul"
    premarket_refresh_time: time = time(8, 30)  # 08:30 KST
    proactive_refresh_hours: int = 23  # Refresh before 24h expiration
    check_interval_seconds: int = 300  # Check every 5 minutes
    emergency_retry_attempts: int = 3
    emergency_retry_delay_seconds: int = 30


class TokenLifecycleManager:
    """
    Manages KIS API token lifecycle to prevent expiration.
    
    Features:
    - Daily 08:30 KST pre-market token refresh
    - Proactive refresh at 23-hour threshold
    - Emergency refresh on 401 errors
    - WebSocket session restart with state preservation
    - Health check integration
    """
    
    def __init__(
        self,
        auth: KISAuth,
        engine: ProviderEngine,
        config: Optional[TokenLifecycleConfig] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.auth = auth
        self.engine = engine
        self.cfg = config or TokenLifecycleConfig()
        self._tz = ZoneInfo(self.cfg.tz_name) if ZoneInfo else None
        self._on_error = on_error
        self._running = False
        self._last_refresh: Optional[datetime] = None
        
    # -----------------------------------------------------
    # Lifecycle Management
    # -----------------------------------------------------
    def _now(self) -> datetime:
        if self._tz:
            return datetime.now(self._tz)
        return datetime.now()
    
    async def start(self) -> None:
        """
        Start token lifecycle manager.
        
        Main loop:
        1. Check if pre-market refresh time (08:30 KST)
        2. Check if proactive refresh needed (23h since last refresh)
        3. Execute refresh if needed
        4. Sleep until next check
        """
        log.info("TokenLifecycleManager started")
        self._running = True
        
        try:
            while self._running:
                now = self._now()
                
                # Check pre-market refresh time
                if self._should_premarket_refresh(now):
                    log.info("🕐 PRE-MARKET REFRESH TIME (08:30 KST)")
                    await self._execute_refresh(reason="pre-market scheduled")
                
                # Check proactive refresh threshold
                elif self._should_proactive_refresh():
                    log.info("⏰ PROACTIVE REFRESH (23-hour threshold)")
                    await self._execute_refresh(reason="proactive 23h threshold")
                
                else:
                    log.debug(f"Token status OK, next check in {self.cfg.check_interval_seconds}s")
                
                # Sleep until next check
                await asyncio.sleep(self.cfg.check_interval_seconds)
        
        except Exception as e:
            log.error(f"TokenLifecycleManager error: {e}", exc_info=True)
            if self._on_error:
                self._on_error(str(e))
    
    def stop(self) -> None:
        """Stop the lifecycle manager"""
        log.info("TokenLifecycleManager stopping...")
        self._running = False
    
    # -----------------------------------------------------
    # Refresh Logic
    # -----------------------------------------------------
    def _should_premarket_refresh(self, now: datetime) -> bool:
        """
        Check if current time is within pre-market refresh window.
        
        Window: 08:30 ~ 08:35 KST (5-minute window to avoid exact timing issues)
        """
        current_time = now.time()
        target_time = self.cfg.premarket_refresh_time
        
        # 5-minute window
        window_start = target_time
        window_end = (datetime.combine(now.date(), target_time) + timedelta(minutes=5)).time()
        
        # Check if already refreshed today
        if self._last_refresh:
            last_refresh_date = self._last_refresh.date()
            if last_refresh_date == now.date():
                return False
        
        return window_start <= current_time <= window_end
    
    def _should_proactive_refresh(self) -> bool:
        """
        Check if proactive refresh needed (23-hour threshold).
        
        Returns True if:
        - Last refresh was more than 23 hours ago
        - OR no refresh has occurred yet
        """
        if self._last_refresh is None:
            return True
        
        now = self._now()
        time_since_refresh = now - self._last_refresh
        threshold = timedelta(hours=self.cfg.proactive_refresh_hours)
        
        return time_since_refresh >= threshold
    
    async def _execute_refresh(self, reason: str) -> bool:
        """
        Execute token refresh with WebSocket restart.
        
        Steps:
        1. Get current slot state (for preservation)
        2. Stop WebSocket gracefully
        3. Force token refresh
        4. Start WebSocket
        5. Verify health
        6. Update last_refresh timestamp
        
        Returns:
            True if refresh successful, False otherwise
        """
        log.info(f"🔄 Starting token refresh: {reason}")
        
        try:
            # Step 1: Preserve current state (if needed)
            slot_state = await self._preserve_slot_state()
            log.debug(f"Preserved slot state: {len(slot_state)} symbols")
            
            # Step 2: Stop WebSocket gracefully
            log.info("Stopping WebSocket stream...")
            await self.engine.stop_stream()
            log.info("WebSocket stopped")
            
            # Step 3: Force token refresh
            log.info("Forcing token refresh...")
            await self.auth.force_refresh()
            log.info("Token refreshed successfully")
            
            # Step 4: Start WebSocket
            log.info("Starting WebSocket stream...")
            success = await self.engine.start_stream()
            if not success:
                log.error("Failed to start WebSocket after token refresh")
                return False
            log.info("WebSocket started")
            
            # Step 5: Restore slot state (if needed)
            if slot_state:
                await self._restore_slot_state(slot_state)
                log.info(f"Restored {len(slot_state)} symbol subscriptions")
            
            # Step 6: Verify health
            health = await self.engine.health()
            log.info(f"Health check: {health}")
            
            if not health.get("ws_connected"):
                log.error("Health check failed: WebSocket not connected")
                return False
            
            # Step 7: Update last refresh timestamp
            self._last_refresh = self._now()
            log.info(f"✅ TOKEN REFRESH COMPLETED: {reason}")
            return True
        
        except Exception as e:
            log.error(f"Token refresh failed: {e}", exc_info=True)
            if self._on_error:
                self._on_error(f"Token refresh failed: {e}")
            return False
    
    async def emergency_refresh(self, retry_attempts: Optional[int] = None) -> bool:
        """
        Emergency token refresh (e.g., on 401 errors).
        
        Retries with exponential backoff if refresh fails.
        
        Args:
            retry_attempts: Number of retry attempts (default: from config)
        
        Returns:
            True if refresh successful, False otherwise
        """
        if retry_attempts is None:
            retry_attempts = self.cfg.emergency_retry_attempts
        
        log.warning(f"🚨 EMERGENCY TOKEN REFRESH (attempts={retry_attempts})")
        
        for attempt in range(1, retry_attempts + 1):
            log.info(f"Emergency refresh attempt {attempt}/{retry_attempts}")
            
            success = await self._execute_refresh(reason=f"emergency (attempt {attempt})")
            
            if success:
                log.info("Emergency refresh successful")
                return True
            
            if attempt < retry_attempts:
                delay = self.cfg.emergency_retry_delay_seconds * (2 ** (attempt - 1))
                log.warning(f"Retry failed, waiting {delay}s before next attempt...")
                await asyncio.sleep(delay)
        
        log.error("Emergency refresh failed after all attempts")
        return False
    
    # -----------------------------------------------------
    # Slot State Preservation
    # -----------------------------------------------------
    async def _preserve_slot_state(self) -> Dict[str, Any]:
        """
        Preserve current slot state before WebSocket restart.
        
        Returns dict with currently subscribed symbols.
        """
        try:
            # Get current subscriptions from engine
            health = await self.engine.health()
            subscribed_symbols = list(getattr(self.engine, '_subs', set()))
            
            return {
                "subscriptions": subscribed_symbols,
                "subscription_count": len(subscribed_symbols),
                "preserved_at": self._now().isoformat()
            }
        except Exception as e:
            log.warning(f"Failed to preserve slot state: {e}")
            return {}
    
    async def _restore_slot_state(self, slot_state: Dict[str, Any]) -> None:
        """
        Restore slot state after WebSocket restart.
        
        Re-subscribes all symbols that were active before refresh.
        """
        try:
            subscriptions = slot_state.get("subscriptions", [])
            if not subscriptions:
                return
            
            log.info(f"Restoring {len(subscriptions)} subscriptions...")
            
            # Re-subscribe with spacing to avoid rate limits
            results = await self.engine.subscribe_many(subscriptions, spacing_sec=0.25)
            
            success_count = sum(1 for ok in results.values() if ok)
            log.info(f"Restored {success_count}/{len(subscriptions)} subscriptions")
        
        except Exception as e:
            log.error(f"Failed to restore slot state: {e}", exc_info=True)
    
    # -----------------------------------------------------
    # Status
    # -----------------------------------------------------
    def get_status(self) -> Dict[str, Any]:
        """Get lifecycle manager status"""
        return {
            "running": self._running,
            "last_refresh": self._last_refresh.isoformat() if self._last_refresh else None,
            "hours_since_refresh": (
                (self._now() - self._last_refresh).total_seconds() / 3600
                if self._last_refresh else None
            ),
            "next_premarket_refresh": f"{self.cfg.premarket_refresh_time} KST",
            "proactive_refresh_threshold_hours": self.cfg.proactive_refresh_hours
        }


# ---- CLI for Testing ----

async def main():
    """CLI for testing TokenLifecycleManager"""
    import argparse
    from dotenv import load_dotenv
    
    parser = argparse.ArgumentParser(description="Token Lifecycle Manager Test CLI")
    parser.add_argument("--mode", choices=["PROD", "VIRTUAL"], default="VIRTUAL", help="KIS mode")
    parser.add_argument("--test-refresh", action="store_true", help="Test immediate refresh")
    parser.add_argument("--run-for", type=int, default=60, help="Run for N seconds (default: 60)")
    args = parser.parse_args()
    
    # Load .env if exists
    env_file = Path("d:/development/prj_obs/app/obs_deploy/.env")
    if env_file.exists():
        load_dotenv(env_file)
    
    # Setup
    auth = KISAuth(mode=args.mode)
    engine = ProviderEngine(auth=auth, mode=args.mode)
    
    manager = TokenLifecycleManager(auth=auth, engine=engine)
    
    if args.test_refresh:
        print("🧪 Testing immediate token refresh...")
        print()
        
        # Test immediate refresh
        success = await manager._execute_refresh(reason="test immediate refresh")
        
        if success:
            print("✅ Token refresh successful")
        else:
            print("❌ Token refresh failed")
        
        # Show status
        status = manager.get_status()
        print()
        print(f"📊 Status: {status}")
    
    else:
        print(f"🚀 Starting TokenLifecycleManager (mode={args.mode}, duration={args.run_for}s)")
        print()
        
        # Show initial status
        status = manager.get_status()
        print(f"Initial status: {status}")
        print()
        
        # Run manager for specified duration
        try:
            manager_task = asyncio.create_task(manager.start())
            
            # Wait for specified duration
            await asyncio.sleep(args.run_for)
            
            # Stop manager
            manager.stop()
            await manager_task
        
        except KeyboardInterrupt:
            print("\n⚠️ Interrupted by user")
            manager.stop()
        
        finally:
            status = manager.get_status()
            print()
            print(f"📊 Final Status: {status}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    asyncio.run(main())
