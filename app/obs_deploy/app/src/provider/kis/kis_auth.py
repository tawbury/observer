from __future__ import annotations

"""
kis_auth.py

KIS (Korea Investment & Securities) OAuth 2.0 Authentication Module

Responsibilities:
- OAuth 2.0 token issuance and renewal
- Token lifecycle management (24-hour validity)
- Approval key management for WebSocket
- Authentication header generation

Token Lifecycle:
- Initial token issuance on startup
- Proactive renewal at 23-hour threshold
- Emergency renewal on 401 errors
- Pre-market refresh at 08:30 KST (optional)

Reference:
- backup/c0a7118/test_kis_api.py - Environment variable pattern
- docs/dev/archi/kis_api_specification_v1.0.md - API specification
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional
import aiohttp

logger = logging.getLogger(__name__)


class KISAuth:
    """
    KIS API OAuth 2.0 Authentication Manager
    
    Features:
    - Token issuance and automatic renewal
    - Approval key management for WebSocket
    - Thread-safe token refresh
    - Configurable for production/simulation modes
    """
    
    def __init__(
        self,
        app_key: Optional[str] = None,
        app_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        is_virtual: bool = False,
    ) -> None:
        """
        Initialize KIS authentication manager.
        
        Args:
            app_key: KIS app key (loads from env if not provided)
            app_secret: KIS app secret (loads from env if not provided)
            base_url: API base URL (loads from env if not provided)
            is_virtual: Use simulation (paper trading) mode
        """
        # Load from environment if not provided
        self.app_key = app_key or os.getenv("KIS_APP_KEY" if not is_virtual else "KIS_PAPER_APP_KEY")
        self.app_secret = app_secret or os.getenv("KIS_APP_SECRET" if not is_virtual else "KIS_PAPER_APP_SECRET")
        self.is_virtual = is_virtual
        
        # Base URLs
        default_real_url = "https://openapi.koreainvestment.com:9443"
        default_virtual_url = "https://openapivts.koreainvestment.com:29443"
        self.base_url = base_url or os.getenv(
            "KIS_BASE_URL",
            default_virtual_url if is_virtual else default_real_url
        )
        
        # Token state
        self.access_token: Optional[str] = None
        self.token_issued_at: Optional[datetime] = None
        self.token_expires_at: Optional[datetime] = None
        
        # WebSocket approval key
        self.approval_key: Optional[str] = None
        
        # Token cache file path (shared across instances)
        self._token_cache_path = self._get_token_cache_path()
        
        # Validation
        if not self.app_key or not self.app_secret:
            raise ValueError(
                "KIS app_key and app_secret must be provided either as arguments "
                "or via KIS_APP_KEY/KIS_APP_SECRET environment variables"
            )
        
        logger.info(
            "KISAuth initialized",
            extra={
                "mode": "virtual" if is_virtual else "real",
                "base_url": self.base_url,
            }
        )
    
    # ============================================================
    # Token Management
    # ============================================================
    
    async def ensure_token(self) -> str:
        """
        Ensure valid access token is available.
        
        Returns:
            Valid access token
            
        Raises:
            RuntimeError: If token refresh fails
        """
        # Try to load from cache first
        if not self.access_token:
            self._load_token_from_cache()
        
        if not self.access_token or self._is_token_expired():
            # Use file lock to prevent multiple instances from issuing tokens simultaneously
            lock_file = self._token_cache_path.parent / f"token_{self.is_virtual}.lock"
            
            # Try to acquire lock with timeout
            max_wait = 120  # 2 minutes max wait
            start_time = time.time()
            
            while (time.time() - start_time) < max_wait:
                try:
                    # Try to create lock file (atomic operation)
                    lock_fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    os.write(lock_fd, str(os.getpid()).encode())
                    os.close(lock_fd)
                    
                    try:
                        # We got the lock, check cache one more time
                        self._load_token_from_cache()
                        if self.access_token and not self._is_token_expired():
                            logger.info("Token was refreshed by another instance")
                            return self.access_token
                        
                        # Actually refresh the token
                        logger.info("Acquired token refresh lock, refreshing...")
                        await self._refresh_token()
                        return self.access_token
                        
                    finally:
                        # Release lock
                        try:
                            lock_file.unlink()
                            logger.info("Released token refresh lock")
                        except:
                            pass
                            
                except FileExistsError:
                    # Another instance holds the lock, wait and retry
                    logger.debug("Waiting for token refresh lock...")
                    await asyncio.sleep(2)
                    
                    # Try to load from cache (the other instance might have finished)
                    self._load_token_from_cache()
                    if self.access_token and not self._is_token_expired():
                        logger.info("Using token refreshed by another instance")
                        return self.access_token
            
            # Timeout waiting for lock
            raise RuntimeError("Timeout waiting for token refresh lock")
        
        return self.access_token
    
    def _is_token_expired(self) -> bool:
        """Check if current token is expired or will expire soon."""
        if not self.token_expires_at:
            return True
        
        # Consider token expired if less than 1 hour remaining
        now = datetime.now(timezone.utc)
        time_remaining = self.token_expires_at - now
        return time_remaining.total_seconds() < 3600
    
    def should_proactive_refresh(self) -> bool:
        """
        Check if token should be proactively refreshed.
        
        Returns:
            True if token age >= 23 hours
        """
        if not self.token_issued_at:
            return False
        
        age = datetime.now(timezone.utc) - self.token_issued_at
        return age.total_seconds() >= (23 * 3600)
    
    async def _refresh_token(self) -> None:
        """
        Refresh OAuth 2.0 access token.
        
        API: POST /oauth2/tokenP
        
        Raises:
            RuntimeError: If token refresh fails
        """
        url = f"{self.base_url}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        data = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }
        
        logger.info("Requesting new OAuth token...")
        
        try:
            # Attempt refresh with limited retry for EGW00133 (1/min issuance limit)
            for attempt in range(2):
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=data) as response:
                        result = await response.json()
                        
                        # Check for error
                        if "error_description" in result:
                            error_msg = result.get("error_description", "Unknown error")
                            error_code = result.get("error_code", "N/A")
                            # If token issuance frequency limit hit, wait and retry once
                            if error_code == "EGW00133" and attempt == 0:
                                wait_seconds = 65
                                logger.warning(
                                    "Token issuance rate-limited (EGW00133), waiting %ss before retry...",
                                    wait_seconds,
                                )
                                await asyncio.sleep(wait_seconds)
                                continue
                            raise RuntimeError(
                                f"Token refresh failed: {error_msg} (code: {error_code})"
                            )
                        
                        # Extract token
                        self.access_token = result["access_token"]
                        self.token_issued_at = datetime.now(timezone.utc)
                        
                        # Token expires in 24 hours
                        expires_in = result.get("expires_in", 86400)
                        self.token_expires_at = self.token_issued_at + timedelta(seconds=expires_in)
                        
                        logger.info(
                            "Token refreshed successfully",
                            extra={
                                "issued_at": self.token_issued_at.isoformat(),
                                "expires_at": self.token_expires_at.isoformat(),
                                "expires_in_hours": expires_in / 3600,
                            }
                        )
                        # Save to cache for reuse
                        self._save_token_to_cache()
                        break
            else:
                # for/else executes when no break occurred
                raise RuntimeError("Token refresh failed after retries")
        
        except aiohttp.ClientError as e:
            logger.error(f"Network error during token refresh: {e}")
            raise RuntimeError(f"Token refresh network error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {e}")
            raise RuntimeError(f"Token refresh failed: {e}") from e
    
    # ============================================================
    # WebSocket Approval Key
    # ============================================================
    
    async def get_approval_key(self) -> str:
        """
        Get WebSocket approval key.
        
        API: POST /oauth2/Approval
        
        Returns:
            Approval key for WebSocket connection
            
        Raises:
            RuntimeError: If approval key request fails
        """
        if self.approval_key:
            return self.approval_key
        
        # Ensure we have valid access token first
        await self.ensure_token()
        
        url = f"{self.base_url}/oauth2/Approval"
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }
        data = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "secretkey": self.app_secret,
        }
        
        logger.info("Requesting WebSocket approval key...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    result = await response.json()
                    
                    if "error_description" in result:
                        error_msg = result.get("error_description", "Unknown error")
                        raise RuntimeError(f"Approval key request failed: {error_msg}")
                    
                    self.approval_key = result["approval_key"]
                    logger.info("WebSocket approval key obtained successfully")
                    
                    return self.approval_key
        
        except aiohttp.ClientError as e:
            logger.error(f"Network error during approval key request: {e}")
            raise RuntimeError(f"Approval key network error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during approval key request: {e}")
            raise RuntimeError(f"Approval key request failed: {e}") from e
    
    # ============================================================
    # Header Generation
    # ============================================================
    
    def get_headers(self, tr_id: str, cust_type: str = "P") -> Dict[str, str]:
        """
        Generate standard API request headers.
        
        Args:
            tr_id: Transaction ID (API-specific)
            cust_type: Customer type ("P" for personal, "B" for business)
            
        Returns:
            Dictionary of HTTP headers
            
        Raises:
            RuntimeError: If no valid token is available
        """
        if not self.access_token:
            raise RuntimeError("No access token available. Call ensure_token() first.")
        
        return {
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "custtype": cust_type,
            "content-type": "application/json; charset=utf-8",
        }
    
    # ============================================================
    # Token Caching (to avoid 1/min issuance limit)
    # ============================================================
    
    def _get_token_cache_path(self) -> Path:
        """Get token cache file path."""
        cache_dir = Path.home() / ".kis_cache"
        cache_dir.mkdir(exist_ok=True)
        mode_suffix = "virtual" if self.is_virtual else "real"
        return cache_dir / f"token_{mode_suffix}.json"
    
    def _load_token_from_cache(self) -> None:
        """Load token from cache file if valid."""
        try:
            if not self._token_cache_path.exists():
                return
            
            with open(self._token_cache_path, "r") as f:
                cache = json.load(f)
            
            # Validate cache structure
            if not all(k in cache for k in ("access_token", "issued_at", "expires_at")):
                return
            
            # Parse timestamps
            issued_at = datetime.fromisoformat(cache["issued_at"])
            expires_at = datetime.fromisoformat(cache["expires_at"])
            
            # Check if still valid (with 1-hour buffer)
            now = datetime.now(timezone.utc)
            if (expires_at - now).total_seconds() < 3600:
                logger.info("Cached token expired or expiring soon, will refresh")
                return
            
            # Load cached token
            self.access_token = cache["access_token"]
            self.token_issued_at = issued_at
            self.token_expires_at = expires_at
            
            logger.info(
                "Loaded token from cache",
                extra={
                    "issued_at": issued_at.isoformat(),
                    "expires_at": expires_at.isoformat(),
                    "remaining_hours": (expires_at - now).total_seconds() / 3600,
                }
            )
        
        except Exception as e:
            logger.warning(f"Failed to load token from cache: {e}")
    
    def _save_token_to_cache(self) -> None:
        """Save current token to cache file."""
        try:
            cache = {
                "access_token": self.access_token,
                "issued_at": self.token_issued_at.isoformat(),
                "expires_at": self.token_expires_at.isoformat(),
            }
            
            with open(self._token_cache_path, "w") as f:
                json.dump(cache, f, indent=2)
            
            logger.debug(f"Token saved to cache: {self._token_cache_path}")
        
        except Exception as e:
            logger.warning(f"Failed to save token to cache: {e}")
    
    # ============================================================
    # Lifecycle Management
    # ============================================================
    
    async def close(self) -> None:
        """Clean up resources."""
        # Token cache persists across sessions intentionally
        logger.info("KISAuth closed")
        # No persistent connections to close in this implementation
