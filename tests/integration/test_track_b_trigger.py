#!/usr/bin/env python3
"""
Track B 트리거 감지 테스트

히스토리 데이터를 충분히 제공하여 트리거 감지 테스트
"""
import asyncio
import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

_project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_project_root / "app" / "observer" / "src"))

print('=== Track B 트리거 감지 테스트 ===')

try:
    from trigger.trigger_engine import TriggerEngine, PriceSnapshot
    
    print('✅ 모듈 임포트 성공')
    
    # 트리거 엔진 생성
    trigger_engine = TriggerEngine()
    print('✅ 트리거 엔진 생성 성공')
    
    # 히스토리 데이터가 있는 스냅샷 생성
    def create_historical_snapshots():
        """히스토리 데이터가 있는 스냅샷 생성"""
        snapshots = []
        base_time = datetime.now(ZoneInfo('Asia/Seoul'))
        
        # 삼성전자 (005930) - 거래량 급등 시뮬레이션
        symbol = '005930'
        
        # 15분 동안의 데이터 생성 (1분 간격)
        for i in range(15):
            timestamp = base_time - timedelta(minutes=15-i)
            
            # 평소 거래량: 100,000
            # 급등 시점: 1,000,000 (10배)
            if i >= 10:  # 마지막 5분간 급등
                volume = 1000000
                price = 50000 + (i * 100)
            else:
                volume = 100000
                price = 50000
            
            snapshot = PriceSnapshot(
                symbol=symbol,
                timestamp=timestamp,
                price=price,
                volume=volume,
                open=price - 50,
                high=price + 100,
                low=price - 75
            )
            snapshots.append(snapshot)
        
        # SK하이닉스 (000660) - 변동성 스파이크 시뮬레이션
        symbol = '000660'
        
        for i in range(15):
            timestamp = base_time - timedelta(minutes=15-i)
            
            # 평소 가격: 60,000
            # 스파이크 시점: 63,000 (5% 상승)
            if i >= 10:  # 마지막 5분간 스파이크
                price = 63000 + (i * 10)
            else:
                price = 60000
            
            snapshot = PriceSnapshot(
                symbol=symbol,
                timestamp=timestamp,
                price=price,
                volume=50000,
                open=60000,
                high=price + 50,
                low=price - 50
            )
            snapshots.append(snapshot)
        
        return snapshots
    
    # 히스토리 데이터 생성
    historical_snapshots = create_historical_snapshots()
    print(f'✅ 히스토리 스냅샷 생성: {len(historical_snapshots)} 개')
    
    # 트리거 엔진에 점진적 업데이트
    print('\n=== 트리거 엔진 점진적 업데이트 테스트 ===')
    
    candidates = []
    for i, snapshot in enumerate(historical_snapshots):
        new_candidates = trigger_engine.update([snapshot])
        
        if new_candidates:
            print(f'시점 {i+1}: {snapshot.symbol} - {snapshot.timestamp.strftime("%H:%M:%S")} - {len(new_candidates)} 개 트리거 감지')
            for candidate in new_candidates:
                print(f'  ✅ {candidate.symbol} - {candidate.trigger_type} (우선순: {candidate.priority_score:.2f})')
                candidates.append(candidate)
        else:
            if i % 5 == 0:  # 5개마다 출력
                print(f'시점 {i+1}: {snapshot.symbol} - {snapshot.timestamp.strftime("%H:%M:%S")} - 트리거 없음')
    
    print(f'\n총 감지된 트리거: {len(candidates)} 개')
    
    if candidates:
        print('\n감지된 트리거 상세:')
        for i, candidate in enumerate(candidates):
            print(f'  {i+1}. {candidate.symbol} - {candidate.trigger_type}')
            print(f'     시간: {candidate.detected_at.strftime("%H:%M:%S")}')
            print(f'     우선순: {candidate.priority_score:.2f}')
            print(f'     상세: {candidate.details}')
    
    # 슬롯 관리자 테스트
    print('\n=== 슬롯 관리자 테스트 ===')
    from slot.slot_manager import SlotManager
    
    slot_manager = SlotManager(max_slots=41)
    
    # 슬롯 할당
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
    
    print(f'\n할당된 슬롯: {len(allocated_slots)} 개')
    
    # 스켈프 데이터 생성
    print('\n=== 스켈프 데이터 생성 테스트 ===')
    
    # 스켈프 데이터 디렉토리 생성
    scalp_dir = _project_root / "app" / "observer" / "config" / "observer" / "scalp"
    scalp_dir.mkdir(parents=True, exist_ok=True)
    
    # 스켈프 데이터 생성
    scalp_data = []
    for slot in allocated_slots:
        # 해당 종목의 최신 스냅샷 찾기
        latest_snapshot = max(
            [s for s in historical_snapshots if s.symbol == slot['symbol']],
            key=lambda x: x.timestamp
        )
        
        scalp_record = {
            'timestamp': datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),
            'symbol': slot['symbol'],
            'slot_id': slot['slot_id'],
            'trigger_type': slot['trigger_type'],
            'priority_score': slot['priority_score'],
            'detected_at': slot['detected_at'],
            'details': {
                'volume': latest_snapshot.volume,
                'price': latest_snapshot.price,
                'price_change': latest_snapshot.price - latest_snapshot.open,
                'high': latest_snapshot.high,
                'low': latest_snapshot.low
            }
        }
        scalp_data.append(scalp_record)
    
    # 스켈프 데이터 파일 저장
    scalp_file = scalp_dir / '20260126.jsonl'
    
    # 기존 파일이 있으면 백업
    if scalp_file.exists():
        backup_file = scalp_dir / '20260126_backup.jsonl'
        scalp_file.rename(backup_file)
        print(f'기존 파일 백업: {backup_file}')
    
    # 새로운 스켈프 데이터 저장
    with open(scalp_file, 'w', encoding='utf-8') as f:
        for record in scalp_data:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    print(f'✅ 스켈프 데이터 저장: {scalp_file}')
    print(f'생성된 스켈프 데이터: {len(scalp_data)} 개')
    
    # 저장된 데이터 확인
    with open(scalp_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(f'파일에 저장된 레코드: {len(lines)} 개')
    
    if lines:
        print('\n생성된 스켈프 데이터:')
        for line in lines:
            data = json.loads(line.strip())
            print(f'  {data["symbol"]} - Slot {data["slot_id"]} ({data["trigger_type"]})')
            print(f'    가격: {data["details"]["price"]:,} (변화: {data["details"]["price_change"]:,})')
            print(f'    거래량: {data["details"]["volume"]:,}')
    
    print('\n✅ Track B 트리거 감지 테스트 완료')
    
except Exception as e:
    print(f'❌ 테스트 오류: {e}')
    import traceback
    traceback.print_exc()

print('=== Track B 로컬 테스트 완료 ===')
