from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import deque
from pathlib import Path
import json

log = logging.getLogger("TriggerEngine")


@dataclass
class TriggerConfig:
    """Trigger detection configuration."""
    # Volume Surge Trigger
    volume_surge_ratio: float = 5.0  # 1min volume > 10min avg * ratio
    volume_surge_priority: float = 0.9
    
    # Volatility Spike Trigger
    volatility_spike_threshold: float = 0.05  # 5% price change in 1min
    volatility_spike_priority: float = 0.95
    
    # Trade Velocity Trigger (not implemented yet - requires tick data)
    trade_velocity_threshold: int = 10  # trades/sec
    trade_velocity_priority: float = 0.7
    
    # Candidate management
    max_candidates: int = 100
    min_priority_score: float = 0.5
    dedup_window_seconds: int = 300  # 5 minutes


@dataclass
class PriceSnapshot:
    """Price snapshot for a symbol at a specific time."""
    symbol: str
    timestamp: datetime
    price: float
    volume: int
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None


@dataclass
class TriggerCandidate:
    """Candidate symbol selected by trigger."""
    symbol: str
    trigger_type: str  # "volume_surge", "volatility_spike", "trade_velocity"
    priority_score: float
    detected_at: datetime
    details: Dict[str, any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "trigger_type": self.trigger_type,
            "priority_score": self.priority_score,
            "detected_at": self.detected_at.isoformat(),
            "details": self.details,
        }


class TriggerEngine:
    """
    Trigger-based symbol selection engine for Track B.
    
    Analyzes Track A snapshots to detect:
    - Volume surges (1min volume >> 10min avg)
    - Volatility spikes (rapid price changes)
    - Trade velocity increases (future: tick-level)
    
    Generates prioritized candidate queue for SlotManager.
    """
    
    def __init__(self, config: Optional[TriggerConfig] = None) -> None:
        self.cfg = config or TriggerConfig()
        
        # Historical data buffer (symbol -> deque of snapshots)
        self._history: Dict[str, deque[PriceSnapshot]] = {}
        self._history_window = timedelta(minutes=15)  # keep 15min of data
        
        # Recent trigger dedup (symbol -> last trigger time)
        self._recent_triggers: Dict[str, datetime] = {}
        
        log.info("TriggerEngine initialized with config: %s", self.cfg)
    
    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def update(self, snapshots: List[PriceSnapshot]) -> List[TriggerCandidate]:
        """
        Update engine with new snapshots and detect triggers.
        
        Args:
            snapshots: List of price snapshots from Track A
            
        Returns:
            List of triggered candidates sorted by priority (highest first)
        """
        # Use aware datetime consistently
        from datetime import timezone
        now = datetime.now(timezone.utc)
        candidates: List[TriggerCandidate] = []
        
        # Update history
        for snap in snapshots:
            self._add_to_history(snap)
        
        # Detect triggers for each symbol
        for snap in snapshots:
            # Skip if recently triggered (dedup)
            if self._is_recently_triggered(snap.symbol, now):
                continue
            
            # Check Volume Surge
            vol_candidate = self._check_volume_surge(snap, now)
            if vol_candidate:
                candidates.append(vol_candidate)
                self._mark_triggered(snap.symbol, now)
                continue
            
            # Check Volatility Spike
            vol_spike_candidate = self._check_volatility_spike(snap, now)
            if vol_spike_candidate:
                candidates.append(vol_spike_candidate)
                self._mark_triggered(snap.symbol, now)
                continue
        
        # Sort by priority (highest first) and limit
        candidates.sort(key=lambda c: c.priority_score, reverse=True)
        return candidates[:self.cfg.max_candidates]
    
    def get_history(self, symbol: str, minutes: int = 10) -> List[PriceSnapshot]:
        """Get recent history for a symbol."""
        if symbol not in self._history:
            return []
        
        from datetime import timezone
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        return [s for s in self._history[symbol] if s.timestamp >= cutoff]
    
    # ---------------------------------------------------------
    # Trigger Detection
    # ---------------------------------------------------------
    def _check_volume_surge(
        self, snap: PriceSnapshot, now: datetime
    ) -> Optional[TriggerCandidate]:
        """
        Detect volume surge: 1min volume > 10min avg * ratio.
        """
        history = self.get_history(snap.symbol, minutes=10)
        if len(history) < 2:
            return None  # insufficient data
        
        # Calculate 10-min average volume
        total_volume = sum(h.volume for h in history)
        avg_volume = total_volume / len(history)
        
        if avg_volume == 0:
            return None
        
        # Check if current volume is surge
        surge_ratio = snap.volume / avg_volume
        
        # Debug logging
        log.debug(f"Volume surge check for {snap.symbol}: "
                 f"current={snap.volume}, avg={avg_volume:.0f}, "
                 f"ratio={surge_ratio:.2f}, threshold={self.cfg.volume_surge_ratio}")
        
        if surge_ratio >= self.cfg.volume_surge_ratio:
            log.info(f"🎯 VOLUME SURGE DETECTED: {snap.symbol} "
                    f"ratio={surge_ratio:.2f} >= {self.cfg.volume_surge_ratio}")
            return TriggerCandidate(
                symbol=snap.symbol,
                trigger_type="volume_surge",
                priority_score=self.cfg.volume_surge_priority,
                detected_at=now,
                details={
                    "current_volume": snap.volume,
                    "avg_volume_10m": int(avg_volume),
                    "surge_ratio": round(surge_ratio, 2),
                },
            )
        
        return None
    
    def _check_volatility_spike(
        self, snap: PriceSnapshot, now: datetime
    ) -> Optional[TriggerCandidate]:
        """
        Detect volatility spike: 1min price change > threshold.
        """
        history = self.get_history(snap.symbol, minutes=1)
        if len(history) < 2:
            return None
        
        # Get earliest price in 1min window
        earliest = history[0]
        price_change = abs(snap.price - earliest.price) / earliest.price
        
        if price_change >= self.cfg.volatility_spike_threshold:
            return TriggerCandidate(
                symbol=snap.symbol,
                trigger_type="volatility_spike",
                priority_score=self.cfg.volatility_spike_priority,
                detected_at=now,
                details={
                    "current_price": snap.price,
                    "previous_price": earliest.price,
                    "price_change_pct": round(price_change * 100, 2),
                },
            )
        
        return None
    
    # ---------------------------------------------------------
    # History Management
    # ---------------------------------------------------------
    def _add_to_history(self, snap: PriceSnapshot) -> None:
        """Add snapshot to history buffer."""
        if snap.symbol not in self._history:
            self._history[snap.symbol] = deque(maxlen=100)  # keep last 100 snapshots
        
        self._history[snap.symbol].append(snap)
        
        # Clean old history
        from datetime import timezone
        cutoff = datetime.now(timezone.utc) - self._history_window
        while (
            self._history[snap.symbol]
            and self._history[snap.symbol][0].timestamp < cutoff
        ):
            self._history[snap.symbol].popleft()
    
    def _is_recently_triggered(self, symbol: str, now: datetime) -> bool:
        """Check if symbol was recently triggered (dedup)."""
        if symbol not in self._recent_triggers:
            return False
        
        last_trigger = self._recent_triggers[symbol]
        elapsed = (now - last_trigger).total_seconds()
        return elapsed < self.cfg.dedup_window_seconds
    
    def _mark_triggered(self, symbol: str, now: datetime) -> None:
        """Mark symbol as triggered."""
        self._recent_triggers[symbol] = now
        
        # Clean old triggers
        cutoff = now - timedelta(seconds=self.cfg.dedup_window_seconds * 2)
        to_remove = [
            sym for sym, ts in self._recent_triggers.items() if ts < cutoff
        ]
        for sym in to_remove:
            del self._recent_triggers[sym]
    
    # ---------------------------------------------------------
    # Config Management
    # ---------------------------------------------------------
    @staticmethod
    def load_config(path: Path) -> TriggerConfig:
        """Load trigger config from YAML file."""
        try:
            import yaml
            with open(path, "r") as f:
                data = yaml.safe_load(f)
                return TriggerConfig(**data)
        except Exception as e:
            log.warning("Failed to load config from %s: %s", path, e)
            return TriggerConfig()
    
    @staticmethod
    def save_config(config: TriggerConfig, path: Path) -> None:
        """Save trigger config to YAML file."""
        try:
            import yaml
            with open(path, "w") as f:
                yaml.dump(config.__dict__, f)
            log.info("Saved trigger config to %s", path)
        except Exception as e:
            log.error("Failed to save config to %s: %s", path, e)


# ---------------- Utility: Parse Track A JSONL ----------------
def parse_track_a_jsonl(log_path: Path) -> List[PriceSnapshot]:
    """Parse Track A JSONL log file into PriceSnapshots."""
    snapshots: List[PriceSnapshot] = []
    
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                record = json.loads(line.strip())
                snap = PriceSnapshot(
                    symbol=record["symbol"],
                    timestamp=datetime.fromisoformat(record["ts"].replace("Z", "+00:00")),
                    price=record["price"]["close"] or 0,
                    volume=record.get("volume", 0),
                    open=record["price"].get("open"),
                    high=record["price"].get("high"),
                    low=record["price"].get("low"),
                )
                snapshots.append(snap)
    except Exception as e:
        log.error("Failed to parse Track A log %s: %s", log_path, e)
    
    return snapshots


# ---------------- CLI for testing ----------------
def main():
    import argparse
    from pathlib import Path
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    
    parser = argparse.ArgumentParser(description="Trigger Engine Test")
    parser.add_argument(
        "--log", required=True, help="Path to Track A JSONL log file"
    )
    args = parser.parse_args()
    
    log_path = Path(args.log)
    if not log_path.exists():
        print(f"Error: Log file not found: {log_path}")
        return
    
    # Parse Track A data
    snapshots = parse_track_a_jsonl(log_path)
    print(f"Loaded {len(snapshots)} snapshots from {log_path}")
    
    # Run trigger engine
    engine = TriggerEngine()
    candidates = engine.update(snapshots)
    
    print(f"\n🎯 Detected {len(candidates)} trigger candidates:\n")
    for i, cand in enumerate(candidates[:10], 1):
        print(f"{i}. {cand.symbol} | {cand.trigger_type} | priority={cand.priority_score:.2f}")
        print(f"   Details: {cand.details}\n")


if __name__ == "__main__":
    main()
