#!/usr/bin/env python3
"""
Track A & B Local Test Runner

로컬 환경에서 Track A와 Track B를 통합 테스트합니다.
도커 없이 순수 로컬 환경에서 실행됩니다.

실행:
    python run_local_test.py
"""

import sys
import logging
import asyncio
from datetime import datetime, timezone, timedelta, date
from pathlib import Path
from typing import List, Dict, Any
import json

# Add src to path
src_path = Path(__file__).parent / "app" / "observer" / "src"
sys.path.insert(0, str(src_path))

from trigger.trigger_engine import TriggerEngine, TriggerConfig, PriceSnapshot
from slot.slot_manager import SlotManager, SlotCandidate

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("LocalTestRunner")


def generate_track_a_data(symbols: List[str], duration_minutes: int = 10) -> List[PriceSnapshot]:
    """
    실제와 유사한 Track A 데이터를 생성하고 swing 폴더에 저장합니다.
    """
    log.info(f"📝 Generating Track A data for {len(symbols)} symbols over {duration_minutes} minutes")
    
    snapshots = []
    now = datetime.now(timezone.utc)
    base_time = now - timedelta(minutes=duration_minutes)
    
    # Base prices for symbols
    base_prices = {
        "005930": 70000,  # Samsung Electronics
        "000660": 95000,  # SK Hynix
        "051910": 156000, # LG Chem
        "012330": 64000,  # Move
        "028260": 41000,  # Three-S
    }
    
    # Create swing directory
    swing_dir = Path("app/observer/config/observer/swing")
    swing_dir.mkdir(parents=True, exist_ok=True)
    
    # Use today's date for filename
    today = date.today().strftime("%Y%m%d")
    swing_log_file = swing_dir / f"{today}.jsonl"
    
    track_a_records = []
    
    for i in range(duration_minutes * 2):  # 30초 간격
        timestamp = base_time + timedelta(seconds=i * 30)
        
        for symbol in symbols:
            base_price = base_prices.get(symbol, 50000)
            
            # Normal price variation
            price_variance = (hash(f"{symbol}_{i}") % 200 - 100) * 10
            price = base_price + price_variance
            
            # Normal volume with occasional spikes
            base_volume = 100000 + (i % 10) * 10000
            
            # Random trigger events (10% chance)
            if hash(f"{symbol}_{i}") % 10 == 0:
                # Volume surge trigger
                volume = base_volume * 20  # 20x surge
                price = base_price * 1.02  # 2% price increase
                log.info(f"🎯 VOLUME SURGE: {symbol} at {timestamp.strftime('%H:%M:%S')}")
            elif hash(f"{symbol}_{i}") % 15 == 0:
                # Volatility spike trigger
                volume = base_volume * 3
                price = base_price * 1.05  # 5% price jump
                log.info(f"🎯 VOLATILITY SPIKE: {symbol} at {timestamp.strftime('%H:%M:%S')}")
            else:
                volume = base_volume
            
            # Open/High/Low
            open_price = base_price
            high_price = max(price, base_price) + (hash(symbol + str(i)) % 1000)
            low_price = min(price, base_price) - (hash(symbol + str(i+1)) % 1000)
            
            snapshot = PriceSnapshot(
                symbol=symbol,
                timestamp=timestamp,
                price=float(price),
                volume=int(volume),
                open=float(open_price),
                high=float(high_price),
                low=float(low_price),
            )
            snapshots.append(snapshot)
            
            # Create Track A record in actual format
            track_a_record = {
                "ts": timestamp.isoformat(),
                "session": "track_a_session",
                "dataset": "track_a_swing",
                "market": "kr_stocks",
                "symbol": symbol,
                "price": {
                    "open": int(open_price),
                    "high": int(high_price),
                    "low": int(low_price),
                    "close": int(price)
                },
                "volume": int(volume),
                "bid_price": None,
                "ask_price": None,
                "source": "kis"
            }
            track_a_records.append(track_a_record)
    
    # Save Track A data to swing folder
    with open(swing_log_file, "w", encoding="utf-8") as f:
        for record in track_a_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    log.info(f"✅ Generated {len(snapshots)} snapshots")
    log.info(f"✅ Track A data saved to: {swing_log_file}")
    return snapshots


def run_track_b_test(snapshots: List[PriceSnapshot]) -> Dict[str, Any]:
    """
    Track B 테스트를 실행하고 결과를 반환합니다.
    """
    log.info("\n" + "="*60)
    log.info("TRACK B TEST EXECUTION")
    log.info("="*60)
    
    # Initialize Track B components
    config = TriggerConfig(
        volume_surge_ratio=5.0,
        volatility_spike_threshold=0.05,
        min_priority_score=0.5,
        dedup_window_seconds=60,  # 1 minute dedup for testing
    )
    
    trigger_engine = TriggerEngine(config=config)
    slot_manager = SlotManager(max_slots=10, min_dwell_seconds=60)
    
    # Process snapshots
    all_candidates = []
    batch_size = 10  # Process in batches
    
    for i in range(0, len(snapshots), batch_size):
        batch = snapshots[i:i + batch_size]
        candidates = trigger_engine.update(batch)
        
        if candidates:
            log.info(f"📊 Batch {i//batch_size}: {len(candidates)} triggers detected")
            
            for candidate in candidates:
                # Allocate slot
                result = slot_manager.assign_slot(candidate)
                if result.success:
                    log.info(f"   ✅ Slot {result.slot_id}: {candidate.symbol} ({candidate.trigger_type})")
                    all_candidates.append({
                        "symbol": candidate.symbol,
                        "slot_id": result.slot_id,
                        "trigger_type": candidate.trigger_type,
                        "priority": candidate.priority_score,
                        "detected_at": candidate.detected_at.isoformat(),
                        "details": candidate.details,
                    })
                else:
                    log.warning(f"   ⚠️ Overflow: {candidate.symbol}")
    
    # Generate scalp log in correct path
    scalp_dir = Path("app/observer/config/observer/scalp")
    scalp_dir.mkdir(parents=True, exist_ok=True)
    
    # Use today's date for filename
    today = date.today().strftime("%Y%m%d")
    scalp_log_file = scalp_dir / f"{today}.jsonl"
    
    with open(scalp_log_file, "w", encoding="utf-8") as f:
        for candidate in all_candidates:
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "symbol": candidate["symbol"],
                "slot_id": candidate["slot_id"],
                "trigger_type": candidate["trigger_type"],
                "priority_score": candidate["priority"],
                "details": candidate["details"],
                "test_run": datetime.now().isoformat(),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    # Get statistics
    trigger_stats = trigger_engine.get_history("005930", minutes=10)  # Sample history
    slot_stats = slot_manager.get_stats()
    
    results = {
        "total_snapshots": len(snapshots),
        "total_candidates": len(all_candidates),
        "allocated_slots": slot_stats["allocated_slots"],
        "total_overflows": slot_stats["total_overflows"],
        "scalp_log_file": str(scalp_log_file),
        "trigger_engine_config": config.__dict__,
        "slot_manager_stats": slot_stats,
    }
    
    log.info(f"\n📊 TRACK B TEST RESULTS:")
    log.info(f"   Total Snapshots: {results['total_snapshots']}")
    log.info(f"   Triggers Detected: {results['total_candidates']}")
    log.info(f"   Slots Allocated: {results['allocated_slots']}")
    log.info(f"   Total Overflows: {results['total_overflows']}")
    log.info(f"   Scalp Log: {results['scalp_log_file']}")
    
    return results


def save_test_summary(results: Dict[str, Any], output_dir: Path):
    """
    테스트 결과 요약을 저장합니다.
    """
    summary_file = output_dir / "test_summary.json"
    
    summary = {
        "test_timestamp": datetime.now(timezone.utc).isoformat(),
        "test_type": "track_a_b_local_integration",
        "environment": "local",
        "results": results,
        "status": "SUCCESS" if results["total_candidates"] > 0 else "NO_TRIGGERS",
    }
    
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    log.info(f"✅ Test summary saved to: {summary_file}")


def load_symbols_from_file(symbol_file: Path) -> List[str]:
    """
    심볼 파일에서 종목 코드를 로드합니다.
    """
    try:
        with open(symbol_file, "r", encoding="utf-8") as f:
            symbols = [line.strip() for line in f if line.strip()]
        log.info(f"✅ Loaded {len(symbols)} symbols from {symbol_file}")
        return symbols[:50]  # 테스트를 위해 상위 50개 종목만 사용
    except Exception as e:
        log.error(f"❌ Failed to load symbols from {symbol_file}: {e}")
        return ["005930", "000660", "051910", "012330", "028260"]  # fallback


def main():
    """
    메인 테스트 실행 함수
    """
    print("\n" + "="*70)
    print("🧪 TRACK A & B LOCAL INTEGRATION TEST")
    print("="*70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Environment: Local (No Docker)")
    print("="*70 + "\n")
    
    try:
        # Load symbols from actual file
        symbol_file = Path("app/observer/config/symbols/kr_all_symbols.txt")
        symbols = load_symbols_from_file(symbol_file)
        
        log.info(f"📊 Testing with {len(symbols)} symbols")
        
        # Generate Track A data
        snapshots = generate_track_a_data(symbols, duration_minutes=10)
        
        # Run Track B test
        results = run_track_b_test(snapshots)
        
        # Final summary
        print("\n" + "="*70)
        print("📊 FINAL TEST SUMMARY")
        print("="*70)
        print(f"Status: {'✅ SUCCESS' if results['total_candidates'] > 0 else '⚠️ NO TRIGGERS'}")
        print(f"Track A Swing Log: app/observer/config/observer/swing/{date.today().strftime('%Y%m%d')}.jsonl")
        print(f"Track B Scalp Log: {results['scalp_log_file']}")
        print("="*70 + "\n")
        
        return 0 if results["total_candidates"] > 0 else 1
        
    except Exception as e:
        log.error(f"❌ Test failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
