import os
import json
import logging
import asyncio
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Set, Optional, Dict, Any
import glob

logger = logging.getLogger("SymbolGenerator")

class SymbolGenerator:
    """
    Robust Symbol Generator with 3-Step Strategy and Retention Policy.
    
    Responsibilities:
    1. Collect symbols using 3-step strategy (API -> Master File -> Local Backup).
    2. Manage file names with AM/PM versioning.
    3. Track changes (Diff) between collection runs.
    4. Enforce 7-day data retention policy (Date + mtime).
    """
    
    def __init__(self, provider_engine, base_dir: Optional[str] = None):
        self.engine = provider_engine
        
        # [Requirement] Environment-based unified path management
        from src.observer.paths import observer_data_dir, snapshot_dir
        self.base_path = Path(base_dir) if base_dir else observer_data_dir()
        
        self.symbols_dir = self.base_path / "symbols"
        self.universe_dir = snapshot_dir()  # Align with UniverseManager's snapshot_dir
        self.backup_dir = self.base_path / "backup"
        self.cache_dir = self.base_path / "cache"  # [Requirement] Fallback to cache
        
        # [Requirement] Market code management
        market_code = os.getenv("MARKET_CODE", "kr")
        self.market_suffix = f"{market_code}_stocks"
        
        # New state and health file paths
        self.state_file = self.base_path / "last_run_state.json"
        self.health_file = self.base_path / "symbol_health.json"
        
        # [Requirement] Hard-fail on directory creation issues with specific message
        try:
            self.symbols_dir.mkdir(parents=True, exist_ok=True)
            self.universe_dir.mkdir(parents=True, exist_ok=True)
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Check write permission explicitly by creating a temporary file
            test_file = self.symbols_dir / ".write_test"
            test_file.touch()
            test_file.unlink()
            
        except (PermissionError, OSError) as e:
            logger.critical(f"[FATAL] 권한 부족: 관리자에게 {self.base_path} 폴더의 쓰기 권한 부여 요청 필요. Error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.critical(f"[FATAL] Failed to initialize directories: {e}")
            sys.exit(1)
        
        logger.info(f"[INIT] SymbolGenerator initialized at {self.symbols_dir}")

    def _get_current_tag(self) -> str:
        """Helper to get AM/PM tag for logging."""
        return "AM" if datetime.now().hour < 12 else "PM"

    async def execute(self, force: bool = False) -> Optional[str]:
        """
        High-level controller for symbol generation.
        Handles CBC (Check-Before-Collect), state check, recovery, and results reporting.
        
        :param force: If True, bypass history/file checks and force collection.
        """
        start_time = time.time()
        tag = self._get_current_tag()
        ymd = datetime.now().strftime("%Y%m%d")
        
        logger.info(f"[{tag}] Starting SymbolGenerator execution (force={force})...")
        
        # 1. Check-Before-Collect (CBC) Logic
        # [Requirement] Skip API if valid T-0 or T-1 data exists with > 2500 symbols
        # If force=True, we ignore the existence of files and proceed.
        should_run, existing_path = self.should_collect(force=force)
        
        # [Requirement] Cold Start: If no files exist (should_run=True), ignore state and force collection.
        if not should_run:
            logger.info(f"[{tag}] [CBC] Valid existing data found at {existing_path}. Skipping collection.")
            # Record Success State for consistency
            self._save_state({
                "last_ymd": ymd,
                "last_tag": tag,
                "status": "SUCCESS",
                "last_run": datetime.now().isoformat(),
                "last_filepath": existing_path
            })
            self._write_health_report(True, existing_path, 0.0)
            return existing_path

        # 2. State Check & Recovery Logic (Traditional)
        # Skip this check if should_run is True (meaning we MUST collect because files are missing)
        state = self._load_state()
        if not should_run and state.get("last_ymd") == ymd and state.get("last_tag") == tag and state.get("status") == "SUCCESS":
            logger.info(f"[{tag}] Already successfully executed for this timeslot. Skipping.")
            return state.get("last_filepath")

        try:
            filepath = await self.generate_daily_symbols()
            duration = time.time() - start_time
            
            # 2. Record Success State
            self._save_state({
                "last_ymd": ymd,
                "last_tag": tag,
                "status": "SUCCESS",
                "last_run": datetime.now().isoformat(),
                "last_filepath": filepath
            })
            
            # 3. Health Check Output
            self._write_health_report(True, filepath, duration)
            return filepath
            
        except Exception as e:
            duration = time.time() - start_time
            logger.exception(f"[{tag}] Critical failure during symbol generation")
            
            # Record Failure State
            self._save_state({
                "last_ymd": ymd,
                "last_tag": tag,
                "status": "FAILED",
                "last_run": datetime.now().isoformat(),
                "error": str(e)
            })
            
            self._write_health_report(False, None, duration, str(e))
            return None

    async def generate_daily_symbols(self) -> str:
        """
        Execute the 4-step collection strategy and save the result.
        Returns the path to the generated symbol file.
        """
        tag = "DAILY"
        logger.info(f"[{tag}] Starting daily symbol generation process (Single File Strategy)...")
        
        symbols = await self._collect_symbols_4step()
        
        if not symbols:
            logger.error(f"[{tag}] [CRITICAL] Failed to collect symbols after all steps.")
            raise RuntimeError("Failed to collect symbols.")

        # Determine filename (YYYYMMDD_kr_stocks.json)
        now = datetime.now()
        ymd = now.strftime("%Y%m%d")
        filename = f"{ymd}_{self.market_suffix}.json"
        filepath = self.symbols_dir / filename
        
        # [Requirement] Diff Update Logic
        # Load existing today's file if it exists to compare
        existing_symbols: Set[str] = set()
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                    # Support both list and dict formats
                    if isinstance(old_data, list):
                        existing_list = old_data
                    else:
                        existing_list = old_data.get("symbols", [])
                    
                    existing_symbols = set(item['code'] if isinstance(item, dict) else item for item in existing_list)
                    logger.info(f"[{tag}] Existing today's file found ({len(existing_symbols)} symbols)")
            except Exception as e:
                logger.warning(f"[{tag}] Failed to read existing file for diff: {e}")

        # Calculate Diff
        current_symbols_set = self._ensure_set(symbols)
        new_symbols = current_symbols_set - existing_symbols
        removed_symbols = existing_symbols - current_symbols_set
        
        diff_msg = f"[DIFF] New: {len(new_symbols)}, Removed: {len(removed_symbols)}, Total: {len(current_symbols_set)}"
        if new_symbols:
            diff_msg += f", New Examples: {list(new_symbols)[:3]}..."
        logger.info(f"[{tag}] {diff_msg}")

        # [Safety Logic] If fetched count is suspiciously low compared to existing, keep existing
        if len(current_symbols_set) < len(existing_symbols) * 0.5: # e.g. dropped by 50%
             logger.warning(f"[{tag}] [WARNING] New symbol count ({len(current_symbols_set)}) dropped significantly from existing ({len(existing_symbols)}). Merging to preserve data.")
             current_symbols_set.update(existing_symbols)

        # Save to JSON
        final_list = sorted(list(current_symbols_set))
        data = {
            "metadata": {
                "date": ymd,
                "generated_at": now.isoformat(),
                "count": len(final_list),
                "source_strategy": "4-Step-Strategy (SingleFile)"
            },
            "symbols": final_list
        }
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"[{tag}] Symbols saved to {filepath} ({len(final_list)} items)")
            
            # Save backup immediately
            self._save_backup(data, ymd, tag)
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"[{tag}] Failed to save symbol file: {e}")
            raise

    # Helper for saving backup in step 3 friendly format
    def _save_backup(self, data: dict, ymd: str, tag: str):
        # We keep using the specific backup naming convention if needed, or unify.
        # Let's align with main file pattern.
        filename = f"{ymd}_kr_stocks.json"
        
        # Save to local backup dir
        try:
            backup_path = self.backup_dir / filename
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
            
        # Save to cache dir (for resilience)
        if self.cache_dir:
            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                cache_path = self.cache_dir / filename
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    # [기존 코드]
    async def _collect_symbols_4step(self) -> Set[str]:
        """
        4-Step Collection Strategy (API -> Master File -> Local Backup -> Emergency Fallback).
        """
        tag = self._get_current_tag()
        
        # Step 1: KIS API with Retry
        symbols, source_step = await self._step_api_with_retry() # (A) 반환 값 변경 예정
        if symbols: 
            logger.info(f"[{tag}] 🚀 4-Step Success: Collected {len(symbols)} symbols from Step 1 (API).") # (A) 추가
            return symbols

        # Step 2: KIS Master File
        symbols, source_step = await self._step_master_file() # (A) 반환 값 변경 예정
        if symbols: 
            logger.info(f"[{tag}] 🚀 4-Step Success: Collected {len(symbols)} symbols from Step 2 (Master File).") # (A) 추가
            return symbols

        # Step 3: Local Backup (JSON Only)
        symbols, source_step = await self._step_local_backup() # (A) 반환 값 변경 예정
        if symbols: 
            logger.info(f"[{tag}] 🚀 4-Step Success: Collected {len(symbols)} symbols from Step 3 (Local Backup).") # (A) 추가
            return symbols

        # Step 4: Emergency Fallback (The Last Resort)
        symbols, source_step = await self._step_emergency_fallback() # (A) 반환 값 변경 예정
        if symbols: 
            logger.critical(f"[{tag}] ⚠️ 4-Step Fallback Success: Collected {len(symbols)} symbols from Step 4 (Emergency Fallback).") # (A) 추가
            return symbols
        
        # [기존 코드]
        logger.critical(f"[{tag}] [4-STEP FALLBACK] All collection strategies failed: API=FAIL, Master=FAIL, Backup=FAIL, Emergency=FAIL")
        return set()

#    async def _collect_symbols_4step(self) -> Set[str]:
#        """
#        4-Step Collection Strategy (API -> Master File -> Local Backup -> Emergency Fallback).
#        """
#        tag = self._get_current_tag()
        
#        # Step 1: KIS API with Retry
#        symbols = await self._step_api_with_retry()
#        if symbols: return symbols

#        # Step 2: KIS Master File
#        symbols = await self._step_master_file()
#        if symbols: return symbols

#        # Step 3: Local Backup (JSON Only)
#        symbols = await self._step_local_backup()
#        if symbols: return symbols

#        # Step 4: Emergency Fallback (The Last Resort)
#        symbols = await self._step_emergency_fallback()
#        if symbols: return symbols

#        logger.critical(f"[{tag}] [4-STEP FALLBACK] All collection strategies failed: API=FAIL, Master=FAIL, Backup=FAIL, Emergency=FAIL")
#        return set()

    # [수정 제안 코드]
    async def _step_api_with_retry(self, retries: int = 3) -> tuple[Optional[Set[str]], str]:
        """Step 1: Fetch via API with exponential backoff and count validation."""
        tag = self._get_current_tag()
        source_tag = "API"
        for attempt in range(1, retries + 1):
            try:
                logger.info(f"[{tag}] Step 1: Attempting KIS API collection (Attempt {attempt}/{retries})...")
                symbols = await self.engine.fetch_stock_list(market="ALL")
                
                count = len(symbols) if symbols else 0 # (A) 추가: 카운트 변수 생성
                
                if self._validate_symbols(symbols):
                    logger.info(f"[{tag}] Step 1 Success: {count} symbols fetched via API (Passed Quality Check).")
                    return set(symbols), source_tag
                else:
                    # [기존 코드] count 정보가 로깅에 포함되지 않음.
                    # [수정] count 정보를 포함하여 WARNING 로깅 강화
                    logger.warning(f"[{tag}] Step 1 Validation Failed: Insufficient data count ({count} < 2500).")
                    
            except Exception as e:
                logger.error(f"[{tag}] Step 1 Attempt {attempt} Failed: {e}")
                
                # [Fast Fail] If 404 (Endpoint not found), retry is useless. Break immediately.
                if "404" in str(e):
                    logger.warning(f"[{tag}] Step 1: 404 Error detected. KIS API endpoint issue. Skipping retries.")
                    break
            
            if attempt < retries:
                wait_time = 10 * attempt 
                logger.info(f"[{tag}] Retrying API collection in {wait_time}s...")
                await asyncio.sleep(wait_time)
                
        # [수정] 실패 시, None과 Source Tag를 반환
        return None, source_tag 

#    async def _step_api_with_retry(self, retries: int = 3) -> Optional[Set[str]]:
#        """Step 1: Fetch via API with exponential backoff and count validation."""
#        tag = self._get_current_tag()
#        for attempt in range(1, retries + 1):
#            try:
#                logger.info(f"[{tag}] Step 1: Attempting KIS API collection (Attempt {attempt}/{retries})...")
#                symbols = await self.engine.fetch_stock_list(market="ALL")
#                if self._validate_symbols(symbols):
#                    logger.info(f"[{tag}] Step 1 Success: {len(symbols)} symbols fetched via API")
#                    return set(symbols)
#                else:
#                    count = len(symbols) if symbols else 0
#                    logger.warning(f"[{tag}] Step 1 Validation Failed: Insufficient data count ({count} < 2500).")
#            except Exception as e:
#                logger.error(f"[{tag}] Step 1 Attempt {attempt} Failed: {e}")
            
#            if attempt < retries:
#                wait_time = 10 * attempt  # Shorter wait for internal retry (10s, 20s)
#                logger.info(f"[{tag}] Retrying API collection in {wait_time}s...")
#                await asyncio.sleep(wait_time)
#        return None

    # [수정 제안 코드]
    async def _step_master_file(self) -> tuple[Optional[Set[str]], str]:
        """Step 2: Fetch via KIS Master File."""
        tag = self._get_current_tag()
        source_tag = "MASTER_FILE"
        
        if hasattr(self.engine, "_fetch_stock_list_from_file"):
            try:
                logger.info(f"[{tag}] Step 2: Attempting KIS Master File collection...")
                symbols = await self.engine._fetch_stock_list_from_file()
                
                count = len(symbols) if symbols else 0 # (A) 추가
                
                if self._validate_symbols(symbols):
                    logger.info(f"[{tag}] Step 2 Success: {count} symbols from master file (Passed Quality Check).")
                    return set(symbols), source_tag
                else:
                    # [수정] count 정보를 포함하여 WARNING 로깅 강화
                    logger.warning(f"[{tag}] Step 2 Validation Failed: Insufficient data count ({count} < 2500).")
                    
            except Exception as e:
                logger.error(f"[{tag}] Step 2 Failed: {e}")
        
        # [수정] 실패 시, None과 Source Tag를 반환
        return None, source_tag

#    async def _step_master_file(self) -> Optional[Set[str]]:
#        """Step 2: Fetch via KIS Master File."""
#        tag = self._get_current_tag()
#        if hasattr(self.engine, "_fetch_stock_list_from_file"):
#            try:
#                logger.info(f"[{tag}] Step 2: Attempting KIS Master File collection...")
#                symbols = await self.engine._fetch_stock_list_from_file()
#                if self._validate_symbols(symbols):
#                    logger.info(f"[{tag}] Step 2 Success: {len(symbols)} symbols from master file")
#                    return set(symbols)
#            except Exception as e:
#                logger.error(f"[{tag}] Step 2 Failed: {e}")
#        return None

    # [수정 제안 코드]
    async def _step_local_backup(self) -> tuple[Optional[Set[str]], str]:
        """Step 3: Fetch via Local Backup snapshots."""
        tag = self._get_current_tag()
        source_tag = "LOCAL_BACKUP"
        try:
            # Search in both backup and cache directories
            search_paths = [self.backup_dir, self.cache_dir]
            backup_files = []
            for path in search_paths:
                if path.exists():
                    backup_files.extend(list(path.glob("symbols_*.json")))
            
            # Sort by modification time, newest first
            backup_files.sort(key=os.path.getmtime, reverse=True)
            
            if backup_files:
                latest_backup = backup_files[0]
                logger.info(f"[{tag}] Step 3 Found latest backup: {latest_backup.name} in {latest_backup.parent}") # (A) 추가
                
                with open(latest_backup, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    symbols = data.get("symbols", [])
                    
                    count = len(symbols) if symbols else 0 # (A) 추가
                    
                    if self._validate_symbols(symbols):
                        logger.info(f"[{tag}] Step 3 Success: {count} symbols from {latest_backup.name} (Passed Quality Check).")
                        return set(symbols), source_tag
                    else:
                        # [수정] count 정보를 포함하여 WARNING 로깅 강화
                        logger.warning(f"[{tag}] Step 3 Validation Failed: Insufficient data count ({count} < 2500) in {latest_backup.name}.")
                        
            else:
                logger.info(f"[{tag}] Step 3 Skip: No backup files found in {self.backup_dir}.") # (A) 추가
                
        except Exception as e:
            logger.error(f"[{tag}] Step 3 Failed: {e}")
            
        # [수정] 실패 시, None과 Source Tag를 반환
        return None, source_tag

#    async def _step_local_backup(self) -> Optional[Set[str]]:
#        """Step 3: Fetch via Local Backup snapshots."""
#        tag = self._get_current_tag()
#        try:
#            logger.info(f"[{tag}] Step 3: Attempting local backup collection from {self.backup_dir}...")
#            backup_files = sorted(list(self.backup_dir.glob("symbols_*.json")), key=os.path.getmtime, reverse=True)
#            if backup_files:
#                latest_backup = backup_files[0]
#                with open(latest_backup, "r", encoding="utf-8") as f:
#                    data = json.load(f)
#                    symbols = data.get("symbols", [])
#                if self._validate_symbols(symbols):
#                    logger.info(f"[{tag}] Step 3 Success: {len(symbols)} symbols from {latest_backup.name}")
#                    return set(symbols)
#        except Exception as e:
#            logger.error(f"[{tag}] Step 3 Failed: {e}")
#        return None

    # [수정 제안 코드]
    async def _step_emergency_fallback(self) -> tuple[Optional[Set[str]], str]:
        """Step 4: Emergency Fallback - Use the most recent symbol file from the symbols directory."""
        tag = self._get_current_tag()
        source_tag = "EMERGENCY_FALLBACK"
        try:
            logger.warning(f"[{tag}] Step 4: EMERGENCY FALLBACK - Attempting to use latest generated symbols...")
            latest_file = self.get_latest_symbol_file()
            
            if latest_file:
                logger.warning(f"[{tag}] Step 4 Found latest valid file: {latest_file}.")
                with open(latest_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    symbols = data.get("symbols", [])
                    
                    count = len(symbols) if symbols else 0 # (A) 추가
                    
                    if symbols:
                        # [수정] 2500개 미만이어도, Emergency Fallback은 "최후의 수단"이므로 성공으로 간주하고 반환.
                        logger.warning(f"[{tag}] Step 4 Success: {count} symbols loaded from {Path(latest_file).name} (COUNT={count}).")
                        return set(symbols), source_tag
                    else:
                        logger.critical(f"[{tag}] Step 4 Failed: Latest file {Path(latest_file).name} found but contains 0 symbols.")
            else:
                logger.critical(f"[{tag}] Step 4 Failed: No valid symbol file found for fallback.")

        except Exception as e:
            logger.critical(f"[{tag}] Step 4 Emergency Fallback Failed: {e}")
            
        # [수정] 실패 시, None과 Source Tag를 반환
        return None, source_tag

#    async def _step_emergency_fallback(self) -> Optional[Set[str]]:
#        """Step 4: Emergency Fallback - Use the most recent symbol file from the symbols directory."""
#        tag = self._get_current_tag()
#        try:
#            logger.warning(f"[{tag}] Step 4: EMERGENCY FALLBACK - Attempting to use latest generated symbols...")
#            latest_file = self.get_latest_symbol_file()
#            if latest_file:
#                logger.info(f"[{tag}] Found latest valid file: {latest_file}. Using as today's data.")
#                with open(latest_file, "r", encoding="utf-8") as f:
#                    data = json.load(f)
#                    symbols = data.get("symbols", [])
#                if symbols:
#                    return set(symbols)
#        except Exception as e:
#            logger.critical(f"[{tag}] Step 4 Emergency Fallback Failed: {e}")
#        return None

    def _validate_symbols(self, symbols: List[str]) -> bool:
        """
        Validate the collected data.
        [Requirement] Minimum count 2,500 symbols check.
        """
        if not symbols or len(symbols) < 2500:
            return False
            
        return True

    def _load_state(self) -> Dict[str, Any]:
        """Load the last run state."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    logger.debug("Loaded state file: %s", self.state_file)
                    return state
            except json.JSONDecodeError as e:
                logger.warning("State file %s contains invalid JSON: line %d. Proceeding with fresh state.", self.state_file, e.lineno)
            except (IOError, OSError) as e:
                logger.warning("Cannot read state file %s: %s (type=%s). Proceeding with fresh state.", self.state_file, e, type(e).__name__)
            except Exception as e:
                logger.warning("Unexpected error loading state file %s: %s (type=%s). Proceeding with fresh state.", self.state_file, e, type(e).__name__)
        return {}

    def _save_state(self, state: Dict[str, Any]):
        """Save the current run state."""
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state file: {e}")

    def _write_health_report(self, success: bool, filepath: Optional[str], duration: float, error: Optional[str] = None):
        """Write a summary report for external monitoring."""
        report = {
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "duration_sec": round(duration, 2),
            "filepath": filepath,
            "error": error
        }
        if filepath and os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    report["symbol_count"] = data.get("metadata", {}).get("count", 0)
            except json.JSONDecodeError as e:
                logger.debug("Health report: symbol file %s has invalid JSON: line %d", filepath, e.lineno)
            except (IOError, OSError) as e:
                logger.debug("Health report: cannot read symbol file %s: %s", filepath, e)
            except Exception as e:
                logger.debug("Health report: unexpected error reading %s: %s (type=%s)", filepath, e, type(e).__name__)

        try:
            with open(self.health_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write health report: {e}")

    async def _log_diff(self, new_symbols: Set[str]):
        """Compare with current latest symbol file and log detailed changes."""
        tag = self._get_current_tag()
        latest_file = self.get_latest_symbol_file()
        if not latest_file:
            logger.info(f"[{tag}] No previous symbol file found for comparison.")
            return

        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                old_data = json.load(f)
                old_symbols = set(old_data.get("symbols", []))
            
            added = new_symbols - old_symbols
            removed = old_symbols - new_symbols
            count_change = len(new_symbols) - len(old_symbols)
            
            logger.info(f"[{tag}] [DIFF SUMMARY] Total Change Count: {count_change:+d} (Current: {len(new_symbols)}, Prev: {len(old_symbols)})")
            
            if added:
                logger.info(f"[{tag}] [DIFF] New Listings ({len(added)}): {list(added)[:15]}...")
            if removed:
                logger.info(f"[{tag}] [DIFF] Delistings ({len(removed)}): {list(removed)[:15]}...")
            if not added and not removed:
                logger.info(f"[{tag}] [DIFF] No symbol changes detected.")
        except Exception as e:
            logger.warning(f"[{tag}] Failed to calculate diff: {e}")

    def get_latest_symbol_file(self) -> Optional[str]:
        """Find the most recent valid symbol file in symbols directory."""
        files = list(self.symbols_dir.glob(f"*_{self.market_suffix}.json"))
        if not files:
            return None
        
        files.sort(reverse=True)
        
        for filepath in files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    json.load(f)
                return str(filepath)
            except json.JSONDecodeError as e:
                logger.warning("[RECOVERY] Skipping corrupted symbol file %s: JSON parse error at line %d, col %d", filepath, e.lineno, e.colno)
                continue
            except (IOError, OSError) as e:
                logger.warning("[RECOVERY] Skipping unreadable symbol file %s: %s (type=%s)", filepath, e, type(e).__name__)
                continue
            except Exception as e:
                logger.warning("[RECOVERY] Skipping symbol file %s due to unexpected error: %s (type=%s)", filepath, e, type(e).__name__)
                continue
        return None

    def _cleanup_old_files(self):
        """
        Delete symbol files older than 7 days.
        [Requirement] Prioritize filename-based date (YYYYMMDD) parsing.
        """
        tag = self._get_current_tag()
        # [Requirement] Keep files for at least 5 business days. 
        # Using 14 calendar days to safely cover weekends and long public holidays.
        cutoff_date = (datetime.now() - timedelta(days=14)).replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_ts = cutoff_date.timestamp()
        
        # Support both new and legacy patterns
        files = list(self.symbols_dir.glob("*.json"))
        deleted_count = 0
        
        for filepath in files:
            should_delete = False
            
            # 1. Filename-based check (Priority)
            # Pattern: YYYYMMDD_{market}_stocks.json or symbols_YYYYMMDD_TAG.json
            try:
                parts = filepath.stem.split("_")
                date_str = None
                
                # New pattern: 20260204_{market}_stocks
                if len(parts) >= 1 and len(parts[0]) == 8 and parts[0].isdigit():
                    date_str = parts[0]
                # Legacy pattern: symbols_20260204_AM
                elif len(parts) >= 2 and len(parts[1]) == 8 and parts[1].isdigit():
                    date_str = parts[1]
                    
                if date_str:
                    file_date = datetime.strptime(date_str, "%Y%m%d")
                    if file_date < cutoff_date:
                        should_delete = True
                        logger.info(f"[{tag}] Cleanup: File {filepath.name} is older than 7 days based on filename date.")
            except Exception:
                pass # Fallback to mtime

            if not should_delete and not date_str:
                try:
                    mtime = filepath.stat().st_mtime
                    if mtime < cutoff_ts:
                        should_delete = True
                except Exception:
                    pass

            if should_delete:
                try:
                    filepath.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"[{tag}] Failed to cleanup {filepath}: {e}")
        
        if deleted_count > 0:
            logger.info(f"[{tag}] Cleaned up {deleted_count} old symbol files (7-day policy).")

    def should_collect(self, force: bool = False) -> tuple[bool, Optional[str]]:
        """
        Check if collection is necessary.
        Returns (True, None) if collection is needed,
        Returns (False, path) if valid data (T-0 or T-1) already exists.
        
        :param force: If True, always returns (True, None)
        """
        if force:
            return True, None
            
        tag = self._get_current_tag()
        today_str = datetime.now().strftime("%Y%m%d")
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        
        # 1. Check Today's file (T-0)
        today_file = self.symbols_dir / f"{today_str}_{self.market_suffix}.json"
        if today_file.exists() and self._is_file_valid_quality(today_file):
            return False, str(today_file)
                
        # 2. Check Yesterday's file (T-1)
        yesterday_file = self.symbols_dir / f"{yesterday_str}_{self.market_suffix}.json"
        if yesterday_file.exists() and self._is_file_valid_quality(yesterday_file):
            logger.info(f"[{tag}] [CBC] Found valid T-1 data: {yesterday_file.name}")
            return False, str(yesterday_file)
                
        return True, None

    def _is_file_valid_quality(self, filepath: Path) -> bool:
        """Helper to check if a file has sufficient symbol count."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                count = data.get("metadata", {}).get("count", 0)
                if count >= 2500:
                    logger.debug("File %s passed quality check: count=%d", filepath.name, count)
                    return True
                else:
                    logger.debug("File %s failed quality check: count=%d (< 2500)", filepath.name, count)
        except json.JSONDecodeError as e:
            logger.debug("File %s failed quality check: invalid JSON (line %d)", filepath.name, e.lineno)
        except (IOError, OSError) as e:
            logger.debug("File %s failed quality check: cannot read (%s)", filepath.name, type(e).__name__)
        except Exception as e:
            logger.debug("File %s failed quality check: unexpected error %s", filepath.name, type(e).__name__)
        return False
    def _ensure_set(self, symbols: Any) -> Set[str]:
        """Convert various symbol formats (list, list of dicts) to a set of strings."""
        if isinstance(symbols, set):
            return set(str(s) for s in symbols)
        if not symbols:
            return set()
        
        result = set()
        for item in symbols:
            if isinstance(item, dict):
                code = item.get('code') or item.get('symbol')
                if code:
                    result.add(str(code))
            else:
                result.add(str(item))
        return result
