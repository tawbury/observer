#!/usr/bin/env python3
"""
트리거 엔진 디버깅 테스트

트리거 엔진 내부 동작 방식 상세 분석
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

_project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_project_root / "app" / "observer" / "src"))

print('=== 트리거 엔진 디버깅 테스트 ===')

try:
    from trigger.trigger_engine import TriggerEngine, TriggerConfig, PriceSnapshot
    
    print('✅ 모듈 임포트 성공')
    
    # 트리거 엔진 설정 확인
    config = TriggerConfig()
    print(f'트리거 엔진 설정:')
    print(f'  volume_surge_ratio: {config.volume_surge_ratio}')
    print(f'  volume_surge_priority: {config.volume_surge_priority}')
    print(f'  volatility_spike_threshold: {config.volatility_spike_threshold}')
    print(f'  volatility_spike_priority: {config.volatility_spike_priority}')
    print(f'  max_candidates: {config.max_candidates}')
    print(f'  min_priority_score: {config.min_priority_score}')
    print(f'  dedup_window_seconds: {config.dedup_window_seconds}')
    
    # 트리거 엔진 생성
    trigger_engine = TriggerEngine()
    print(f'✅ 트리거 엔진 생성 성공')
    
    # 히스토리 데이터 생성
    def create_test_snapshots():
        """테스트용 스냅샷 생성"""
        snapshots = []
        base_time = datetime.now(ZoneInfo('Asia/Seoul'))
        
        # 10분 동안의 데이터 생성 (1분 간격)
        for i in range(10):
            timestamp = base_time - timedelta(minutes=10-i)
            
            # 평소 거래량: 100,000
            # 급등 시점: 1,000,000 (10배)
            if i >= 5:  # 마지막 5분간 급등
                volume = 1000000
                price = 50000
            else:
                volume = 100000
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
    
    # 테스트 데이터 생성
    test_snapshots = create_test_snapshots()
    print(f'\n✅ 테스트 스냅샷 생성: {len(test_snapshots)} 개')
    
    # 스냅샷 상세 정보 출력
    print('\n=== 스냅샷 상세 정보 ===')
    for i, snapshot in enumerate(test_snapshots):
        print(f'{i+1:2d}. {snapshot.timestamp.strftime("%H:%M:%S")} - 거래량: {snapshot.volume:,}, 가격: {snapshot.price:,}')
    
    # 트리거 엔진 내부 상태 확인
    print('\n=== 트리거 엔진 내부 상태 ===')
    print(f'히스토리 버퍼 크기: {len(trigger_engine._history)}')
    print(f'히스토리 윈도우: {trigger_engine._history_window}')
    print(f'최근 트리거: {len(trigger_engine._recent_triggers)}')
    
    # 점진적 업데이트 및 상태 확인
    print('\n=== 점진적 업데이트 및 상태 확인 ===')
    
    for i, snapshot in enumerate(test_snapshots):
        print(f'\n시점 {i+1}: {snapshot.timestamp.strftime("%H:%M:%S")}')
        print(f'  입력 거래량: {snapshot.volume:,}')
        
        # 업데이트 전 상태
        symbol_history = trigger_engine._history.get(snapshot.symbol)
        if symbol_history:
            print(f'  업데이트 전 히스토리: {len(symbol_history)} 개')
            if len(symbol_history) > 0:
                volumes = [s.volume for s in symbol_history]
                avg_volume = sum(volumes) / len(volumes)
                print(f'  평균 거래량: {avg_volume:,.0f}')
                print(f'  볼륨 급등 기준: {avg_volume * config.volume_surge_ratio:,.0f}')
        else:
            print(f'  업데이트 전 히스토리: 없음')
        
        # 업데이트 실행
        candidates = trigger_engine.update([snapshot])
        
        # 업데이트 후 상태
        symbol_history = trigger_engine._history.get(snapshot.symbol)
        if symbol_history:
            print(f'  업데이트 후 히스토리: {len(symbol_history)} 개')
            if len(symbol_history) > 0:
                volumes = [s.volume for s in symbol_history]
                avg_volume = sum(volumes) / len(volumes)
                print(f'  평균 거래량: {avg_volume:,.0f}')
                print(f'  볼륨 급등 기준: {avg_volume * config.volume_surge_ratio:,.0f}')
                
                # 수동 계산
                if snapshot.volume > avg_volume * config.volume_surge_ratio:
                    surge_ratio = snapshot.volume / avg_volume
                    print(f'  ✅ 볼륨 급등 감지됨! (비율: {surge_ratio:.2f})')
                else:
                    print(f'  ❌ 볼륨 급등 미감지 (비율: {snapshot.volume / avg_volume:.2f})')
        
        print(f'  감지된 트리거: {len(candidates)} 개')
        for candidate in candidates:
            print(f'    ✅ {candidate.trigger_type} - 우선순: {candidate.priority_score:.2f}')
    
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
    
    print('\n✅ 트리거 엔진 디버깅 완료')
    
except Exception as e:
    print(f'❌ 테스트 오류: {e}')
    import traceback
    traceback.print_exc()

print('=== 트리거 엔진 디버깅 완료 ===')
