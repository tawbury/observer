#!/usr/bin/env python3
"""
Docker 컨테이너에서 오늘 날짜의 스켈프 로그 파일을 생성하는 테스트 스크립트
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import json

now = datetime.now(ZoneInfo('Asia/Seoul'))
scalp_dir = Path('/app/config/observer/scalp')
scalp_dir.mkdir(parents=True, exist_ok=True)

date_str = now.strftime('%Y%m%d')
log_file = scalp_dir / f'{date_str}.jsonl'

# Write a test scalp entry
entry = {
    'timestamp': now.isoformat(),
    'symbol': '005930',
    'execution_time': now.isoformat(),
    'price': {
        'current': 71000,
        'open': 70500,
        'high': 71500,
        'low': 70000,
        'change_rate': 0.01
    },
    'volume': {
        'accumulated': 10000000,
        'current': 50000
    },
    'bid_ask': {},
    'source': 'websocket_test',
    'session_id': 'docker_volume_test'
}

with log_file.open('a', encoding='utf-8') as f:
    f.write(json.dumps(entry, ensure_ascii=False) + '\n')

print(f'✅ Test entry written to {log_file}')
print(f'📏 File size: {log_file.stat().st_size} bytes')

# Verify local mount
print(f'\n🔍 Verifying Docker volume mount...')
print(f'Container path: {log_file}')
print(f'Expected local path: d:/development/prj_obs/app/observer/config/observer/scalp/{date_str}.jsonl')
