import os
import json
import logging
import asyncio
import sys
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
        # Use OBSERVER_DATA_DIR environment variable as root
        env_root = os.getenv("OBSERVER_DATA_DIR", "/opt/platform/runtime/observer/data")
        self.base_path = Path(base_dir) if base_dir else Path(env_root)
        self.symbols_dir = self.base_path / "symbols"
        self.backup_dir = self.base_path / "backup"
        
        # Hard-fail on directory creation issues to prevent operating in an unstable environment
        try:
            self.symbols_dir.mkdir(parents=True, exist_ok=True)
            self.backup_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            logger.critical(f"[FATAL] Permission denied during directory creation: {e}")
            sys.exit(1)
        except Exception as e:
            logger.critical(f"[FATAL] Failed to initialize directories: {e}")
            sys.exit(1)
        
        logger.info(f"[INIT] SymbolGenerator initialized at {self.symbols_dir}")

    def _get_current_tag(self) -> str:
        """Helper to get AM/PM tag for logging."""
        return "AM" if datetime.now().hour < 12 else "PM"

    async def generate_daily_symbols(self) -> str:
        """
        Execute the 3-step collection strategy and save the result.
        Returns the path to the generated symbol file.
        """
        tag = self._get_current_tag()
        logger.info(f"[{tag}] Starting daily symbol generation process...")
        
        symbols = await self._collect_symbols_3step()
        
        if not symbols:
            logger.error(f"[{tag}] [CRITICAL] Failed to collect symbols after all 3 steps.")
            raise RuntimeError("Failed to collect symbols.")

        # Determine version (AM/PM)
        now = datetime.now()
        ymd = now.strftime("%Y%m%d")
        filename = f"symbols_{ymd}_{tag}.json"
        filepath = self.symbols_dir / filename
        
        # Track Diff before saving
        await self._log_diff(symbols)
        
        # Save to JSON
        data = {
            "metadata": {
                "date": ymd,
                "version": tag,
                "generated_at": now.isoformat(),
                "count": len(symbols),
                "source_strategy": "3-Step-Success"
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

    async def _collect_symbols_3step(self) -> Set[str]:
        """
        3-Step Collection Strategy.
        """
        tag = self._get_current_tag()
        # Step 1: KIS API
        try:
            logger.info(f"[{tag}] Step 1: Attempting KIS API collection...")
            symbols = await self.engine.fetch_stock_list(market="ALL")
            if symbols and len(symbols) > 500:
                logger.info(f"[{tag}] Step 1 Success: {len(symbols)} symbols fetched via API")
                return set(symbols)
        except Exception as e:
            logger.warning(f"[{tag}] Step 1 Failed (API): {e}")

        # Step 2: KIS Master File
        logger.info(f"[{tag}] Step 2: Attempting KIS Master File download...")
        if hasattr(self.engine, "_fetch_stock_list_from_file"):
            try:
                symbols = await self.engine._fetch_stock_list_from_file()
                if symbols:
                    logger.info(f"[{tag}] Step 2 Success: {len(symbols)} symbols from master file")
                    return set(symbols)
            except Exception as e:
                logger.warning(f"[{tag}] Step 2 Failed (Master File): {e}")
        else:
            logger.info(f"[{tag}] Step 2 Skipped: Engine method '_fetch_stock_list_from_file' not implemented.")

        # Step 3: Local Backup
        try:
            logger.info(f"[{tag}] Step 3: Attempting local backup data...")
            backup_files = list(self.backup_dir.glob("*.txt")) + list(self.backup_dir.glob("*.csv"))
            if backup_files:
                backup_files.sort(key=os.path.getmtime, reverse=True)
                latest_backup = backup_files[0]
                logger.info(f"[{tag}] Loading from local backup: {latest_backup}")
                
                with open(latest_backup, "r", encoding="utf-8") as f:
                    symbols = [line.strip() for line in f if line.strip()]
                
                if symbols:
                    logger.info(f"[{tag}] Step 3 Success: {len(symbols)} symbols from backup")
                    return set(symbols)
            else:
                logger.warning(f"[{tag}] Step 3 Failed: No backup files found in {self.backup_dir}")
        except Exception as e:
            logger.error(f"[{tag}] Step 3 Failed (Local Backup): {e}")

        return set()

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
        Uses both filename date and file modification time (mtime) for robustness.
        """
        tag = self._get_current_tag()
        cutoff_date = datetime.now() - timedelta(days=7)
        cutoff_ts = cutoff_date.timestamp()
        
        files = list(self.symbols_dir.glob("symbols_*.json"))
        
        deleted_count = 0
        for filepath in files:
            should_delete = False
            
            # 1. Filename-based check
            try:
                date_str = filepath.stem.split("_")[1]
                file_date = datetime.strptime(date_str, "%Y%m%d")
                if file_date < cutoff_date:
                    should_delete = True
            except (IndexError, ValueError):
                # Filename doesn't match pattern, rely on mtime
                pass
            
            # 2. mtime-based secondary check
            try:
                if not should_delete and filepath.stat().st_mtime < cutoff_ts:
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
