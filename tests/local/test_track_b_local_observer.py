#!/usr/bin/env python3
"""
Track B 로컬 테스트 스크립트 (observer 쪽)

트리거 감지 및 스켈프 데이터 생성 기능 테스트
"""
import asyncio
import sys
import os
import json
from pathlib import Path
from datetime import datetime, time
from zoneinfo import ZoneInfo

_project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_project_root / "app" / "observer" / "src"))

print('=== Track B 트리거 감지 및 스켈프 데이터 생성 테스트 ===')

try:
    from collector.track_b_collector import TrackBCollector, TrackBConfig
    from provider.kis.kis_auth import KISAuth
    from provider import ProviderEngine
    from trigger.trigger_engine import TriggerEngine, PriceSnapshot
    
    print('✅ 모듈 임포트 성공')
    
    # Track B 설정
    config = TrackBConfig()
    print(f'Track B 설정: {config}')
    
    # Mock 객체 생성
    class MockAuth:
        def get_websocket_approval_key(self):
            return 'mock_approval_key'
    
    class MockProviderEngine:
        def __init__(self, auth):
            self.auth = auth
            self.ws_connected = False
        
        async def connect_websocket(self):
            self.ws_connected = True
            print('✅ Mock WebSocket 연결 성공')
        
        async def disconnect_websocket(self):
            self.ws_connected = False
            print('✅ Mock WebSocket 연결 해제')
    
    # Mock 객체 생성
    mock_auth = MockAuth()
    mock_engine = MockProviderEngine(mock_auth)
    trigger_engine = TriggerEngine()
    
    # Track B 생성
    track_b = TrackBCollector(mock_engine, trigger_engine, config)
    print('✅ Track B 인스턴스 생성 성공')
    
    # 테스트용 스윙 데이터 생성
    def create_test_swing_data():
        """테스트용 스윙 데이터 생성"""
        test_data = []
        symbols = ['005930', '000660', '035420', '051910', '068270']
        
        for i, symbol in enumerate(symbols):
            # 트리거를 유발하는 데이터 생성
            volume = 1000000 + (i * 500000)  # 높은 거래량
            price = 50000 + (i * 1000)
            
            snapshot = PriceSnapshot(
                symbol=symbol,
                timestamp=datetime.now(ZoneInfo('Asia/Seoul')),
                price=price,
                volume=volume,
                open=price - 100,
                high=price + 200,
                low=price - 150
            )
            test_data.append(snapshot)
        
        return test_data
    
    # 테스트 데이터 생성
    test_snapshots = create_test_swing_data()
    print(f'✅ 테스트 스냅샷 생성: {len(test_snapshots)} 개')
    
    # 트리거 엔진 테스트
    print('\n=== 트리거 엔진 테스트 ===')
    candidates = trigger_engine.update(test_snapshots)
    print(f'감지된 트리거: {len(candidates)} 개')
    
    if candidates:
        print('감지된 트리거 상세:')
        for i, candidate in enumerate(candidates[:5]):
            print(f'  {i+1}. {candidate.symbol} - {candidate.trigger_type} (우선순: {candidate.priority_score:.2f})')
    
    # 슬롯 관리자 테스트
    print('\n=== 슬롯 관리자 테스트 ===')
    from slot.slot_manager import SlotManager
    
    slot_manager = SlotManager(max_slots=config.max_slots)
    
    # 슬롯 할당
    allocated_slots = []
    for candidate in candidates[:config.max_slots]:
        slot_id = len(allocated_slots) + 1
        slot_manager.allocate_slot(candidate.symbol, slot_id, candidate.priority_score)
        allocated_slots.append({
            'slot_id': slot_id,
            'symbol': candidate.symbol,
            'trigger_type': candidate.trigger_type,
            'priority_score': candidate.priority_score
        })
    
    print(f'할당된 슬롯: {len(allocated_slots)} 개')
    for slot in allocated_slots[:5]:
        print(f'  Slot {slot["slot_id"]}: {slot["symbol"]} ({slot["trigger_type"]})')
    
    # 스켈프 데이터 생성 테스트
    print('\n=== 스켈프 데이터 생성 테스트 ===')
    
    # 스켈프 데이터 디렉토리 생성
    scalp_dir = _project_root / "app" / "observer" / "config" / "observer" / "scalp"
    scalp_dir.mkdir(parents=True, exist_ok=True)
    
    # 스켈프 데이터 생성
    scalp_data = []
    for slot in allocated_slots[:5]:
        scalp_record = {
            'timestamp': datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),
            'symbol': slot['symbol'],
            'slot_id': slot['slot_id'],
            'trigger_type': slot['trigger_type'],
            'priority_score': slot['priority_score'],
            'details': {
                'volume': next(s.volume for s in test_snapshots if s.symbol == slot['symbol']),
                'price': next(s.price for s in test_snapshots if s.symbol == slot['symbol'])
            }
        }
        scalp_data.append(scalp_record)
    
    # 스켈프 데이터 파일 저장
    scalp_file = scalp_dir / '20260126.jsonl'
    with open(scalp_file, 'a', encoding='utf-8') as f:
        for record in scalp_data:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    print(f'✅ 스켈프 데이터 저장: {scalp_file}')
    print(f'생성된 스켈프 데이터: {len(scalp_data)} 개')
    
    # 저장된 데이터 확인
    with open(scalp_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(f'파일에 저장된 레코드: {len(lines)} 개')
    
    if lines:
        print('최근 스켈프 데이터:')
        for line in lines[-3:]:
            data = json.loads(line.strip())
            print(f'  {data["symbol"]} - Slot {data["slot_id"]} ({data["trigger_type"]})')
    
    print('\n✅ Track B 트리거 감지 및 스켈프 데이터 생성 테스트 완료')
    
except Exception as e:
    print(f'❌ 테스트 오류: {e}')
    import traceback
    traceback.print_exc()

print('=== Track B 로컬 테스트 완료 ===')
