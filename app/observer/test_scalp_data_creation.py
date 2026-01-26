#!/usr/bin/env python3
"""
스켈프 데이터 생성 테스트

트리거 감지 후 스켈프 데이터 생성 확인
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# 경로 설정
sys.path.insert(0, 'src')

print('=== 스켈프 데이터 생성 테스트 ===')

try:
    from trigger.trigger_engine import TriggerEngine, PriceSnapshot
    from slot.slot_manager import SlotManager
    
    print('✅ 모듈 임포트 성공')
    
    # 트리거 엔진 생성 (낮은 기준)
    from trigger.trigger_engine import TriggerConfig
    config = TriggerConfig(volume_surge_ratio=2.0)
    trigger_engine = TriggerEngine(config)
    
    # 테스트 데이터 생성
    test_snapshots = []
    base_time = datetime.now(ZoneInfo('Asia/Seoul'))
    
    # 급등 데이터 생성
    for i in range(10):
        timestamp = base_time - timedelta(minutes=10-i)
        
        if i >= 5:  # 마지막 5분간 급등
            volume = 1000000
            price = 50000
        else:
            volume = 10000
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
    
    print(f'✅ 테스트 스냅샷 생성: {len(test_snapshots)} 개')
    
    # 트리거 감지
    candidates = trigger_engine.update(test_snapshots)
    print(f'✅ 트리거 감지: {len(candidates)} 개')
    
    if candidates:
        print('감지된 트리거:')
        for candidate in candidates:
            print(f'  {candidate.symbol} - {candidate.trigger_type} (우선순: {candidate.priority_score:.2f})')
        
        # 슬롯 관리자 생성
        slot_manager = SlotManager(max_slots=41)
        
        # 슬롯 할당
        allocated_slots = []
        for candidate in candidates[:5]:  # 상위 5개만
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
                print(f'  ✅ Slot {slot_id}: {candidate.symbol}')
        
        # 스켈프 데이터 생성
        print(f'\n=== 스켈프 데이터 생성 ===')
        
        scalp_data = []
        for slot in allocated_slots:
            scalp_record = {
                'timestamp': datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),
                'symbol': slot['symbol'],
                'slot_id': slot['slot_id'],
                'trigger_type': slot['trigger_type'],
                'priority_score': slot['priority_score'],
                'detected_at': slot['detected_at'],
                'details': {
                    'volume': 1000000,
                    'price': 50000,
                    'price_change': 100,
                    'high': 50200,
                    'low': 49850
                }
            }
            scalp_data.append(scalp_record)
        
        print(f'생성된 스켈프 데이터: {len(scalp_data)} 개')
        
        # 파일 저장
        scalp_dir = Path('config/observer/scalp')
        scalp_dir.mkdir(parents=True, exist_ok=True)
        
        scalp_file = scalp_dir / '20260126.jsonl'
        
        # 기존 파일 확인
        if scalp_file.exists():
            print(f'기존 파일 존재: {scalp_file}')
            with open(scalp_file, 'r', encoding='utf-8') as f:
                existing_lines = f.readlines()
                print(f'기존 레코드: {len(existing_lines)} 개')
        
        # 새로운 데이터 저장
        with open(scalp_file, 'w', encoding='utf-8') as f:
            for record in scalp_data:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        print(f'✅ 스켈프 데이터 저장: {scalp_file}')
        
        # 저장 확인
        with open(scalp_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f'파일에 저장된 레코드: {len(lines)} 개')
        
        if lines:
            print('\n저장된 데이터:')
            for line in lines:
                data = json.loads(line.strip())
                print(f'  {data["symbol"]} - Slot {data["slot_id"]} ({data["trigger_type"]})')
        
        print('\n✅ 스켈프 데이터 생성 테스트 완료')
        
    else:
        print('❌ 트리거가 감지되지 않아 스켈프 데이터 생성 불가')
    
except Exception as e:
    print(f'❌ 테스트 오류: {e}')
    import traceback
    traceback.print_exc()

print('=== 스켈프 데이터 생성 테스트 완료 ===')
