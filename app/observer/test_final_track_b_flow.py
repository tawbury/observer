#!/usr/bin/env python3
"""
Track B 전체 흐름 최종 테스트

올바른 SlotCandidate 구조 사용
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# 경로 설정
sys.path.insert(0, 'src')

print('=== Track B 전체 흐름 최종 테스트 ===')

try:
    from trigger.trigger_engine import TriggerEngine, PriceSnapshot, TriggerCandidate
    from slot.slot_manager import SlotManager, SlotCandidate
    
    print('✅ 모듈 임포트 성공')
    
    # 1. 직접 트리거 생성 (테스트용)
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
    
    # 2. 슬롯 관리자 테스트
    print('\n=== 슬롯 관리자 테스트 ===')
    slot_manager = SlotManager(max_slots=41)
    
    allocated_slots = []
    for candidate in candidates:
        # SlotCandidate 생성 (올바른 필드만 사용)
        slot_candidate = SlotCandidate(
            symbol=candidate.symbol,
            trigger_type=candidate.trigger_type,
            priority_score=candidate.priority_score,
            detected_at=candidate.detected_at
        )
        
        # 슬롯 할당
        result = slot_manager.assign_slot(slot_candidate)
        
        if result.success:
            allocated_slots.append({
                'slot_id': result.slot_id,
                'symbol': candidate.symbol,
                'trigger_type': candidate.trigger_type,
                'priority_score': candidate.priority_score,
                'detected_at': candidate.detected_at.isoformat(),
                'reason': result.reason,
                'details': candidate.details  # 트리거 상세 정보는 별도 저장
            })
            print(f'  ✅ Slot {result.slot_id}: {candidate.symbol} ({result.reason})')
        else:
            print(f'  ❌ 슬롯 할당 실패: {candidate.symbol}')
    
    print(f'할당된 슬롯: {len(allocated_slots)} 개')
    
    # 3. 스켈프 데이터 생성
    print('\n=== 스켈프 데이터 생성 ===')
    
    scalp_data = []
    for slot in allocated_slots:
        # 트리거 상세 정보 추출
        details = slot['details']
        
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
    
    # 4. 파일 저장
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
    
    # 5. 저장 확인
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
    
    # 6. Track B 로깅 메서드 테스트
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
    
    # 파일 내용 출력
    print('\n=== 파일 내용 ===')
    for i, line in enumerate(final_lines):
        data = json.loads(line.strip())
        print(f'{i+1}. {data["symbol"]} - Slot {data["slot_id"]}')
        print(f'   트리거: {data["trigger_type"]}')
        print(f'   우선순: {data["priority_score"]:.2f}')
        print(f'   상세: {data["details"]}')
    
    print('\n✅ Track B 전체 흐름 최종 테스트 완료')
    
except Exception as e:
    print(f'❌ 테스트 오류: {e}')
    import traceback
    traceback.print_exc()

print('=== Track B 전체 흐름 최종 테스트 완료 ===')
