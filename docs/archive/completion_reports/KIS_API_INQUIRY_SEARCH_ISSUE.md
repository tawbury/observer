# ❌ KIS API 종목검색 - 문제점 분석

## 🔴 현재 문제

테스트 결과 `inquire-search` API가 **404 에러**를 반환합니다.

```
HTTP Status: 404
Content-Type: application/octet-stream
```

### 원인 분석

공식 GitHub 샘플 코드 검토 결과:

| API | 실제 용도 | 엔드포인트 |
|------|---------|----------|
| `/uapi/domestic-stock/v1/quotations/inquire-search` | ❌ **존재하지 않음** (국내주식) | N/A |
| `/uapi/overseas-price/v1/quotations/inquire-search` | ✅ **해외주식 조건검색만 지원** | 올바름 |
| `/uapi/domestic-stock/v1/quotations/psearch-title` | ✅ **사전 저장 조건 목록 조회** | 국내주식 |
| `/uapi/domestic-stock/v1/quotations/psearch-result` | ✅ **저장된 조건 검색 결과 조회** | 국내주식 |

---

## 🔍 KIS API 국내주식 조건검색의 제한사항

### 공식 문서 인용
> "HTS(efriend Plus) [0110] 조건검색에서 등록 및 서버저장한 **나의 조건** 목록을 확인할 수 있는 API"
> 
> 출처: https://github.com/koreainvestment/open-trading-api

**핵심:** KIS API는 **사전에 저장된 조건만 검색 가능**합니다. "모든 종목" 검색 API는 없습니다.

### psearch_title + psearch_result의 작동 방식

```
1. psearch_title(user_id) 
   → 사용자가 저장한 조건 목록 조회
   ← seq (조건 키값) 반환

2. psearch_result(user_id, seq)
   → 저장된 조건으로 검색 실행
   ← 검색 결과 최대 100건
```

**문제:** 직접 조건을 생성하거나 "모든 종목" 조건을 실행할 수 없습니다.

---

## ✅ 공식 권장 해결방법

KIS 공식 문서에서 **종목정보파일** 다운로드를 권장합니다:

- **다운로드**: https://apiportal.koreainvestment.com/apiservice-category
- **파일명**: 종목정보파일 (일일 갱신)
- **형식**: CSV/Excel
- **내용**: 전체 2894개 종목 정보
- **API 호출 불필요**: 매매 가능 종목만 필터링

### 공식 API 포털 문서
```
[국내주식] 종목정보 > 종목정보파일
- 매매 및 시세조회 가능한 전체 종목 리스트
- CSV 형식으로 매일 갱신
```

---

## 🎯 해결책

### Option 1: 종목정보파일 다운로드 (공식 권장) ⭐

```python
import urllib.request
import pandas as pd

# 공식 종목정보파일 다운로드
url = "https://apiportal.koreainvestment.com/stock-info"  # or direct link
df = pd.read_csv(url)
symbols = df['종목코드'].tolist()  # 2894개
```

**장점:**
- ✅ API 호출 불필요 (레이트 제한 없음)
- ✅ 공식 권장 방식
- ✅ 모든 종목 한번에 획득
- ✅ 신뢰성 높음

**단점:**
- 파일 포맷 파싱 필요

### Option 2: 국내주식 기본시세 API 활용

사실 개별 종목 시세 API를 사용해서 종목을 수집하는 것도 가능합니다:

```python
# 공식 API로 제공되는 데이터
# /uapi/domestic-stock/v1/quotations/inquire-price (개별 종목)

# 하지만 2894개를 각각 호출하려면:
# - 시간: 약 145초 (2894 / 20 req/sec)
# - API 할당: 2894 / 1000 = 약 3000+ 요청
```

**문제:** 시간과 API 할당이 비효율적

---

## 📊 최종 결론

| 방법 | 속도 | 신뢰성 | API 사용 | 권장도 |
|------|------|--------|---------|------|
| **종목정보파일 다운로드** | ⭐⭐⭐⭐⭐ 1초 | ⭐⭐⭐⭐⭐ 공식 | ❌ 없음 | **⭐⭐⭐⭐⭐** |
| 조건검색 API (국내) | ❌ 불가능 | ⭐⭐ 제한적 | ✅ 필요 | ❌ 미권장 |
| 개별 종목 API | ⭐ 매우 느림 | ⭐⭐⭐⭐ 안정 | ✅ 많음 | ⚠️ 비효율 |

---

## 🔧 다음 행동

1. ✅ **공식 종목정보파일 다운로드** 구현
2. ✅ 2894개 종목 자동 추출
3. ✅ `kr_all_symbols.txt` 업데이트
4. ✅ 로컬 테스트 (API 호출 불필요)

---

## 📝 참고 자료

**공식 KIS API GitHub:**
https://github.com/koreainvestment/open-trading-api

**관련 API 코드:**
- `examples_llm/domestic_stock/psearch_title/` - 조건 목록 조회
- `examples_llm/domestic_stock/psearch_result/` - 조건 검색 실행
- `stock_info/` - 종목정보파일 참고 데이터

---

**작성일**: 2026-01-27
**상태**: ❌ inquire-search API 불가능 → ✅ 공식 방법으로 전환 필요
