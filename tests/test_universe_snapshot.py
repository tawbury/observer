#!/usr/bin/env python3
"""Test UniverseManager with kr_all_symbols.txt file-based snapshot generation."""

import sys
import os
sys.path.insert(0, 'app/obs_deploy/app/src')

# KIS 자격증명 (테스트용)
os.environ['KIS_APP_KEY'] = os.environ.get('KIS_APP_KEY', 'TEST_KEY_PLACEHOLDER')
os.environ['KIS_APP_SECRET'] = os.environ.get('KIS_APP_SECRET', 'TEST_SECRET_PLACEHOLDER')
os.environ['KIS_IS_VIRTUAL'] = 'true'

import asyncio
import json
from datetime import date
from universe.universe_manager import UniverseManager

# Mock provider (파일 기반만 테스트)
class MockEngine:
    async def fetch_stock_list(self, market='ALL'):
        print("[INFO] KIS API 조회 시도...")
        return []  # API 실패 시뮬레이션
    
    async def fetch_daily_prices(self, symbol, days=2):
        # UniverseManager._extract_prev_close()의 기대 형식
        import random
        close_price = random.randint(10000, 100000)
        return [{
            'instruments': [{
                'symbol': symbol,
                'price': {
                    'close': close_price
                }
            }]
        }]

async def test_run_once():
    print("🧪 UniverseScheduler run_once() 테스트")
    print("=" * 60)
    print()
    
    engine = MockEngine()
    manager = UniverseManager(
        provider_engine=engine,
        market='kr_stocks',
        min_price=4000,
        min_count=100
    )
    
    today = date.today()
    print(f"📅 대상 날짜: {today.isoformat()}")
    print()
    
    try:
        # 스냅샷 생성
        print("⏳ 스냅샷 생성 중... (병렬 가격 조회, Semaphore(5) 동시성)")
        snapshot_path = await manager.create_daily_snapshot(today)
        
        print(f"✅ 스냅샷 생성 완료")
        print(f"📄 경로: {snapshot_path}")
        print()
        
        # 결과 출력
        with open(snapshot_path, encoding='utf-8') as f:
            snapshot = json.load(f)
        
        print("📊 스냅샷 내용:")
        print(f"  - 날짜: {snapshot['date']}")
        print(f"  - 시장: {snapshot['market']}")
        print(f"  - 필터 기준 가격: >= {snapshot['filter_criteria']['min_price']:,}원")
        print(f"  - 이전 거래일: {snapshot['filter_criteria']['prev_trading_day']}")
        print(f"  - ✅ 최종 종목 수: {snapshot['count']:,}개")
        print()
        
        if snapshot['count'] >= 1000:
            print(f"🎉 성공! 기대 기준(>= 1,000개)을 충족했습니다.")
        else:
            print(f"⚠️ 경고: 기대보다 적음 ({snapshot['count']:,}개 < 1,000개)")
        
        print()
        print(f"📍 첫 5개 종목: {snapshot['symbols'][:5]}")
        print(f"📍 마지막 5개 종목: {snapshot['symbols'][-5:]}")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_run_once())
