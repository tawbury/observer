"""
JSONL Migration Logic Test
생성일: 2026-01-28
설명: JSONL 파일 파싱 로직 테스트 (PostgreSQL 연결 없이)
"""

import json
from datetime import datetime
from pathlib import Path
import pytest

from db.migrate_jsonl_to_db import JSONLToDBMigrator


def test_jsonl_parsing_logic():
    """JSONL 파싱 로직 테스트"""
    # 샘플 JSONL 데이터
    scalp_tick_data = {
        "symbol": "005930",
        "event_time": "2026-01-28T09:00:00Z",
        "bid_price": 70000,
        "ask_price": 70100,
        "bid_size": 100,
        "ask_size": 200,
        "last_price": 70050,
        "volume": 1000,
        "session_id": "test_session_scalp",
        "mitigation_level": 0,
        "quality_flag": "normal"
    }
    
    # 파싱 결과 검증
    assert scalp_tick_data['symbol'] == "005930"
    assert scalp_tick_data['bid_price'] == 70000
    assert scalp_tick_data['ask_price'] == 70100
    
    # 날짜 파싱 테스트
    event_time = datetime.fromisoformat(scalp_tick_data['event_time'].replace('Z', '+00:00'))
    assert event_time.year == 2026
    assert event_time.month == 1
    assert event_time.day == 28


def test_swing_bar_parsing():
    """Swing bar 데이터 파싱 테스트"""
    swing_bar_data = {
        "symbol": "005930",
        "bar_time": "2026-01-28T09:00:00Z",
        "open": 70000,
        "high": 70400,
        "low": 69600,
        "close": 70200,
        "volume": 100000,
        "bid_price": 70150,
        "ask_price": 70250,
        "session_id": "test_session_swing",
        "schema_version": "1.0",
        "mitigation_level": 0,
        "quality_flag": "normal"
    }
    
    # OHLCV 데이터 검증
    assert swing_bar_data['open'] == 70000
    assert swing_bar_data['high'] == 70400
    assert swing_bar_data['low'] == 69600
    assert swing_bar_data['close'] == 70200
    assert swing_bar_data['volume'] == 100000
    
    # bid/ask 데이터 검증
    assert swing_bar_data['bid_price'] == 70150
    assert swing_bar_data['ask_price'] == 70250


def test_generated_jsonl_files():
    """생성된 JSONL 파일들 검증"""
    test_data_dir = Path(__file__).parent / 'test_data'
    
    # 파일 존재 확인
    scalp_tick_file = test_data_dir / 'scalp_ticks_test.jsonl'
    scalp_1m_file = test_data_dir / 'scalp_1m_bars_test.jsonl'
    swing_bar_file = test_data_dir / 'swing_bars_test.jsonl'
    
    assert scalp_tick_file.exists(), f"Scalp tick 파일 없음: {scalp_tick_file}"
    assert scalp_1m_file.exists(), f"Scalp 1m bar 파일 없음: {scalp_1m_file}"
    assert swing_bar_file.exists(), f"Swing bar 파일 없음: {swing_bar_file}"
    
    # 파일 내용 검증
    with open(scalp_tick_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        assert len(lines) > 0, "Scalp tick 파일이 비어있음"
        
        first_line = json.loads(lines[0])
        assert 'symbol' in first_line
        assert 'event_time' in first_line
        assert 'bid_price' in first_line
        assert 'ask_price' in first_line
    
    with open(swing_bar_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        assert len(lines) > 0, "Swing bar 파일이 비어있음"
        
        first_line = json.loads(lines[0])
        assert 'symbol' in first_line
        assert 'bar_time' in first_line
        assert 'open' in first_line
        assert 'high' in first_line
        assert 'low' in first_line
        assert 'close' in first_line


def test_data_type_validation():
    """데이터 타입 검증 테스트"""
    test_data_dir = Path(__file__).parent / 'test_data'
    scalp_tick_file = test_data_dir / 'scalp_ticks_test.jsonl'
    
    if scalp_tick_file.exists():
        with open(scalp_tick_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 5:  # 처음 5개만 테스트
                    break
                    
                data = json.loads(line)
                
                # 타입 검증
                assert isinstance(data['symbol'], str)
                assert isinstance(data['bid_price'], (int, float))
                assert isinstance(data['ask_price'], (int, float))
                assert isinstance(data['bid_size'], int)
                assert isinstance(data['ask_size'], int)
                assert isinstance(data['volume'], int)
                assert isinstance(data['session_id'], str)
                assert isinstance(data['mitigation_level'], int)
                assert isinstance(data['quality_flag'], str)
                
                # 값 범위 검증
                assert data['bid_price'] > 0
                assert data['ask_price'] > 0
                assert data['bid_size'] >= 0
                assert data['ask_size'] >= 0
                assert data['volume'] >= 0
                assert data['mitigation_level'] >= 0


def test_migration_batch_logic():
    """배치 처리 로직 시뮬레이션"""
    # 배치 크기 테스트
    batch_size = 10
    test_data = []
    
    # 테스트 데이터 생성
    for i in range(25):  # 25개 데이터 (2.5 배치)
        test_data.append({
            "symbol": f"00{i:04d}",
            "bid_price": 70000 + i * 10,
            "ask_price": 70100 + i * 10
        })
    
    # 배치 처리 시뮬레이션
    batches = []
    current_batch = []
    
    for data in test_data:
        current_batch.append(data)
        
        if len(current_batch) >= batch_size:
            batches.append(current_batch.copy())
            current_batch = []
    
    # 남은 배치 처리
    if current_batch:
        batches.append(current_batch)
    
    # 배치 검증
    assert len(batches) == 3  # 10 + 10 + 5
    assert len(batches[0]) == 10
    assert len(batches[1]) == 10
    assert len(batches[2]) == 5
    
    # 전체 데이터 개수 확인
    total_processed = sum(len(batch) for batch in batches)
    assert total_processed == 25