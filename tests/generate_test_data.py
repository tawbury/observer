"""
Test JSONL Data Generation
생성일: 2026-01-28
설명: DB 마이그레이션 테스트용 JSONL 데이터 생성
"""

import json
from datetime import datetime, timedelta
from pathlib import Path


def generate_scalp_tick_data():
    """Scalp tick 테스트 데이터 생성"""
    test_data_dir = Path(__file__).parent / 'test_data'
    test_data_dir.mkdir(exist_ok=True)
    
    scalp_tick_file = test_data_dir / 'scalp_ticks_test.jsonl'
    
    base_time = datetime(2026, 1, 28, 9, 0, 0)
    symbols = ['005930', '000660', '051910']
    
    with open(scalp_tick_file, 'w', encoding='utf-8') as f:
        for i in range(100):  # 100개 틱 데이터 생성
            for j, symbol in enumerate(symbols):
                tick_time = base_time + timedelta(seconds=i*2 + j*0.5)  # 0.5초 간격
                
                data = {
                    "symbol": symbol,
                    "event_time": tick_time.isoformat() + "Z",
                    "bid_price": 70000 + i * 10 + j * 1000,
                    "ask_price": 70100 + i * 10 + j * 1000,
                    "bid_size": 100 + i * 5,
                    "ask_size": 200 + i * 3,
                    "last_price": 70050 + i * 10 + j * 1000,
                    "volume": 1000 + i * 100,
                    "session_id": "test_session_scalp",
                    "mitigation_level": 0,
                    "quality_flag": "normal"
                }
                
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
    
    print(f"✓ Scalp tick 테스트 데이터 생성: {scalp_tick_file}")
    return scalp_tick_file


def generate_scalp_1m_bar_data():
    """Scalp 1분 봉 테스트 데이터 생성"""
    test_data_dir = Path(__file__).parent / 'test_data'
    test_data_dir.mkdir(exist_ok=True)
    
    scalp_1m_file = test_data_dir / 'scalp_1m_bars_test.jsonl'
    
    base_time = datetime(2026, 1, 28, 9, 0, 0)
    symbols = ['005930', '000660', '051910']
    
    with open(scalp_1m_file, 'w', encoding='utf-8') as f:
        for i in range(30):  # 30분간 데이터
            for j, symbol in enumerate(symbols):
                bar_time = base_time + timedelta(minutes=i)
                
                data = {
                    "symbol": symbol,
                    "bar_time": bar_time.isoformat() + "Z",
                    "open": 70000 + i * 50 + j * 1000,
                    "high": 70200 + i * 50 + j * 1000,
                    "low": 69800 + i * 50 + j * 1000,
                    "close": 70100 + i * 50 + j * 1000,
                    "volume": 50000 + i * 1000,
                    "coverage_ratio": 0.95 - i * 0.01,  # 점진적 감소
                    "session_id": "test_session_scalp_1m",
                    "quality_flag": "normal"
                }
                
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
    
    print(f"✓ Scalp 1분 봉 테스트 데이터 생성: {scalp_1m_file}")
    return scalp_1m_file


def generate_swing_bar_data():
    """Swing 10분 봉 테스트 데이터 생성"""
    test_data_dir = Path(__file__).parent / 'test_data'
    test_data_dir.mkdir(exist_ok=True)
    
    swing_bar_file = test_data_dir / 'swing_bars_test.jsonl'
    
    base_time = datetime(2026, 1, 28, 9, 0, 0)
    symbols = ['005930', '000660', '051910']
    
    with open(swing_bar_file, 'w', encoding='utf-8') as f:
        for i in range(20):  # 20개 10분 봉 (3시간 20분)
            for j, symbol in enumerate(symbols):
                bar_time = base_time + timedelta(minutes=i*10)
                
                data = {
                    "symbol": symbol,
                    "bar_time": bar_time.isoformat() + "Z",
                    "open": 70000 + i * 100 + j * 1000,
                    "high": 70400 + i * 100 + j * 1000,
                    "low": 69600 + i * 100 + j * 1000,
                    "close": 70200 + i * 100 + j * 1000,
                    "volume": 100000 + i * 5000,
                    "bid_price": 70150 + i * 100 + j * 1000,
                    "ask_price": 70250 + i * 100 + j * 1000,
                    "session_id": "test_session_swing",
                    "schema_version": "1.0",
                    "mitigation_level": 0,
                    "quality_flag": "normal"
                }
                
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
    
    print(f"✓ Swing 10분 봉 테스트 데이터 생성: {swing_bar_file}")
    return swing_bar_file


def main():
    """테스트 데이터 생성"""
    print("DB 마이그레이션 테스트용 JSONL 데이터 생성")
    print("=" * 50)
    
    scalp_tick_file = generate_scalp_tick_data()
    scalp_1m_file = generate_scalp_1m_bar_data()
    swing_bar_file = generate_swing_bar_data()
    
    print("\n생성 완료!")
    print(f"- Scalp Tick: {scalp_tick_file} (300 lines)")
    print(f"- Scalp 1m Bar: {scalp_1m_file} (90 lines)")
    print(f"- Swing 10m Bar: {swing_bar_file} (60 lines)")


if __name__ == "__main__":
    main()