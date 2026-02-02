#!/usr/bin/env python3
"""
로컬 유니버스 시스템 테스트 (도커 제외, KIS API 제외)
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime, date

# 경로 설정
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root / "src"))

# ============================================================================
# 테스트 1: 심볼 파일 확인
# ============================================================================
def test_symbol_file():
    print("\n" + "="*70)
    print("테스트 1: 심볼 파일 확인")
    print("="*70)
    
    symbol_file = project_root / "config" / "symbols" / "kr_all_symbols.txt"
    
    print(f"\n📁 파일 경로: {symbol_file}")
    print(f"   존재 여부: {symbol_file.exists()}")
    
    if not symbol_file.exists():
        print("   ❌ 파일이 없습니다!")
        return False
    
    # 파일 읽기
    with open(symbol_file, 'r', encoding='utf-8') as f:
        symbols = [line.strip() for line in f if line.strip()]
    
    print(f"   ✅ 파일 로드 성공")
    print(f"   📊 총 심볼 수: {len(symbols)}")
    print(f"   첫 5개: {symbols[:5]}")
    print(f"   마지막 5개: {symbols[-5:]}")
    
    # 포맷 검증
    invalid = [s for s in symbols if not (len(s) == 6 and s.isdigit())]
    if invalid:
        print(f"   ⚠️  잘못된 포맷: {invalid[:5]}")
    else:
        print(f"   ✅ 모든 심볼이 6자리 숫자 형식")
    
    return True

# ============================================================================
# 테스트 2: UniverseManager 경로 계산
# ============================================================================
def test_universe_manager_paths():
    print("\n" + "="*70)
    print("테스트 2: UniverseManager 경로 계산")
    print("="*70)
    
    # UniverseManager 경로 계산 로직 재현
    universe_manager_file = project_root / "src" / "universe" / "universe_manager.py"
    
    print(f"\n📍 UniverseManager 파일: {universe_manager_file}")
    print(f"   존재 여부: {universe_manager_file.exists()}")
    
    # 경로 계산 (UniverseManager.__init__ 로직)
    base_dir = os.path.abspath(os.path.join(
        str(universe_manager_file.parent),  # /src/universe
        "..",  # /src
        "..",  # /
        "config"  # /config
    ))
    
    symbols_dir = os.path.join(base_dir, "symbols")
    txt_path = os.path.join(symbols_dir, "kr_all_symbols.txt")
    
    print(f"\n🔧 계산된 경로:")
    print(f"   base_dir: {base_dir}")
    print(f"   symbols_dir: {symbols_dir}")
    print(f"   txt_path: {txt_path}")
    
    print(f"\n✅ 경로 검증:")
    print(f"   base_dir 존재: {os.path.exists(base_dir)}")
    print(f"   symbols_dir 존재: {os.path.exists(symbols_dir)}")
    print(f"   txt_path 존재: {os.path.exists(txt_path)}")
    
    return os.path.exists(txt_path)

# ============================================================================
# 테스트 3: 유니버스 스냅샷 디렉토리
# ============================================================================
def test_universe_snapshot_dir():
    print("\n" + "="*70)
    print("테스트 3: 유니버스 스냅샷 디렉토리")
    print("="*70)
    
    universe_dir = project_root / "config" / "universe"
    
    print(f"\n📁 스냅샷 디렉토리: {universe_dir}")
    print(f"   존재 여부: {universe_dir.exists()}")
    
    if universe_dir.exists():
        snapshots = list(universe_dir.glob("*.json"))
        print(f"   ✅ 스냅샷 파일 수: {len(snapshots)}")
        if snapshots:
            print(f"   최근 파일: {snapshots[-1].name}")
    else:
        print(f"   ⚠️  디렉토리가 없으므로 생성 필요")
        universe_dir.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ 디렉토리 생성됨")
    
    return True

# ============================================================================
# 테스트 4: 유니버스 스냅샷 생성
# ============================================================================
def test_create_universe_snapshot():
    print("\n" + "="*70)
    print("테스트 4: 유니버스 스냅샷 생성")
    print("="*70)
    
    # 심볼 파일 로드
    symbol_file = project_root / "config" / "symbols" / "kr_all_symbols.txt"
    
    if not symbol_file.exists():
        print(f"   ❌ 심볼 파일이 없습니다: {symbol_file}")
        return False
    
    with open(symbol_file, 'r', encoding='utf-8') as f:
        symbols = [line.strip() for line in f if line.strip()]
    
    print(f"   ✅ 심볼 파일 로드: {len(symbols)}개")
    
    # 스냅샷 생성
    today = datetime.now().strftime('%Y%m%d')
    universe_dir = project_root / "config" / "universe"
    universe_dir.mkdir(parents=True, exist_ok=True)
    
    snapshot = {
        'metadata': {
            'date': today,
            'generated_at': datetime.now().isoformat(),
            'symbol_count': len(symbols),
            'market': 'kr_stocks',
            'source': 'kr_all_symbols.txt',
            'filter': 'All symbols (file-based)'
        },
        'symbols': symbols[:1500]  # 상위 1500개 사용 (가격 필터 생략)
    }
    
    snapshot_path = universe_dir / f"{today}_kr_stocks.json"
    
    try:
        with open(snapshot_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        
        print(f"\n   ✅ 스냅샷 생성 성공")
        print(f"   📁 파일: {snapshot_path}")
        print(f"   📊 심볼 수: {len(snapshot['symbols'])}")
        
        # 파일 검증
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        
        print(f"   ✅ 파일 검증 성공 (라운드트립)")
        print(f"   📊 로드된 심볼: {len(loaded['symbols'])}")
        
        return True
    except Exception as e:
        print(f"   ❌ 스냅샷 생성 실패: {e}")
        return False

# ============================================================================
# 테스트 5: Track A Collector 시뮬레이션
# ============================================================================
def test_track_a_collector_simulation():
    print("\n" + "="*70)
    print("테스트 5: Track A Collector 심볼 로드 시뮬레이션")
    print("="*70)
    
    # 오늘 날짜의 스냅샷 찾기
    today = datetime.now().strftime('%Y%m%d')
    universe_dir = project_root / "config" / "universe"
    snapshot_path = universe_dir / f"{today}_kr_stocks.json"
    
    print(f"\n   찾는 파일: {snapshot_path}")
    print(f"   존재 여부: {snapshot_path.exists()}")
    
    if not snapshot_path.exists():
        print(f"   ❌ 스냅샷을 찾을 수 없습니다")
        print(f"   💡 먼저 테스트 4 (스냅샷 생성)를 실행하세요")
        return False
    
    # 스냅샷 로드
    try:
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)
        
        symbols = snapshot.get('symbols', [])
        
        print(f"\n   ✅ 스냅샷 로드 성공")
        print(f"   📊 심볼 수: {len(symbols)}")
        print(f"   첫 5개: {symbols[:5]}")
        
        if len(symbols) > 100:
            print(f"   ✅ 최소 100개 심볼 요구사항 충족")
        else:
            print(f"   ❌ 최소 100개 심볼 필요 (현재: {len(symbols)})")
            return False
        
        return True
    except Exception as e:
        print(f"   ❌ 스냅샷 로드 실패: {e}")
        return False

# ============================================================================
# 메인
# ============================================================================
def main():
    print("\n" + "#"*70)
    print("# 로컬 유니버스 시스템 테스트")
    print("#"*70)
    
    results = {}
    
    # 테스트 실행
    results['test_symbol_file'] = test_symbol_file()
    results['test_universe_manager_paths'] = test_universe_manager_paths()
    results['test_universe_snapshot_dir'] = test_universe_snapshot_dir()
    results['test_create_universe_snapshot'] = test_create_universe_snapshot()
    results['test_track_a_collector_simulation'] = test_track_a_collector_simulation()
    
    # 결과 요약
    print("\n" + "="*70)
    print("📊 테스트 결과 요약")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n🎯 결과: {passed}/{total} 테스트 성공")
    
    if passed == total:
        print("\n✅ 모든 테스트 성공!")
        print("💡 다음 단계: OCI 서버에 스냅샷 배포")
    else:
        print(f"\n❌ {total - passed}개 테스트 실패")
        print("💡 위의 실패 항목을 해결한 후 다시 시도하세요")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
