# 독립 Track B (Deprecated)

독립 Track B 프로토타입 문서는 더 이상 유지하지 않습니다. 중복 코드(independent_track_b_collector.py, independent_track_b_scanner.py, track_b_independent.py)와 관련 실험용 테스트는 2026-01-27에 제거되었습니다.

현재 Track B는 src/collector/track_b_collector.py 하나로 운용하며, Track A 의존성 없이 부트스트랩 심볼 기반으로 동작합니다. 실시간 체결 로그 수집이 필요하면 src/collector/collect_live_scalp.py CLI를 사용하세요.

유효한 테스트는 tests/test_track_b_standalone.py입니다.
