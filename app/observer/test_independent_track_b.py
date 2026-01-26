"""
독립 Track B 스캐너 테스트

KIS 공식 API 기반 독립적인 실시간 스캐닝 테스트
"""
import asyncio
import json
import logging
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 경로 설정
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from collector.track_b_independent import TrackBIndependent, TrackBIndependentConfig
from provider.kis.kis_auth_enhanced import KISAuthEnhanced


async def test_independent_track_b():
    """독립 Track B 테스트"""
    print("=== 독립 Track B 스캐너 테스트 ===")
    
    # 설정
    config = TrackBIndependentConfig()
    print(f"설정: market={config.market}, max_slots={config.max_slots}")
    print(f"거래 시간: {config.trading_start} - {config.trading_end}")
    
    # 인증 (실제 환경에서는 환경 변수에서 읽어오기)
    app_key = os.getenv("KIS_APP_KEY")
    app_secret = os.getenv("KIS_APP_SECRET")
    
    if not app_key or not app_secret:
        print("❌ KIS API 키가 설정되지 않았습니다.")
        print("환경 변수 KIS_APP_KEY, KIS_APP_SECRET를 설정해주세요.")
        return
    
    # 독립 Track B 생성
    try:
        track_b = TrackBIndependent(config.market, config.max_slots)
        print("✅ TrackBIndependent 인스턴스 생성 성공")
        
        # 에러 콜백 설정
        def on_error(error_msg):
            print(f"❌ Track B 에러: {error_msg}")
        
        track_b.set_error_callback(on_error)
        
        # 테스트용 가짜 데이터 생성
        await create_test_data()
        
        # 스캐너 시작
        print("\n=== 스캐너 시작 ===")
        scanner_task = asyncio.create_task(track_b.start())
        
        # 30초 동안 실행
        await asyncio.sleep(30)
        
        # 통계 정보 출력
        stats = track_b.get_stats()
        print(f"\n=== 통계 정보 ===")
        print(f"활성 슬롯: {stats['active_slots']}")
        print(f"구독 종목: {stats['subscribed_symbols']}")
        print(f"Universe 크기: {stats['universe_size']}")
        print(f"실행 상태: {stats['running']}")
        
        # 중지
        print("\n=== 스캐너 중지 ===")
        await track_b.stop()
        scanner_task.cancel()
        
        print("✅ 테스트 완료")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


async def create_test_data():
    """테스트용 데이터 생성"""
    try:
        # 테스트용 Universe 파일 생성
        test_universe = {
            "symbols": [
                "005930",  # 삼성전자
                "000660",  # SK하이닉스
                "035420",  # NAVER
                "051910",  # LG화학
                "068270",  # 셀트리온
                "207940",  # 삼성바이오로직스
                "247540",  # 에코프로
                "251270",  # 제일호텔
                "323410",  # 케이카
                "329160",  # 하이브
                "347860",  # 셀레론
                "352820",  # 하이닉스
                "373220",  # LG에너지솔루션
                "416670",  # 대한항공
                "437330",  # 한화에어로스페이스
            ]
        }
        
        # Universe 디렉토리 생성
        universe_dir = Path("config/universe")
        universe_dir.mkdir(parents=True, exist_ok=True)
        
        # 오늘 날짜 Universe 파일 생성
        today = datetime.now(ZoneInfo("Asia/Seoul"))
        universe_file = universe_dir / f"{today.strftime('%Y%m%d')}_kr_stocks.json"
        
        with open(universe_file, 'w', encoding='utf-8') as f:
            json.dump(test_universe, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 테스트 Universe 생성: {universe_file}")
        print(f"종목 수: {len(test_universe['symbols'])}")
        
    except Exception as e:
        print(f"❌ 테스트 데이터 생성 실패: {e}")


def test_event_detectors():
    """이벤트 감지기 테스트"""
    print("\n=== 이벤트 감지기 테스트 ===")
    
    from collector.independent_track_b_scanner import VolumeSurgeDetector, VolatilityDetector
    
    # 거래량 급등 감지기 테스트
    volume_detector = VolumeSurgeDetector(surge_threshold=3.0, window_seconds=60)
    
    # 테스트 데이터 생성
    test_symbol = "005930"
    test_timestamp = datetime.now(ZoneInfo("Asia/Seoul"))
    
    # 정상 거래량 데이터
    for i in range(60):
        volume = 10000 + (i * 100)  # 점진 증가
        event = volume_detector.detect(test_symbol, volume, test_timestamp)
        if event:
            print(f"✅ Volume surge detected: {event.symbol} (ratio: {event.details['surge_ratio']:.2f})")
    
    # 급등 거래량 데이터
    surge_volume = 100000  # 평균보다 10배 높은 거래량
    event = volume_detector.detect(test_symbol, surge_volume, test_timestamp)
    if event:
        print(f"✅ Volume surge detected: {event.symbol} (ratio: {event.details['surge_ratio']:.2f})")
    
    # 변동성 감지기 테스트
    volatility_detector = VolatilityDetector(volatility_threshold=0.05, window_seconds=60)
    
    # 정상 가격 변화 데이터
    for i in range(60):
        price = 50000 + (i * 10)  # 점진 증가
        event = volatility_detector.detect(test_symbol, price, test_timestamp)
        if event:
            print(f"✅ Volatility spike detected: {event.symbol} (change: {event.details['price_change']:.2%})")
    
    # 급등 가격 변화 데이터
    spike_price = 55000  # 10% 변화
    event = volatility_detector.detect(test_symbol, spike_price, test_timestamp)
    if event:
        print(f"✅ Volatility spike detected: {event.symbol} (change: {event.details['price_change']:.2%})")
    
    print("✅ 이벤트 감지기 테스트 완료")


def test_slot_manager():
    """슬롯 관리자 테스트"""
    print("\n=== 슬롯 관리자 테스트 ===")
    
    from collector.independent_track_b_scanner import DynamicSlotManager, VolumeSurgeEvent, VolatilitySpikeEvent
    
    slot_manager = DynamicSlotManager(max_slots=5)
    test_timestamp = datetime.now(ZoneInfo("Asia/Seoul"))
    
    # 테스트 이벤트 생성
    events = [
        VolumeSurgeEvent("005930", test_timestamp, 100000, 10000, 10.0),
        VolumeSurgeEvent("000660", test_timestamp, 80000, 8000, 10.0),
        VolatilitySpikeEvent("035420", test_timestamp, 0.08, 50000),
        VolumeSurgeEvent("051910", test_timestamp, 60000, 6000, 10.0),
        VolatilitySpikeEvent("207940", test_timestamp, 0.06, 40000),
        VolumeSurgeEvent("247540", test_timestamp, 120000, 12000, 10.0),
        VolumeSurgeEvent("251270", test_timestamp, 90000, 9000, 10.0),
    ]
    
    # 슬롯 할당 테스트
    for event in events:
        slot_id = slot_manager.allocate_slot(event)
        if slot_id:
            print(f"✅ Slot {slot_id}: {event.symbol} (priority={event.priority_score:.2f})")
        else:
            print(f"❌ No slot for {event.symbol} (priority={event.priority_score:.2f})")
    
    # 통계 정보 출력
    print(f"\n=== 슬롯 통계 ===")
    stats = slot_manager.get_stats()
    print(f"활성 슬롯: {stats['active_slots']}")
    print(f"구독 종목: {stats['subscribed_symbols']}")
    print(f"Universe 크기: {stats['universe_size']}")
    print(f"실행 상태: {stats['running']}")
    
    # 활성 종목 목록
    active_symbols = slot_manager.get_active_symbols()
    print(f"활성 종목: {list(active_symbols)}")
    
    print("✅ 슬롯 관리자 테스트 완료")


if __name__ == "__main__":
    # 테스트 실행
    test_event_detectors()
    test_slot_manager()
    
    # 메인 테스트 (실제 API 호출)
    print("\n=== 메인 테스트 시작 ===")
    asyncio.run(test_independent_track_b())
