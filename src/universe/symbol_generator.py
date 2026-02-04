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
        from observer.paths import observer_data_dir
        self.base_path = Path(base_dir) if base_dir else observer_data_dir()
        
        self.symbols_dir = self.base_path / "symbols"
        self.universe_dir = self.base_path / "universe"  # Mandatory output directory
        self.backup_dir = self.base_path / "backup"
        
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

    async def execute(self) -> Optional[str]:
        """
        High-level controller for symbol generation.
        Handles CBC (Check-Before-Collect), state check, recovery, and results reporting.
        """
        start_time = time.time()
        tag = self._get_current_tag()
        ymd = datetime.now().strftime("%Y%m%d")
        
        logger.info(f"[{tag}] Starting SymbolGenerator execution...")
        
        # 1. Check-Before-Collect (CBC) Logic
        # [Requirement] Skip API if valid T-0 or T-1 data exists with > 2500 symbols
        should_run, existing_path = self.should_collect()
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
        state = self._load_state()
        if state.get("last_ymd") == ymd and state.get("last_tag") == tag and state.get("status") == "SUCCESS":
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
        tag = self._get_current_tag()
        logger.info(f"[{tag}] Starting daily symbol generation process...")
        
        symbols = await self._collect_symbols_4step()
        
        if not symbols:
            logger.error(f"[{tag}] [CRITICAL] Failed to collect symbols after all steps.")
            raise RuntimeError("Failed to collect symbols.")

        # Determine version (AM/PM)
        now = datetime.now()
        ymd = now.strftime("%Y%m%d")
        filename = f"symbols_{ymd}_{tag}.json"
        filepath = self.symbols_dir / filename
        
        # [Requirement] AM/PM File Management & Diff Update
        # Load existing today's file if it exists to compare/merge
        existing_symbols: Set[str] = set()
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                    existing_symbols = set(old_data.get("symbols", []))
                    logger.info(f"[{tag}] Existing today's file found ({len(existing_symbols)} symbols)")
            except Exception:
                pass

        # Track Diff before saving
        await self._log_diff(symbols)
        
        # If new symbols are fewer than existing, keep existing ones to be safe (unless emergency)
        if len(symbols) < len(existing_symbols) and len(symbols) < 2500:
            logger.warning(f"[{tag}] New symbol count ({len(symbols)}) is less than existing ({len(existing_symbols)}). Merging with existing data for stability.")
            symbols.update(existing_symbols)

        # Save to JSON
        data = {
            "metadata": {
                "date": ymd,
                "version": tag,
                "generated_at": now.isoformat(),
                "count": len(symbols),
                "source_strategy": "4-Step-Strategy"
            },
            "symbols": sorted(list(symbols))
        }
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"[{tag}] Symbols saved to {filepath} ({len(symbols)} items)")
        except Exception as e:
            logger.error(f"[{tag}] Failed to save symbol file: {e}")
            raise
        
        # Cleanup old files
        self._cleanup_old_files()
        
        return str(filepath)

    async def _collect_symbols_4step(self) -> Set[str]:
        """
        4-Step Collection Strategy (API -> Master File -> Local Backup -> Emergency Fallback).
        """
        tag = self._get_current_tag()
        
        # Step 1: KIS API with Retry
        symbols = await self._step_api_with_retry()
        if symbols: return symbols

        # Step 2: KIS Master File
        symbols = await self._step_master_file()
        if symbols: return symbols

        # Step 3: Local Backup (JSON Only)
        symbols = await self._step_local_backup()
        if symbols: return symbols

        # Step 4: Emergency Fallback (The Last Resort)
        symbols = await self._step_emergency_fallback()
        if symbols: return symbols

        return set()

    async def _step_api_with_retry(self, retries: int = 3) -> Optional[Set[str]]:
        """Step 1: Fetch via API with exponential backoff and count validation."""
        tag = self._get_current_tag()
        for attempt in range(1, retries + 1):
            try:
                logger.info(f"[{tag}] Step 1: Attempting KIS API collection (Attempt {attempt}/{retries})...")
                symbols = await self.engine.fetch_stock_list(market="ALL")
                if self._validate_symbols(symbols):
                    logger.info(f"[{tag}] Step 1 Success: {len(symbols)} symbols fetched via API")
                    return set(symbols)
                else:
                    count = len(symbols) if symbols else 0
                    logger.warning(f"[{tag}] Step 1 Validation Failed: Insufficient data count ({count} < 2500).")
            except Exception as e:
                logger.error(f"[{tag}] Step 1 Attempt {attempt} Failed: {e}")
            
            if attempt < retries:
                wait_time = 10 * attempt  # Shorter wait for internal retry (10s, 20s)
                logger.info(f"[{tag}] Retrying API collection in {wait_time}s...")
                await asyncio.sleep(wait_time)
        return None

    async def _step_master_file(self) -> Optional[Set[str]]:
        """Step 2: Fetch via KIS Master File."""
        tag = self._get_current_tag()
        if hasattr(self.engine, "_fetch_stock_list_from_file"):
            try:
                logger.info(f"[{tag}] Step 2: Attempting KIS Master File collection...")
                symbols = await self.engine._fetch_stock_list_from_file()
                if self._validate_symbols(symbols):
                    logger.info(f"[{tag}] Step 2 Success: {len(symbols)} symbols from master file")
                    return set(symbols)
            except Exception as e:
                logger.error(f"[{tag}] Step 2 Failed: {e}")
        return None

    async def _step_local_backup(self) -> Optional[Set[str]]:
        """Step 3: Fetch via Local Backup snapshots."""
        tag = self._get_current_tag()
        try:
            logger.info(f"[{tag}] Step 3: Attempting local backup collection from {self.backup_dir}...")
            backup_files = sorted(list(self.backup_dir.glob("symbols_*.json")), key=os.path.getmtime, reverse=True)
            if backup_files:
                latest_backup = backup_files[0]
                with open(latest_backup, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    symbols = data.get("symbols", [])
                if self._validate_symbols(symbols):
                    logger.info(f"[{tag}] Step 3 Success: {len(symbols)} symbols from {latest_backup.name}")
                    return set(symbols)
        except Exception as e:
            logger.error(f"[{tag}] Step 3 Failed: {e}")
        return None

    async def _step_emergency_fallback(self) -> Optional[Set[str]]:
        """Step 4: Emergency Fallback - Use the most recent symbol file from the symbols directory."""
        tag = self._get_current_tag()
        try:
            logger.warning(f"[{tag}] Step 4: EMERGENCY FALLBACK - Attempting to use latest generated symbols...")
            latest_file = self.get_latest_symbol_file()
            if latest_file:
                logger.info(f"[{tag}] Found latest valid file: {latest_file}. Using as today's data.")
                with open(latest_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    symbols = data.get("symbols", [])
                if symbols:
                    return set(symbols)
        except Exception as e:
            logger.critical(f"[{tag}] Step 4 Emergency Fallback Failed: {e}")
        return None

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
                    return json.load(f)
            except Exception:
                logger.warning("Failed to load state file. Proceeding with fresh state.")
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
            except Exception:
                pass

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
        files = list(self.symbols_dir.glob("symbols_*.json"))
        if not files:
            return None
        
        files.sort(reverse=True)
        
        for filepath in files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    json.load(f)
                return str(filepath)
            except Exception:
                logger.warning(f"[RECOVERY] Skipping corrupted symbol file: {filepath}")
                continue
        return None

    def _cleanup_old_files(self):
        """
        Delete symbol files older than 7 days.
        [Requirement] Prioritize filename-based date (YYYYMMDD) parsing.
        Use modification time (mtime) only as a fallback.
        """
        tag = self._get_current_tag()
        cutoff_date = (datetime.now() - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_ts = cutoff_date.timestamp()
        
        files = list(self.symbols_dir.glob("symbols_*.json"))
        
        deleted_count = 0
        for filepath in files:
            should_delete = False
            
            # 1. Filename-based check (Priority)
            # Pattern: symbols_YYYYMMDD_TAG.json
            try:
                parts = filepath.stem.split("_")
                if len(parts) >= 2:
                    date_str = parts[1]
                    file_date = datetime.strptime(date_str, "%Y%m%d")
                    if file_date < cutoff_date:
                        should_delete = True
                        logger.info(f"[{tag}] Cleanup: File {filepath.name} is older than 7 days based on filename date.")
            except (IndexError, ValueError):
                # Filename doesn't match expected pattern (symbols_YYYYMMDD_*.json)
                # Fallback to mtime
                try:
                    if filepath.stat().st_mtime < cutoff_ts:
                        should_delete = True
                        logger.info(f"[{tag}] Cleanup: File {filepath.name} is older than 7 days based on mtime fallback.")
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

    def should_collect(self) -> tuple[bool, Optional[str]]:
        """
        Check if collection is necessary.
        Returns (True, None) if collection is needed,
        Returns (False, path) if valid data (T-0 or T-1) already exists.
        """
        tag = self._get_current_tag()
        today_str = datetime.now().strftime("%Y%m%d")
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        
        # 1. Check Today's file (T-0)
        # Search for any tag (AM/PM) to see if we have valid data for today
        today_files = list(self.symbols_dir.glob(f"symbols_{today_str}_*.json"))
        for f in sorted(today_files, reverse=True):
            if self._is_file_valid_quality(f):
                return False, str(f)
                
        # 2. Check Yesterday's file (T-1)
        # In a deployment scenario, T-1 might be sufficient to start
        yesterday_files = list(self.symbols_dir.glob(f"symbols_{yesterday_str}_*.json"))
        for f in sorted(yesterday_files, reverse=True):
            if self._is_file_valid_quality(f):
                logger.info(f"[{tag}] [CBC] Found valid T-1 data: {f.name}")
                return False, str(f)
                
        return True, None

    def _is_file_valid_quality(self, filepath: Path) -> bool:
        """Helper to check if a file has sufficient symbol count."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                count = data.get("metadata", {}).get("count", 0)
                if count >= 2500:
                    return True
        except Exception:
            pass
        return False
