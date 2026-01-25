"""
Mock WebSocket Provider for Track B Testing

실제 KIS WebSocket 대신 모의 Tick 데이터를 생성하여
Track B 파이프라인 전체를 테스트합니다.

사용:
  python test/test_track_b_websocket_mock.py --duration=60 --symbols=005930,000660
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional, Dict, Any, Set
from dataclasses import dataclass
import argparse
from pathlib import Path

log = logging.getLogger("MockWebSocketProvider")


@dataclass
class MockTickData:
    """Mock real-time tick data."""
    symbol: str
    price: int
    volume: int
    bid_price: int
    ask_price: int
    execution_time: str  # HHMMSS
    trade_count: int
    change_rate: float


class MockKISWebSocketProvider:
    """
    Mock KIS WebSocket Provider
    
    실제 WebSocket 대신 정해진 간격으로 모의 Tick 데이터를 생성합니다.
    - 2Hz 데이터 생성 (0.5초 간격)
    - 심볼별 구독/구독해제 관리
    - 콜백 메커니즘 제공
    """
    
    def __init__(self, symbols: Set[str] = None, tick_frequency: float = 0.5):
        """
        Initialize mock provider.
        
        Args:
            symbols: Initial symbols to generate ticks for
            tick_frequency: Time between ticks in seconds (0.5 = 2Hz)
        """
        self.subscribed_symbols: Set[str] = symbols or set()
        self.tick_frequency = tick_frequency
        self.is_connected = False
        
        # Callbacks
        self.on_price_update: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_connection: Optional[Callable[[], None]] = None
        self.on_disconnection: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        
        # Background task
        self._tick_task: Optional[asyncio.Task] = None
        self._tick_count = 0
        
        log.info(f"MockKISWebSocketProvider initialized (freq={tick_frequency}Hz)")
    
    async def connect(self) -> bool:
        """Connect (mock)."""
        log.info("📡 Mock WebSocket: Connecting...")
        await asyncio.sleep(0.1)  # Simulate connection delay
        self.is_connected = True
        log.info("✅ Mock WebSocket: Connected")
        
        if self.on_connection:
            self.on_connection()
        
        # Start tick generation task
        self._tick_task = asyncio.create_task(self._generate_ticks())
        
        return True
    
    async def disconnect(self) -> None:
        """Disconnect (mock)."""
        log.info("📡 Mock WebSocket: Disconnecting...")
        self.is_connected = False
        
        if self._tick_task and not self._tick_task.done():
            self._tick_task.cancel()
            try:
                await self._tick_task
            except asyncio.CancelledError:
                pass
        
        log.info("✅ Mock WebSocket: Disconnected")
        
        if self.on_disconnection:
            self.on_disconnection()
    
    async def subscribe(self, symbol: str) -> bool:
        """Subscribe to symbol."""
        if symbol in self.subscribed_symbols:
            log.debug(f"Already subscribed to {symbol}")
            return True
        
        self.subscribed_symbols.add(symbol)
        log.info(f"✅ Mock WebSocket: Subscribed to {symbol} (total: {len(self.subscribed_symbols)})")
        return True
    
    async def unsubscribe(self, symbol: str) -> bool:
        """Unsubscribe from symbol."""
        if symbol not in self.subscribed_symbols:
            log.debug(f"Not subscribed to {symbol}")
            return True
        
        self.subscribed_symbols.discard(symbol)
        log.info(f"✅ Mock WebSocket: Unsubscribed from {symbol} (total: {len(self.subscribed_symbols)})")
        return True
    
    async def _generate_ticks(self) -> None:
        """Background task: generate mock ticks."""
        base_prices = {
            "005930": 70000,    # Samsung
            "000660": 95000,    # SK Hynix
            "051910": 156000,   # LG Chem
            "012330": 64000,    # Hyundai Motor
            "028260": 41000,    # Samsung SDI
            "068270": 283500,   # Celltrion
            "207940": 97000,    # Samsung Bio
            "066970": 74500,    # LG Electronics
        }
        
        try:
            while self.is_connected:
                current_time = datetime.now(timezone.utc)
                time_str = current_time.strftime("%H%M%S")
                
                # Generate tick for each subscribed symbol
                for symbol in list(self.subscribed_symbols):
                    # Generate realistic price movement
                    base_price = base_prices.get(symbol, 50000)
                    
                    # Small random walk
                    variance = (self._tick_count % 5 - 2) * 100  # -200 to +200
                    price = base_price + variance
                    
                    # Bid/Ask spread
                    bid_price = price - 50
                    ask_price = price + 50
                    
                    # Volume per tick
                    volume = 1000 + (self._tick_count % 2000)
                    
                    # Change rate (from base)
                    change_rate = (variance / base_price) * 100
                    
                    tick = MockTickData(
                        symbol=symbol,
                        price=int(price),
                        volume=int(volume),
                        bid_price=int(bid_price),
                        ask_price=int(ask_price),
                        execution_time=time_str,
                        trade_count=self._tick_count % 10 + 1,
                        change_rate=change_rate,
                    )
                    
                    # Convert to standard format and call callback
                    if self.on_price_update:
                        price_data = {
                            "symbol": tick.symbol,
                            "execution_time": tick.execution_time,
                            "timestamp": current_time.isoformat(),
                            "price": {
                                "close": tick.price,
                                "change_rate": tick.change_rate,
                            },
                            "volume": {
                                "accumulated": tick.volume,
                                "trade_value": tick.volume * tick.price,
                            },
                            "bid_ask": {
                                "bid_price": tick.bid_price,
                                "ask_price": tick.ask_price,
                            },
                            "source": "mock_websocket"
                        }
                        self.on_price_update(price_data)
                
                self._tick_count += 1
                await asyncio.sleep(self.tick_frequency)
        
        except asyncio.CancelledError:
            log.debug("Tick generation cancelled")
        except Exception as e:
            log.error(f"❌ Error in tick generation: {e}")
            if self.on_error:
                self.on_error(str(e))
    
    @property
    def subscription_count(self) -> int:
        return len(self.subscribed_symbols)
    
    @property
    def available_slots(self) -> int:
        return 41 - len(self.subscribed_symbols)


async def test_mock_provider():
    """Test the mock provider."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    parser = argparse.ArgumentParser(description="Mock WebSocket Provider Test")
    parser.add_argument("--duration", type=int, default=30, help="Test duration in seconds")
    parser.add_argument("--symbols", default="005930,000660,051910", help="Comma-separated symbols")
    parser.add_argument("--freq", type=float, default=0.5, help="Tick frequency (Hz)")
    
    args = parser.parse_args()
    
    symbols = set(args.symbols.split(","))
    
    print("\n" + "="*70)
    print("🧪 MOCK WEBSOCKET PROVIDER TEST")
    print("="*70)
    print(f"Duration: {args.duration}s")
    print(f"Symbols: {symbols}")
    print(f"Frequency: {args.freq}Hz")
    print("="*70 + "\n")
    
    # Create provider
    provider = MockKISWebSocketProvider(
        symbols=symbols,
        tick_frequency=args.freq
    )
    
    # Track ticks received
    tick_counts = {s: 0 for s in symbols}
    
    def on_tick(data: Dict[str, Any]) -> None:
        symbol = data.get("symbol")
        if symbol in tick_counts:
            tick_counts[symbol] += 1
            if tick_counts[symbol] % 4 == 1:  # Log every 4 ticks
                log.info(
                    f"📊 {symbol} @ {data['price']['close']} "
                    f"(bid={data['bid_ask']['bid_price']}, "
                    f"ask={data['bid_ask']['ask_price']})"
                )
    
    provider.on_price_update = on_tick
    
    # Connect and run
    await provider.connect()
    
    try:
        # Run for specified duration
        await asyncio.sleep(args.duration)
        
        # Summary
        print("\n" + "="*70)
        print("📊 SUMMARY")
        print("="*70)
        for symbol, count in tick_counts.items():
            expected = int(args.duration / args.freq)
            print(f"{symbol}: {count} ticks (expected ~{expected})")
        print("="*70 + "\n")
    
    finally:
        await provider.disconnect()


if __name__ == "__main__":
    asyncio.run(test_mock_provider())
