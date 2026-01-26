"""
Independent Track B Scanner - 독립적인 실시간 시장 스캐너

KIS 공식 API 기반으로 Track A와 독립적인 실시간 스캐닝 구현
- WebSocket 실시간 데이터 구독
- 이벤트 기반 트리거 감지
- 동적 슬롯 관리
- 실시간 스켈프 데이터 수집

참고: https://github.com/koreainvestment/open-trading-api
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from collections import defaultdict, deque
from pathlib import Path
from zoneinfo import ZoneInfo

from shared.time_helpers import TimeAwareMixin
from shared.trading_hours import in_trading_hours
from provider.kis.kis_websocket_provider import KISWebSocketProvider
from paths import observer_asset_dir

log = logging.getLogger("IndependentTrackBScanner")


@dataclass
class RealTimeEvent:
    """실시간 이벤트 데이터"""
    symbol: str
    event_type: str  # "volume_surge", "volatility_spike", "price_momentum"
    timestamp: datetime
    priority_score: float
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "priority_score": self.priority_score,
            "details": self.details,
        }


@dataclass
class VolumeSurgeEvent(RealTimeEvent):
    """거래량 급등 이벤트"""
    def __init__(self, symbol: str, timestamp: datetime, current_volume: int, avg_volume: float, surge_ratio: float):
        super().__init__(
            symbol=symbol,
            event_type="volume_surge",
            timestamp=timestamp,
            priority_score=0.9,
            details={
                "current_volume": current_volume,
                "avg_volume": avg_volume,
                "surge_ratio": surge_ratio
            }
        )


@dataclass
class VolatilitySpikeEvent(RealTimeEvent):
    """변동성 스파이크 이벤트"""
    def __init__(self, symbol: str, timestamp: datetime, price_change: float, current_price: float):
        super().__init__(
            symbol=symbol,
            event_type="volatility_spike",
            timestamp=timestamp,
            priority_score=0.95,
            details={
                "price_change": price_change,
                "current_price": current_price
            }
        )


class VolumeSurgeDetector:
    """실시간 거래량 급등 감지기"""
    
    def __init__(self, surge_threshold: float = 5.0, window_seconds: int = 60):
        self.surge_threshold = surge_threshold
        self.window_seconds = window_seconds
        self.volume_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_seconds))
    
    def detect(self, symbol: str, volume: int, timestamp: datetime) -> Optional[VolumeSurgeEvent]:
        """거래량 급등 감지"""
        # 거래량 기록
        self.volume_history[symbol].append((timestamp, volume))
        
        # 충분한 데이터가 있는지 확인
        if len(self.volume_history[symbol]) < 30:  # 30초 이상 데이터 필요
            return None
        
        # 평균 거래량 계산
        volumes = [v for _, v in self.volume_history[symbol]]
        avg_volume = sum(volumes) / len(volumes)
        
        # 급등 감지
        if avg_volume > 0 and volume > avg_volume * self.surge_threshold:
            surge_ratio = volume / avg_volume
            return VolumeSurgeEvent(symbol, timestamp, volume, avg_volume, surge_ratio)
        
        return None


class VolatilityDetector:
    """실시간 변동성 감지기"""
    
    def __init__(self, volatility_threshold: float = 0.05, window_seconds: int = 60):
        self.volatility_threshold = volatility_threshold
        self.window_seconds = window_seconds
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_seconds))
    
    def detect(self, symbol: str, price: float, timestamp: datetime) -> Optional[VolatilitySpikeEvent]:
        """변동성 스파이크 감지"""
        # 가격 기록
        self.price_history[symbol].append((timestamp, price))
        
        # 충분한 데이터가 있는지 확인
        if len(self.price_history[symbol]) < 30:  # 30초 이상 데이터 필요
            return None
        
        # 가격 변화 계산
        prices = [p for _, p in self.price_history[symbol]]
        if len(prices) < 2:
            return None
        
        # 첫 가격과 현재 가격 비교
        first_price = prices[0]
        price_change = abs(price - first_price) / first_price
        
        # 변동성 스파이크 감지
        if price_change > self.volatility_threshold:
            return VolatilitySpikeEvent(symbol, timestamp, price_change, price)
        
        return None


class RealTimeEventScanner:
    """실시간 이벤트 스캐너"""
    
    def __init__(self):
        self.volume_detector = VolumeSurgeDetector()
        self.volatility_detector = VolatilityDetector()
        self.event_handlers = {
            'volume_surge': self.handle_volume_surge,
            'volatility_spike': self.handle_volatility_spike,
        }
    
    def scan_price_update(self, symbol: str, price: float, volume: int, timestamp: datetime) -> List[RealTimeEvent]:
        """가격 업데이트 스캔"""
        events = []
        
        # 거래량 급등 감지
        volume_event = self.volume_detector.detect(symbol, volume, timestamp)
        if volume_event:
            events.append(volume_event)
        
        # 변동성 스파이크 감지
        volatility_event = self.volatility_detector.detect(symbol, price, timestamp)
        if volatility_event:
            events.append(volatility_event)
        
        return events
    
    def handle_volume_surge(self, event: VolumeSurgeEvent) -> bool:
        """거래량 급등 이벤트 처리"""
        log.info(f"🔥 Volume surge detected: {event.symbol} (ratio: {event.details['surge_ratio']:.2f})")
        return True
    
    def handle_volatility_spike(self, event: VolatilitySpikeEvent) -> bool:
        """변동성 스파이크 이벤트 처리"""
        log.info(f"⚡ Volatility spike detected: {event.symbol} (change: {event.details['price_change']:.2%})")
        return True


class DynamicSlotManager:
    """동적 슬롯 관리자"""
    
    def __init__(self, max_slots: int = 41):
        self.max_slots = max_slots
        self.active_slots: Dict[str, Dict] = {}  # symbol -> slot_info
        self.slot_priorities: Dict[str, float] = {}  # symbol -> priority
    
    def allocate_slot(self, event: RealTimeEvent) -> Optional[int]:
        """동적 슬롯 할당"""
        symbol = event.symbol
        priority = event.priority_score
        
        # 이미 활성화된 슬롯인지 확인
        if symbol in self.active_slots:
            # 우선순위가 더 높으면 업데이트
            if priority > self.slot_priorities.get(symbol, 0):
                self.active_slots[symbol].update({
                    'priority': priority,
                    'event_type': event.event_type,
                    'last_update': event.timestamp
                })
                self.slot_priorities[symbol] = priority
                return self.active_slots[symbol]['slot_id']
            return None
        
        # 새 슬롯 할당
        if len(self.active_slots) < self.max_slots:
            slot_id = len(self.active_slots) + 1
            self.active_slots[symbol] = {
                'slot_id': slot_id,
                'priority': priority,
                'event_type': event.event_type,
                'allocated_at': event.timestamp,
                'last_update': event.timestamp
            }
            self.slot_priorities[symbol] = priority
            return slot_id
        
        # 낮은 우선순위 슬롯 교체
        return self._replace_low_priority_slot(symbol, priority, event)
    
    def _replace_low_priority_slot(self, symbol: str, priority: float, event: RealTimeEvent) -> Optional[int]:
        """낮은 우선순위 슬롯 교체"""
        if not self.slot_priorities:
            return None
        
        # 가장 낮은 우선순위 슬롯 찾기
        lowest_symbol = min(self.slot_priorities.items(), key=lambda x: x[1])[0]
        
        if priority > self.slot_priorities[lowest_symbol]:
            slot_id = self.active_slots[lowest_symbol]['slot_id']
            
            # 기존 슬롯 제거
            del self.active_slots[lowest_symbol]
            del self.slot_priorities[lowest_symbol]
            
            # 새 슬롯 할당
            self.active_slots[symbol] = {
                'slot_id': slot_id,
                'priority': priority,
                'event_type': event.event_type,
                'allocated_at': event.timestamp,
                'last_update': event.timestamp
            }
            self.slot_priorities[symbol] = priority
            
            log.info(f"🔄 Replaced slot {slot_id}: {lowest_symbol} -> {symbol}")
            return slot_id
        
        return None
    
    def release_slot(self, symbol: str) -> bool:
        """슬롯 해제"""
        if symbol in self.active_slots:
            slot_id = self.active_slots[symbol]['slot_id']
            del self.active_slots[symbol]
            del self.slot_priorities[symbol]
            log.info(f"🔓 Released slot {slot_id}: {symbol}")
            return True
        return False
    
    def get_active_symbols(self) -> Set[str]:
        """활성화된 종목 목록"""
        return set(self.active_slots.keys())


class ScalpDataCollector:
    """스켈프 데이터 수집기"""
    
    def __init__(self, market: str = "kr_stocks"):
        self.market = market
        self.base_dir = observer_asset_dir()
        self.daily_log_subdir = "scalp"
    
    def log_scalp_data(self, symbol: str, slot_id: int, event: RealTimeEvent, price_data: Dict[str, Any]):
        """스켈프 데이터 로깅"""
        try:
            # 날짜별 파일 생성
            now = datetime.now(ZoneInfo("Asia/Seoul"))
            date_str = now.strftime("%Y%m%d")
            
            log_file = self.base_dir / self.daily_log_subdir / f"{date_str}.jsonl"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 스켈프 데이터 생성
            scalp_record = {
                "timestamp": now.isoformat(),
                "symbol": symbol,
                "slot_id": slot_id,
                "event_type": event.event_type,
                "priority_score": event.priority_score,
                "details": event.details,
                "price_data": price_data,
                "market": self.market
            }
            
            # 파일에 기록
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(scalp_record, ensure_ascii=False) + '\n')
            
            log.debug(f"Scalp data logged: {symbol} (slot {slot_id})")
            
        except Exception as e:
            log.error(f"Error logging scalp data: {e}", exc_info=True)


class IndependentTrackBScanner(TimeAwareMixin):
    """독립적인 Track B 실시간 스캐너"""
    
    def __init__(self, market: str = "kr_stocks", max_slots: int = 41):
        self._tz_name = "Asia/Seoul"
        self.market = market
        self.max_slots = max_slots
        
        # 컴포넌트 초기화
        self.websocket_provider = None
        self.event_scanner = RealTimeEventScanner()
        self.slot_manager = DynamicSlotManager(max_slots)
        self.scalp_collector = ScalpDataCollector(market)
        
        # 상태
        self._running = False
        self._subscribed_symbols: Set[str] = set()
        self._universe_symbols: List[str] = []
        
        # WebSocket 콜백 등록
        self._price_update_callback = None
    
    async def start(self) -> None:
        """독립적인 실시간 스캐닝 시작"""
        log.info("IndependentTrackBScanner started (max_slots=%d)", self.max_slots)
        self._running = True
        
        try:
            # 1. WebSocket 연결
            await self._start_websocket()
            
            # 2. 가격 업데이트 콜백 등록
            self._register_price_callback()
            
            # 3. Universe 로드
            await self._load_universe()
            
            # 4. 메인 스캐닝 루프
            await self._scanning_loop()
            
        except Exception as e:
            log.error(f"IndependentTrackBScanner error: {e}", exc_info=True)
        finally:
            await self._stop_websocket()
    
    async def stop(self) -> None:
        """스캐너 중지"""
        log.info("IndependentTrackBScanner stopping...")
        self._running = False
    
    async def _start_websocket(self) -> None:
        """WebSocket 연결 시작"""
        self.websocket_provider = KISWebSocketProvider()
        await self.websocket_provider.connect()
        log.info("WebSocket connected successfully")
    
    async def _stop_websocket(self) -> None:
        """WebSocket 연결 종료"""
        if self.websocket_provider:
            await self.websocket_provider.disconnect()
            log.info("WebSocket disconnected")
    
    def _register_price_callback(self) -> None:
        """가격 업데이트 콜백 등록"""
        self._price_update_callback = self._on_price_update
        if self.websocket_provider:
            self.websocket_provider.register_price_callback(self._price_update_callback)
        log.info("Price update callback registered")
    
    async def _load_universe(self) -> None:
        """Universe 로드"""
        try:
            universe_file = self.base_dir / "config" / "universe" / f"{datetime.now().strftime('%Y%m%d')}_kr_stocks.json"
            
            if universe_file.exists():
                with open(universe_file, 'r') as f:
                    universe_data = json.load(f)
                    self._universe_symbols = universe_data.get('symbols', [])
                
                log.info(f"Loaded universe: {len(self._universe_symbols)} symbols")
            else:
                log.warning("Universe file not found, using empty universe")
                self._universe_symbols = []
                
        except Exception as e:
            log.error(f"Error loading universe: {e}", exc_info=True)
            self._universe_symbols = []
    
    async def _scanning_loop(self) -> None:
        """메인 스캐닝 루프"""
        while self._running:
            now = self._now()
            
            # 거래 시간 체크
            if not in_trading_hours(now, time(9, 30), time(15, 30)):
                log.info("Outside trading hours, waiting...")
                await asyncio.sleep(60)
                continue
            
            # Universe 구독 관리
            await self._manage_subscriptions()
            
            # 대기
            await asyncio.sleep(30)  # 30초마다 구독 상태 확인
    
    async def _manage_subscriptions(self) -> None:
        """구독 관리"""
        try:
            # 현재 활성화된 종목
            active_symbols = self.slot_manager.get_active_symbols()
            
            # 구독해야 할 종목 (활성화된 종목)
            symbols_to_subscribe = active_symbols - self._subscribed_symbols
            
            # 구독 해제할 종목
            symbols_to_unsubscribe = self._subscribed_symbols - active_symbols
            
            # 구독 실행
            if symbols_to_subscribe and self.websocket_provider:
                symbols_list = list(symbols_to_subscribe)
                await self._subscribe_symbols(symbols_list)
            
            # 구독 해제 실행
            if symbols_to_unsubscribe and self.websocket_provider:
                symbols_list = list(symbols_to_unsubscribe)
                await self._unsubscribe_symbols(symbols_list)
                
        except Exception as e:
            log.error(f"Error managing subscriptions: {e}", exc_info=True)
    
    async def _subscribe_symbols(self, symbols: List[str]) -> None:
        """종목 구독"""
        try:
            # KIS WebSocket 구독 형식에 맞게 변환
            for symbol in symbols:
                # 실시간 호가 구독
                await self.websocket_provider.subscribe(symbol)
                self._subscribed_symbols.add(symbol)
                log.debug(f"Subscribed: {symbol}")
                
        except Exception as e:
            log.error(f"Error subscribing symbols {symbols}: {e}", exc_info=True)
    
    async def _unsubscribe_symbols(self, symbols: List[str]) -> None:
        """종목 구독 해제"""
        try:
            for symbol in symbols:
                await self.websocket_provider.unsubscribe(symbol)
                self._subscribed_symbols.discard(symbol)
                log.debug(f"Unsubscribed: {symbol}")
                
        except Exception as e:
            log.error(f"Error unsubscribing symbols {symbols}: {e}", exc_info=True)
    
    def _on_price_update(self, symbol: str, price_data: Dict[str, Any]) -> None:
        """가격 업데이트 처리"""
        try:
            # 가격 데이터 파싱
            price = float(price_data.get('price', 0))
            volume = int(price_data.get('volume', 0))
            timestamp = self._now()
            
            # 이벤트 스캔
            events = self.event_scanner.scan_price_update(symbol, price, volume, timestamp)
            
            # 이벤트 처리
            for event in events:
                self._handle_event(event, price_data)
                
        except Exception as e:
            log.error(f"Error processing price update for {symbol}: {e}", exc_info=True)
    
    def _handle_event(self, event: RealTimeEvent, price_data: Dict[str, Any]) -> None:
        """이벤트 처리"""
        try:
            # 이벤트 핸들러 실행
            handler = self.event_scanner.event_handlers.get(event.event_type)
            if handler and handler(event):
                # 슬롯 할당
                slot_id = self.slot_manager.allocate_slot(event)
                
                if slot_id:
                    # 슬롯 할당 성공
                    log.info(f"✅ Slot {slot_id}: {event.symbol} (priority={event.priority_score:.2f}, trigger={event.event_type})")
                    
                    # 스켈프 데이터 수집
                    self.scalp_collector.log_scalp_data(event.symbol, slot_id, event, price_data)
                else:
                    # 슬롯 할당 실패
                    log.warning(f"⚠️ No slot available for {event.symbol} (priority={event.priority_score:.2f})")
                    
        except Exception as e:
            log.error(f"Error handling event {event.event_type} for {event.symbol}: {e}", exc_info=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 정보"""
        return {
            "active_slots": len(self.slot_manager.active_slots),
            "subscribed_symbols": len(self._subscribed_symbols),
            "universe_size": len(self._universe_symbols),
            "running": self._running,
            "market": self.market
        }
