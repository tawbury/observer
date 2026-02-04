from __future__ import annotations

"""
kis_auth.py

KIS (Korea Investment & Securities) OAuth 2.0 Authentication Module

Responsibilities:
- OAuth 2.0 token issuance and renewal (Memory-First)
- Singleton pattern for shared access across the project
- Persistent aiohttp session management (Connection Pooling)
- Proactive validation with 1-hour buffer
- Emergency 401 refresh support
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
import aiohttp

logger = logging.getLogger(__name__)


class KISAuth:
    """
    KIS API OAuth 2.0 Authentication Manager (Singleton)
    
    Features:
    - Thread-safe Singleton access via get_instance()
    - Memory-only token storage (No file caching/locking)
    - Persistent aiohttp session for optimized network performance
    - Strict memory-based validation
    """
    
    _instance: Optional[KISAuth] = None
    _lock = asyncio.Lock()
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(KISAuth, cls).__new__(cls)
        return cls._instance

    @classmethod
    async def get_instance(
        cls,
        app_key: Optional[str] = None,
        app_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        is_virtual: bool = False,
    ) -> KISAuth:
        """Get or initialize the singleton instance."""
        async with cls._lock:
            if cls._instance is None or not hasattr(cls._instance, 'app_key'):
                instance = cls(app_key, app_secret, base_url, is_virtual)
                cls._instance = instance
            return cls._instance

    def __init__(
        self,
        app_key: Optional[str] = None,
        app_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        is_virtual: bool = False,
    ) -> None:
        """Initialize KIS authentication manager (called only once)."""
        # Skip if already initialized
        if hasattr(self, 'initialized') and self.initialized:
            return
            
        # Load from environment if not provided
        self.app_key = app_key or os.getenv("KIS_APP_KEY" if not is_virtual else "KIS_PAPER_APP_KEY")
        self.app_secret = app_secret or os.getenv("KIS_APP_SECRET" if not is_virtual else "KIS_PAPER_APP_SECRET")
        self.is_virtual = is_virtual
        self.hts_id = os.getenv("KIS_HTS_ID")
        
        # Base URLs
        default_real_url = "https://openapi.koreainvestment.com:9443"
        default_virtual_url = "https://openapivts.koreainvestment.com:29443"
        self.base_url = base_url or os.getenv(
            "KIS_BASE_URL",
            default_virtual_url if is_virtual else default_real_url
        )
        
        # Token state (Memory + File Cache)
        self.access_token: Optional[str] = None
        self.token_issued_at: Optional[datetime] = None
        self.token_expires_at: Optional[datetime] = None
        self.approval_key: Optional[str] = None

        # Token cache configuration
        cache_dir_str = os.getenv("KIS_TOKEN_CACHE_DIR", "/tmp/kis_cache")
        self.cache_dir = Path(cache_dir_str)
        self.cache_file = self.cache_dir / "token_cache.json"
        self._ensure_cache_dir()

        # Session state (Singleton Session)
        self._session: Optional[aiohttp.ClientSession] = None
        self._refresh_lock = asyncio.Lock()
        
        # Validation
        if not self.app_key or not self.app_secret:
            raise ValueError("KIS app_key and app_secret must be provided via args or ENV")
        
        self.initialized = True
        logger.info(f"KISAuth Singleton initialized (mode={'virtual' if is_virtual else 'real'})")

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create a persistent aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def _ensure_cache_dir(self) -> None:
        """Ensure cache directory exists."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Token cache directory ready: {self.cache_dir}")
        except Exception as e:
            logger.warning(f"Failed to create cache directory {self.cache_dir}: {e}")

    def _load_cached_token(self) -> Optional[Dict[str, str]]:
        """Load cached token from file if valid."""
        if not self.cache_file.exists():
            logger.debug("Token cache file does not exist")
            return None

        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate required fields
            if "access_token" not in data or "expires_at" not in data:
                logger.warning("Invalid cache file format")
                return None

            # Check expiration
            from zoneinfo import ZoneInfo
            expires_at = datetime.fromisoformat(data["expires_at"])
            now = datetime.now(ZoneInfo("Asia/Seoul"))

            # Same 1-hour buffer as memory check
            if (expires_at - now).total_seconds() < 3600:
                logger.info("Cached token expired or expiring soon")
                return None

            logger.info(f"Using cached token (expires at {expires_at.isoformat()})")
            return data

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to load token cache: {e}")
            # Delete corrupted cache file
            try:
                self.cache_file.unlink(missing_ok=True)
            except Exception:
                pass
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading token cache: {e}")
            return None

    def _save_token_cache(self, token: str, expires_at: datetime) -> None:
        """Save token to cache file."""
        try:
            data = {
                "access_token": token,
                "expires_at": expires_at.isoformat(),
                "issued_at": datetime.now().isoformat()
            }

            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Token cached successfully (expires at {expires_at.isoformat()})")

        except Exception as e:
            logger.error(f"Failed to save token cache: {e}")

    async def ensure_token(self) -> str:
        """
        Ensure valid access token is available (Memory → Cache → Refresh).
        Includes a 1-hour buffer check for proactive renewal.
        """
        # 1. Check memory first
        if self.access_token and not self._is_token_expired():
            return self.access_token

        async with self._refresh_lock:
            # Double-check inside lock
            if self.access_token and not self._is_token_expired():
                return self.access_token

            # 2. Check file cache
            cached = self._load_cached_token()
            if cached:
                self.access_token = cached["access_token"]
                from zoneinfo import ZoneInfo
                self.token_expires_at = datetime.fromisoformat(cached["expires_at"])
                self.token_issued_at = datetime.fromisoformat(cached["issued_at"])
                return self.access_token

            # 3. Refresh from API
            logger.info("Token missing or expired, refreshing from KIS API...")
            await self._refresh_token()
            return self.access_token

    def _is_token_expired(self) -> bool:
        """Check if token is expired or will expire within 1 hour."""
        if not self.access_token or not self.token_expires_at:
            return True
            
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        # Buffer of 1 hour to prevent mid-operation expiry
        return (self.token_expires_at - now).total_seconds() < 3600

    async def _refresh_token(self, force: bool = False) -> None:
        """issue/renewal of OAuth token with exponential backoff retry."""
        url = f"{self.base_url}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        data = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }
        
        max_retries = 3
        retry_delay = 60  # Start with 60s to clear KIS 1-min rate limit
        
        for attempt in range(max_retries + 1):
            try:
                session = await self.get_session()
                async with session.post(url, headers=headers, json=data) as response:
                    result = await response.json()
                    
                    if "access_token" not in result:
                        error_msg = result.get("error_description", "Unknown error")
                        error_code = result.get("error_code", "N/A")
                        # KIS often returns EGW00133 for rate limits
                        logger.warning(f"Token refresh attempt {attempt+1} failed: {error_msg} (code: {error_code})")
                        
                        if attempt < max_retries:
                            logger.info(f"Retrying in {retry_delay} seconds...")
                            await asyncio.sleep(retry_delay)
                            retry_delay *= 2 # Exponential backoff
                            continue
                        else:
                            raise RuntimeError(f"Token refresh failed after {max_retries} retries: {error_msg} (code: {error_code})")
                    
                    self.access_token = result["access_token"]
                    from zoneinfo import ZoneInfo
                    self._tz = ZoneInfo("Asia/Seoul")
                    self.token_issued_at = datetime.now(self._tz)
                    expires_in = result.get("expires_in", 86400)
                    self.token_expires_at = self.token_issued_at + timedelta(seconds=expires_in)

                    # Save to cache
                    self._save_token_cache(self.access_token, self.token_expires_at)

                    logger.info(f"Token refreshed successfully: Expires at {self.token_expires_at.isoformat()}")
                    return
            except Exception as e:
                logger.error(f"Error during KIS token refresh (attempt {attempt+1}/{max_retries+1}): {e}")
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise

    async def emergency_refresh(self) -> str:
        """Emergency force refresh (usually on 401)."""
        async with self._refresh_lock:
            logger.warning("Emergency token refresh triggered!")
            await self._refresh_token(force=True)
            return self.access_token

    def get_headers(self, tr_id: str, cust_type: str = "P") -> Dict[str, str]:
        """Generate headers with CURRENT memory token."""
        if not self.access_token:
            raise RuntimeError("Access token unavailable. Call ensure_token() first.")
        
        return {
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "custtype": cust_type,
            "content-type": "application/json; charset=utf-8",
        }

    async def get_approval_key(self) -> str:
        """Get WebSocket approval key using singleton session."""
        if self.approval_key:
            return self.approval_key
            
        await self.ensure_token()
        url = f"{self.base_url}/oauth2/Approval"
        headers = self.get_headers(tr_id="NONE") # tr_id not needed for approval usually, but we need raw token
        data = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "secretkey": self.app_secret,
        }
        
        session = await self.get_session()
        async with session.post(url, headers=headers, json=data) as response:
            result = await response.json()
            if "approval_key" in result:
                self.approval_key = result["approval_key"]
                return self.approval_key
            raise RuntimeError(f"Approval key request failed: {result}")

    async def close(self) -> None:
        """Cleanup singleton session."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("KISAuth singleton session closed")
