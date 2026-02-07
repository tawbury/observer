
import asyncio
import time
import logging
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# Add src to path
# Assuming this script is at d:\development\prj_obs\tests\manual\test_rate_limiter_pacing.py
# We need to add d:\development\prj_obs\src to system path
current_dir = Path(__file__).resolve().parent
src_path = current_dir.parent.parent / "src"
print(f"Adding src path: {src_path}")
sys.path.insert(0, str(src_path))

from provider.kis.kis_rest_provider import RateLimiter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("TestRateLimiter")

async def test_pacing():
    RPS = 15
    RPM = 900
    EXPECTED_GAP = 1.0 / RPS
    
    logger.info(f"Starting RateLimiter Test (RPS={RPS}, Minimum Gap ~ {EXPECTED_GAP:.4f}s)")
    
    limiter = RateLimiter(requests_per_second=RPS, requests_per_minute=RPM)
    
    timestamps = []
    
    # Warmup
    await limiter.acquire()
    first_time = time.monotonic()
    timestamps.append(first_time)
    
    test_count = 30
    logger.info(f"Acquiring {test_count} more tokens...")
    
    for i in range(test_count):
        await limiter.acquire()
        now = time.monotonic()
        timestamps.append(now)
        # print(f"Token {i+1} acquired")
        
    total_duration = timestamps[-1] - timestamps[0]
    logger.info(f"Total duration for {test_count} *additional* requests: {total_duration:.4f}s")
    
    # Analyze gaps
    gaps = []
    violations = 0
    min_allowance_s = 0.002 # 2ms allowance for loop overhead measurement error
    
    for i in range(1, len(timestamps)):
        gap = timestamps[i] - timestamps[i-1]
        gaps.append(gap)
        
        # Check if gap is suspiciously small
        if gap < (EXPECTED_GAP - min_allowance_s):
            logger.error(f"Gap violation at index {i}: {gap:.6f}s < {EXPECTED_GAP:.6f}s (Threshold)")
            violations += 1
            
    if gaps:
        avg_gap = sum(gaps) / len(gaps)
        min_detected = min(gaps)
        max_detected = max(gaps)
        logger.info(f"Stats (N={len(gaps)}): Min={min_detected:.6f}s, Max={max_detected:.6f}s, Avg={avg_gap:.6f}s")
    
    if violations > 0:
        logger.error(f"❌ FAILED: {violations} pacing violations detected.")
        sys.exit(1)
    
    # Check total duration
    # If we made N requests AFTER the first one, the total time should be at least N * gap
    # Example: 15 RPS -> 0.066s gap. 30 requests -> ~2.0s
    expected_min_duration = test_count * EXPECTED_GAP * 0.95 # 5% margin
    
    if total_duration < expected_min_duration:
        logger.error(f"❌ FAILED: Total duration {total_duration:.4f}s is too fast (expected >= {expected_min_duration:.4f}s)")
        sys.exit(1)
        
    logger.info("✅ SUCCESS: Strict pacing verification passed.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_pacing())
