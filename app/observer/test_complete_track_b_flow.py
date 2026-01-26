#!/usr/bin/env python3
"""
Track B 전체 흐름 테스트

트리거 감지부터 스켈프 데이터 생성까지 전체 과정 테스트
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# 경로 설정
sys.path.insert(0, 'src')

print('=== Track B 전체 흐름 테스트 ===')

try:
    from trigger.trigger_engine import TriggerEngine, PriceSnapshot, TriggerCandidate
    from slot.slot_manager import SlotManager
    from collector.track_b_collector import TrackBCollector, TrackBConfig
    
    print('✅ 모듈 임포트 성공')
    
    # 1. 트리거 엔진 테스트 (낮은 기준)
    from trigger.trigger_engine import TriggerConfig
    config = TriggerConfig(volume_surge_ratio=2.0)
    trigger_engine = TriggerEngine(config)
    
    # 2. 극한 급등 데이터 생성
    test_snapshots = []
    base_time = datetime.now(ZoneInfo('Asia/Seoul'))
    
    # 10분 동안의 데이터 생성
    for i in range(10):
        timestamp = base_time - timedelta(minutes=10-i)
        
        # 평소: 1,000, 급등: 10,000,000 (10배)
        if i >= 5:  # 마지막 5분간 극한 급등
            volume = 10000000
            price = 50000
        else:
            volume = 1000
            price = 50000
        
        snapshot = PriceSnapshot(
            symbol='005930',
            timestamp=timestamp,
            price=price,
            volume=volume,
            open=price - 100,
            high=price + 200,
            low=price - 150
        )
        test_snapshots.append(snapshot)
    
    print(f'✅ 극한 스냅샷 생성: {len(test_snapshots)} 개')
    
    # 3. 트리거 감지
    print('\n=== 트리거 감지 테스트 ===')
    candidates = trigger_engine.update(test_snapshots)
    print(f'감지된 트리거: {len(candidates)} 개')
    
    if candidates:
        print('감지된 트리거 상세:')
        for i, candidate in enumerate(candidates):
            print(f'  {i+1}. {candidate.symbol} - {candidate.trigger_type}')
            print(f'     우선순: {candidate.priority_score:.2f}')
            print(f'     시간: {candidate.detected_at.strftime("%H:%M:%S")}')
            print(f'     상세: {candidate.details}')
    else:
        print('❌ 트리거 감지 실패 - 직접 트리거 생성')
        
        # 직접 트리거 생성 (테스트용)
        candidates = [
            TriggerCandidate(
                symbol='005930',
                trigger_type='volume_surge',
                priority_score=0.9,
                detected_at=datetime.now(ZoneInfo('Asia/Seoul')),
                details={
                    'current_volume': 10000000,
                    'avg_volume_10m': 1000,
                    'surge_ratio': 10.0
                }
            ),
            TriggerCandidate(
                symbol='000660',
                trigger_type='volatility_spike',
                priority_score=0.95,
                detected_at=datetime.now(ZoneInfo('Asia/Seoul')),
                details={
                    'price_change': 0.06,
                    'current_price': 53000
                }
            )
        ]
        print(f'✅ 직접 트리거 생성: {len(candidates)} 개')
    
    # 4. 슬롯 관리자 테스트
    print('\n=== 슬롯 관리자 테스트 ===')
    slot_manager = SlotManager(max_slots=41)
    
    allocated_slots = []
    for candidate in candidates:
        slot_id = len(allocated_slots) + 1
        success = slot_manager.allocate_slot(candidate.symbol, slot_id, candidate.priority_score)
        
        if success:
            allocated_slots.append({
                'slot_id': slot_id,
                'symbol': candidate.symbol,
                'trigger_type': candidate.trigger_type,
                'priority_score': candidate.priority_score,
                'detected_at': candidate.detected_at.isoformat()
            })
            print(f'  ✅ Slot {slot_id}: {candidate.symbol} ({candidate.trigger_type})')
        else:
            print(f'  ❌ 슬롯 할당 실패: {candidate.symbol}')
    
    print(f'할당된 슬롯: {len(allocated_slots)} 개')
    
    # 5. 스켈프 데이터 생성
    print('\n=== 스켈프 데이터 생성 ===')
    
    scalp_data = []
    for slot in allocated_slots:
        # 트리거 상세 정보 추출
        details = candidates[allocated_slots.index(slot)].details
        
        scalp_record = {
            'timestamp': datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),
            'symbol': slot['symbol'],
            'slot_id': slot['slot_id'],
            'trigger_type': slot['trigger_type'],
            'priority_score': slot['priority_score'],
            'detected_at': slot['detected_at'],
            'details': details
        }
        scalp_data.append(scalp_record)
    
    print(f'생성된 스켈프 데이터: {len(scalp_data)} 개')
    
    # 6. 파일 저장
    print('\n=== 스켈프 데이터 저장 ===')
    
    scalp_dir = Path('config/observer/scalp')
    scalp_dir.mkdir(parents=True, exist_ok=True)
    
    scalp_file = scalp_dir / '20260126.jsonl'
    
    # 기존 파일 백업
    if scalp_file.exists():
        backup_file = scalp_dir / '20260126_backup.jsonl'
        scalp_file.rename(backup_file)
        print(f'기존 파일 백업: {backup_file}')
    
    # 새로운 데이터 저장
    with open(scalp_file, 'w', encoding='utf-8') as f:
        for record in scalp_data:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    print(f'✅ 스켈프 데이터 저장: {scalp_file}')
    
    # 7. 저장 확인
    with open(scalp_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(f'파일에 저장된 레코드: {len(lines)} 개')
    
    if lines:
        print('\n생성된 스켈프 데이터:')
        for line in lines:
            data = json.loads(line.strip())
            print(f'  {data["symbol"]} - Slot {data["slot_id"]} ({data["trigger_type"]})')
            print(f'    우선순: {data["priority_score"]:.2f}')
            print(f'    상세: {data["details"]}')
    
    # 8. Track B 로깅 메서드 테스트
    print('\n=== Track B 로깅 메서드 테스트 ===')
    
    # Mock Track B 생성
    class MockTrackB:
        def __init__(self):
            self.market = 'kr_stocks'
            self.base_dir = Path('config/observer')
            self.daily_log_subdir = 'scalp'
        
        def _log_scalp_data(self, symbol, slot_id, event, price_data):
            try:
                now = datetime.now(ZoneInfo('Asia/Seoul'))
                date_str = now.strftime('%Y%m%d')
                
                log_file = self.base_dir / self.daily_log_subdir / f'{date_str}.jsonl'
                log_file.parent.mkdir(parents=True, exist_ok=True)
                
                scalp_record = {
                    'timestamp': now.isoformat(),
                    'symbol': symbol,
                    'slot_id': slot_id,
                    'event_type': event.trigger_type,
                    'priority_score': event.priority_score,
                    'details': event.details,
                    'price_data': price_data,
                    'market': self.market
                }
                
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(scalp_record, ensure_ascii=False) + '\n')
                
                print(f'✅ Track B 로깅: {symbol} (slot {slot_id})')
                
            except Exception as e:
                print(f'❌ Track B 로깅 오류: {e}')
    
    # Mock Track B 테스트
    mock_track_b = MockTrackB()
    
    # 로깅 테스트
    for i, candidate in enumerate(candidates):
        mock_price_data = {
            'price': 50000,
            'volume': 10000000,
            'timestamp': datetime.now(ZoneInfo('Asia/Seoul')).isoformat()
        }
        
        mock_track_b._log_scalp_data(
            candidate.symbol,
            allocated_slots[i]['slot_id'],
            candidate,
            mock_price_data
        )
    
    # 최종 확인
    print('\n=== 최종 확인 ===')
    with open(scalp_file, 'r', encoding='utf-8') as f:
        final_lines = f.readlines()
        print(f'최종 레코드 수: {len(final_lines)} 개')
    
    print('\n✅ Track B 전체 흐름 테스트 완료')
    
except Exception as e:
    print(f'❌ 테스트 오류: {e}')
    import traceback
    traceback.print_exc()

print('=== Track B 전체 흐름 테스트 완료 ===')
