#!/usr/bin/env python3
"""
한국 상장 주식 종목 수집 및 캐시 생성 스크립트

목표: 한국 증권거래소(KRX)의 모든 상장 주식 종목 수집
- KOSPI (유가증권시장): ~951개
- KOSDAQ (코스닥): ~1,825개
- KONEX (코넥스): ~112개
- 우선주 포함: 57개 (이중 계산)
- 합계: 2,888개

데이터 소스: pykrx 라이브러리
저장 위치: ./app/observer/config/symbols/kr_all_symbols.txt
"""

import asyncio
import time
from pathlib import Path
from pykrx import stock


def collect_all_stocks():
    """모든 상장 주식 종목 수집"""
    print("=" * 70)
    print("한국 상장 주식 전체 종목 수집")
    print("=" * 70)
    
    start = time.time()
    
    # 모든 마켓에서 종목 수집
    all_tickers = set()
    market_info = {}
    
    for market in ['KOSPI', 'KOSDAQ', 'KONEX']:
        try:
            tickers = stock.get_market_ticker_list(market=market)
            all_tickers.update(tickers)
            market_info[market] = len(tickers)
            print(f"✓ {market}: {len(tickers):,}개")
        except Exception as e:
            print(f"✗ {market}: Error - {e}")
            market_info[market] = 0
    
    # 정렬
    all_tickers = sorted(list(all_tickers))
    
    elapsed = time.time() - start
    
    # 데이터 분석
    digit_only = [s for s in all_tickers if s.isdigit()]
    with_alpha = [s for s in all_tickers if not s.isdigit()]
    
    print(f"\n[결과]")
    print(f"총 종목 수: {len(all_tickers):,}개")
    print(f"  - 일반주 (6자리 숫자): {len(digit_only):,}개")
    print(f"  - 우선주 (영문 포함): {len(with_alpha):,}개")
    print(f"조회 시간: {elapsed:.2f}초")
    
    return all_tickers, digit_only, with_alpha


def save_cache(symbols: list, output_path: Path = None):
    """종목 데이터를 캐시 파일에 저장"""
    if output_path is None:
        # app/observer/config/symbols/kr_all_symbols.txt에 저장
        output_path = Path(__file__).parent.parent / "config" / "symbols" / "kr_all_symbols.txt"
    
    # 디렉토리 생성
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 파일 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(symbols))
    
    file_size = output_path.stat().st_size / 1024
    
    print(f"\n[저장]")
    print(f"경로: {output_path}")
    print(f"크기: {file_size:.2f} KB")
    print(f"개수: {len(symbols):,}개")
    
    return output_path


def verify_cache(cache_path: Path):
    """캐시 파일 검증"""
    print(f"\n[검증]")
    
    with open(cache_path, 'r', encoding='utf-8') as f:
        symbols = [line.strip() for line in f if line.strip()]
    
    print(f"파일 존재: ✓")
    print(f"행 수: {len(symbols):,}")
    
    digit_only = [s for s in symbols if s.isdigit()]
    with_alpha = [s for s in symbols if not s.isdigit()]
    
    print(f"일반주: {len(digit_only):,}개")
    print(f"우선주: {len(with_alpha):,}개")
    
    # 샘플 출력
    print(f"\n[샘플 데이터]")
    print(f"첫 5개: {symbols[:5]}")
    print(f"마지막 5개: {symbols[-5:]}")
    print(f"우선주 샘플: {with_alpha[:5]}")


def main():
    """메인 함수"""
    print()
    
    # 1. 종목 수집
    symbols, digit_only, with_alpha = collect_all_stocks()
    
    # 2. 캐시 저장
    cache_path = save_cache(symbols)
    
    # 3. 캐시 검증
    verify_cache(cache_path)
    
    print("\n" + "=" * 70)
    print("✅ 완료")
    print("=" * 70)
    
    return len(symbols)


if __name__ == "__main__":
    total = main()
    print(f"\n최종 종목 수: {total:,}개")
