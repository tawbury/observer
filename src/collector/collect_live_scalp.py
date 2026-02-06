#!/usr/bin/env python3
"""
Minimal live KIS WebSocket tick collector (Track B helper)

- Connects via ProviderEngine (real or virtual based on .env)
- Subscribes to a few symbols (default: 005930, 000660, 373220)
- Logs ticks to data/assets/scalp/YYYYMMDD.jsonl (same path as Track B)

Run:
  python -m collector.collect_live_scalp --symbols 005930,000660,373220 --seconds 120
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from zoneinfo import ZoneInfo

# Workspace imports
import sys

_src_root = Path(__file__).resolve().parents[1]
if str(_src_root) not in sys.path:
    sys.path.insert(0, str(_src_root))

from provider import ProviderEngine, KISAuth
from observer.paths import observer_asset_dir, env_file_path

log = logging.getLogger("LiveScalpCollector")


def _scalp_log_path() -> Path:
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    log_dir = observer_asset_dir() / "scalp"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{now.strftime('%Y%m%d')}.jsonl"


def _make_record(data: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    return {
        "timestamp": now.isoformat(),
        "symbol": data.get("symbol"),
        "execution_time": data.get("execution_time"),
        "price": {
            "current": data.get("price", {}).get("close"),
            "open": data.get("price", {}).get("open"),
            "high": data.get("price", {}).get("high"),
            "low": data.get("price", {}).get("low"),
            "change_rate": data.get("price", {}).get("change_rate"),
        },
        "volume": data.get("volume", {}),
        "bid_ask": data.get("bid_ask", {}),
        "source": "websocket",
        "session_id": "live_scalp_test",
    }


async def collect(symbols: List[str], seconds: int, is_virtual_env: bool | None = None) -> int:
    log.info("Starting live scalp collection: symbols=%s, duration=%ds, virtual=%s", symbols, seconds, is_virtual_env)

    # Load .env
    env_path = env_file_path()
    if env_path.exists():
        try:
            from dotenv import load_dotenv  # type: ignore

            load_dotenv(env_path)
            log.debug("Loaded .env from %s", env_path)
        except ImportError as e:
            log.warning("dotenv not installed, skipping .env load: %s", e)
        except Exception as e:
            log.warning("Failed to load .env from %s: %s (type=%s)", env_path, e, type(e).__name__)

    # Engine
    auth = KISAuth(is_virtual=is_virtual_env)
    engine = ProviderEngine(auth=auth, is_virtual=is_virtual_env)

    # Output
    out_path = _scalp_log_path()
    try:
        f = out_path.open("a", encoding="utf-8")
        log.info("Opened scalp log file for writing: %s", out_path)
    except (IOError, PermissionError, OSError) as e:
        log.error("FATAL: Cannot open scalp log file %s: %s (type=%s)", out_path, e, type(e).__name__)
        return 1

    # Callback
    tick_count = [0]  # mutable counter

    def on_price_update(data: Dict[str, Any]) -> None:
        try:
            if not data or not isinstance(data, dict):
                log.warning("Invalid WebSocket data received (not a dict): %s", repr(data)[:200])
                return
            if "symbol" not in data:
                log.warning("WebSocket data missing 'symbol' field: keys=%s, sample=%s", list(data.keys()), repr(data)[:200])
                return

            rec = _make_record(data)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()  # Force flush
            tick_count[0] += 1
            if tick_count[0] % 10 == 1:
                log.info("Received %d ticks so far...", tick_count[0])
        except (IOError, OSError) as e:
            log.error("Failed to write tick to file %s: %s", out_path, e)
        except Exception as e:
            log.error("Unexpected error in price update callback: %s (type=%s)", e, type(e).__name__, exc_info=True)

    engine.on_price_update = on_price_update

    try:
        # Start stream
        ok = await engine.start_stream()
        if not ok:
            log.error("Failed to start websocket stream")
            return 1

        # Subscribe
        for s in symbols:
            try:
                await engine.subscribe(s)
                log.info(f"Subscribed {s}")
            except Exception as e:
                log.warning(f"Subscribe failed for {s}: {e}")

        # Run
        log.info("Collecting data for %d seconds...", seconds)
        await asyncio.sleep(seconds)
        log.info("Collection complete. Total ticks received: %d, file: %s", tick_count[0], out_path)
        return 0

    finally:
        try:
            await engine.stop_stream()
        finally:
            await engine.close()
            f.flush()
            f.close()


def main() -> int:
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", default="005930,000660,373220", help="Comma-separated symbols")
    p.add_argument("--seconds", type=int, default=120)
    p.add_argument("--virtual", action="store_true", help="Use virtual KIS env")
    args = p.parse_args()

    # Normalize to 6-digit codes expected by KIS (left-pad zeros)
    symbols = [s.strip().zfill(6) for s in args.symbols.split(",") if s.strip()]
    return asyncio.run(collect(symbols, args.seconds, is_virtual_env=args.virtual))


if __name__ == "__main__":
    raise SystemExit(main())
