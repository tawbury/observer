#!/usr/bin/env python3
"""
트리거 엔진 극한 테스트

더 극적인 급등 데이터로 트리거 감지 테스트
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# 경로 설정
sys.path.insert(0, 'src')

print('=== 트리거 엔진 극한 테스트 ===')

try:
    from trigger.trigger_engine import TriggerEngine, TriggerConfig, PriceSnapshot
    
    print('✅ 모듈 임포트 성공')
    
    # 더 낮은 기준으로 트리거 엔진 생성
    config = TriggerConfig(volume_surge_ratio=2.0)  # 2배로 낮춤
    trigger_engine = TriggerEngine(config)
    
    print(f'트리거 엔진 설정 (수정됨):')
    print(f'  volume_surge_ratio: {config.volume_surge_ratio} (기존: 5.0)')
    print(f'  volume_surge_priority: {config.volume_surge_priority}')
    
    # 극한 급등 데이터 생성
    def create_extreme_snapshots():
        """극한 급등 데이터 생성"""
        snapshots = []
        base_time = datetime.now(ZoneInfo('Asia/Seoul'))
        
        # 10분 동안의 데이터 생성
        for i in range(10):
            timestamp = base_time - timedelta(minutes=10-i)
            
            # 평소 거래량: 10,000
            # 극한 급등: 1,000,000 (100배)
            if i >= 5:  # 마지막 5분간 극한 급등
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
                open=50000,
                high=50050,
                low=49950
            )
            snapshots.append(snapshot)
        
        return snapshots
    
    # 극한 데이터 생성
    extreme_snapshots = create_extreme_snapshots()
    print(f'✅ 극한 스냅샷 생성: {len(extreme_snapshots)} 개')
    
    # 스냅샷 상세 정보 출력
    print('\n=== 극한 스냅샷 상세 정보 ===')
    for i, snapshot in enumerate(extreme_snapshots):
        print(f'{i+1:2d}. {snapshot.timestamp.strftime("%H:%M:%S")} - 거래량: {snapshot.volume:,}, 가격: {snapshot.price:,}')
    
    # 점진적 업데이트
    print('\n=== 점진적 업데이트 테스트 ===')
    
    for i, snapshot in enumerate(extreme_snapshots):
        print(f'\n시점 {i+1}: {snapshot.timestamp.strftime("%H:%M:%S")}')
        print(f'  입력 거래량: {snapshot.volume:,}')
        
        # 업데이트 전 상태
        symbol_history = trigger_engine._history.get(snapshot.symbol)
        if symbol_history:
            volumes = [s.volume for s in symbol_history]
            avg_volume = sum(volumes) / len(volumes)
            print(f'  업데이트 전 평균 거래량: {avg_volume:,.0f}')
            print(f'  급등 기준: {avg_volume * config.volume_surge_ratio:,.0f}')
        
        # 업데이트 실행
        candidates = trigger_engine.update([snapshot])
        
        # 업데이트 후 상태
        symbol_history = trigger_engine._history.get(snapshot.symbol)
        if symbol_history:
            volumes = [s.volume for s in symbol_history]
            avg_volume = sum(volumes) / len(volumes)
            print(f'  업데이트 후 평균 거래량: {avg_volume:,.0f}')
            print(f'  급등 기준: {avg_volume * config.volume_surge_ratio:,.0f}')
            
            # 수동 계산
            if snapshot.volume > avg_volume * config.volume_surge_ratio:
                surge_ratio = snapshot.volume / avg_volume
                print(f'  ✅ 볼륨 급등 감지됨! (비율: {surge_ratio:.2f})')
            else:
                print(f'  ❌ 볼륨 급등 미감지 (비율: {snapshot.volume / avg_volume:.2f})')
        
        print(f'  감지된 트리거: {len(candidates)} 개')
        for candidate in candidates:
            print(f'    ✅ {candidate.trigger_type} - 우선순: {candidate.priority_score:.2f}')
            print(f'       상세: {candidate.details}')
    
    # 최종 상태 확인
    print('\n=== 최종 상태 확인 ===')
    print(f'히스토리 버퍼 크기: {len(trigger_engine._history)}')
    
    for symbol, history in trigger_engine._history.items():
        print(f'  {symbol}: {len(history)} 개 스냅샷')
        if len(history) > 0:
            volumes = [s.volume for s in history]
            avg_volume = sum(volumes) / len(volumes)
            max_volume = max(volumes)
            print(f'    평균 거래량: {avg_volume:,.0f}')
            print(f'    최대 거래량: {max_volume:,}')
            print(f'    급등 비율: {max_volume / avg_volume:.2f}')
    
    print(f'최근 트리거: {len(trigger_engine._recent_triggers)}')
    for symbol, trigger_time in trigger_engine._recent_triggers.items():
        print(f'  {symbol}: {trigger_time.strftime("%H:%M:%S")}')
    
    # 변동성 스파이크 테스트
    print('\n=== 변동성 스파이크 테스트 ===')
    
    # 변동성 데이터 생성
    volatility_snapshots = []
    base_time = datetime.now(ZoneInfo('Asia/Seoul'))
    
    for i in range(10):
        timestamp = base_time - timedelta(minutes=10-i)
        
        # 평소 가격: 50,000
        # 스파이크: 52,500 (5% 상승)
        if i >= 5:
            price = 52500
        else:
            price = 50000
        
        snapshot = PriceSnapshot(
            symbol='000660',
            timestamp=timestamp,
            price=price,
            volume=50000,
            open=50000,
            high=price + 100,
            low=price - 100
        )
        volatility_snapshots.append(snapshot)
    
    print(f'변동성 스냅샷 생성: {len(volatility_snapshots)} 개')
    
    # 변동성 트리거 테스트
    for i, snapshot in enumerate(volatility_snapshots):
        candidates = trigger_engine.update([snapshot])
        
        if candidates:
            print(f'시점 {i+1}: {snapshot.symbol} - {len(candidates)} 개 트리거 감지')
            for candidate in candidates:
                print(f'  ✅ {candidate.trigger_type} - 우선순: {candidate.priority_score:.2f}')
    
    print('\n✅ 트리거 엔진 극한 테스트 완료')
    
except Exception as e:
    print(f'❌ 테스트 오류: {e}')
    import traceback
    traceback.print_exc()

print('=== 트리거 엔진 극한 테스트 완료 ===')
