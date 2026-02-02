#!/usr/bin/env python3
"""
간단 스켈프 데이터 생성 테스트

파일 백업 없이 직접 생성
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

_project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_project_root / "src"))

print('=== 간단 스켈프 데이터 생성 테스트 ===')

try:
    # 스켈프 데이터 생성
    scalp_data = [
        {
            'timestamp': datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),
            'symbol': '005930',
            'slot_id': 1,
            'trigger_type': 'volume_surge',
            'priority_score': 0.9,
            'detected_at': datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),
            'details': {
                'current_volume': 10000000,
                'avg_volume_10m': 1000,
                'surge_ratio': 10.0
            }
        },
        {
            'timestamp': datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),
            'symbol': '000660',
            'slot_id': 2,
            'trigger_type': 'volatility_spike',
            'priority_score': 0.95,
            'detected_at': datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),
            'details': {
                'price_change': 0.06,
                'current_price': 53000
            }
        }
    ]
    
    print(f'생성된 스켈프 데이터: {len(scalp_data)} 개')
    
    # 파일 저장
    scalp_dir = _project_root / "config" / "observer" / "scalp"
    scalp_dir.mkdir(parents=True, exist_ok=True)
    
    scalp_file = scalp_dir / '20260126.jsonl'
    
    # 직접 덮어쓰기
    with open(scalp_file, 'w', encoding='utf-8') as f:
        for record in scalp_data:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    print(f'✅ 스켈프 데이터 저장: {scalp_file}')
    
    # 저장 확인
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
    
    print('\n✅ 간단 스켈프 데이터 생성 테스트 완료')
    
except Exception as e:
    print(f'❌ 테스트 오류: {e}')
    import traceback
    traceback.print_exc()

print('=== 간단 스켈프 데이터 생성 테스트 완료 ===')
