# Track B 강제 테스트 가이드 (비거래 시간 테스트)

## 개요

Track B (WebSocket 실시간 Tick 수집)를 **비거래 시간**에 테스트하기 위한 3가지 방법:

### 문제
- KIS WebSocket은 **거래 시간에만** 실시간 데이터 제공
- 현재 시간: 비거래 시간 (오후 4시 이후 또는 주말)
- 다음 거래 시간: 월요일 오전 9시 (약 48시간 후)

### 해결책
**Mock 테스트를 통해 즉시 강제 테스트 가능**

---

## 방법 1: 간단한 강제 테스트 (권장 ⭐)

Track B의 핵심 컴포넌트를 즉시 테스트합니다.

```bash
# Terminal에서 실행
cd d:\development\prj_obs
python test/test_track_b_simple.py
```

### 테스트 내용
1. **TriggerEngine Direct Test**
   - Volatility Spike 감지 (5% 가격 변동) ✅
   - Volume Surge 감지 (5배 거래량) ⚠️ (10분 평균 필요)

2. **SlotManager Direct Test**
   - 5개 슬롯에 6개 후보 할당
   - 첫 5개는 할당, 6번째는 Overflow
   - 우선순위 기반 교체 정책 검증

### 기대 결과
```
✅ PASS: Volatility spike detected
✅ PASS: Slot allocation working correctly
```

---

## 방법 2: 전체 통합 테스트

Mock Track A 데이터 생성 → TriggerEngine → SlotManager → Logging

```bash
python test/test_track_b_mock.py --mode=full
```

### 옵션
- `--mode=full` : 전체 테스트 (triggers + slots + integration)
- `--mode=triggers` : TriggerEngine만 테스트
- `--mode=slots` : SlotManager만 테스트

### 생성 파일
- `test/test_data/mock_swing.jsonl` - Mock Track A 로그 (150개 snapshot)
- `test/test_data/mock_scalp.jsonl` - Mock Scalp 로그 (실시간 tick)

---

## 방법 3: 실시간 통합 테스트 (장시간 실행)

Mock Track A 스냅샷을 지속적으로 생성하며 Track B 파이프라인을 테스트합니다.

```bash
python test/test_track_b_integration.py --duration=60 --mode=full
```

### 옵션
- `--duration=60` : 60초 동안 테스트 (기본값)
- `--mode=full` : WebSocket 구독 포함 (기본값)
- `--mode=triggers_only` : Trigger 감지만 테스트

---

## 무엇을 테스트할 수 있나?

### ✅ 테스트 가능
1. **Trigger Detection** (TriggerEngine)
   - Volatility Spike: 5% 가격 변동
   - Volume Surge: 5배 거래량 증가
   - Trade Velocity: 거래 속도 (선택사항)

2. **Slot Management** (SlotManager)
   - 41개 슬롯 할당/해제
   - 우선순위 기반 교체 (2분 Dwell Time)
   - Overflow 로깅 (JSONL)

3. **Logging**
   - Scalp 로그 (실시간 Tick)
   - Overflow 로그 (거부된 후보)
   - Statistics (할당/교체/거부 카운트)

### ❌ 테스트 불가능
- 실시간 KIS WebSocket 데이터 (거래 시간 필요)
- 실제 2Hz Tick 수집 (거래 시간 필요)
- 네트워크 연결 안정성 (이전 Fix 참고)

---

## 코드 구조

### TriggerEngine (Track A → Candidates)
```
TriggerEngine.update(snapshots: List[PriceSnapshot]) → List[TriggerCandidate]

입력: 가격/거래량 스냅샷
- symbol: "005930"
- timestamp: datetime
- price: 70000
- volume: 500000

출력: 트리거된 후보
- symbol: "005930"
- trigger_type: "volatility_spike"
- priority_score: 0.95
```

### SlotManager (Candidates → Slots)
```
SlotManager.assign_slot(candidate: SlotCandidate) → AllocationResult

입력: TriggerEngine의 후보
- symbol, trigger_type, priority_score, detected_at

출력: 할당 결과
- success: True/False
- slot_id: 0-40 (할당된 슬롯)
- overflow: 거부됨 (all slots occupied)
- replaced_symbol: 교체된 기존 심볼
```

---

## 실행 예시

### 1. 간단한 테스트 실행
```bash
python test/test_track_b_simple.py
```

**출력:**
```
╔════════════════════════════════════════════════════════╗
║ TRACK B FORCE-TEST SUITE (Without Market Hours)       ║
╚════════════════════════════════════════════════════════╝

TEST 1: TriggerEngine Direct Testing
✅ PASS: Volatility spike detected
✅ PASS: Slot allocation working correctly

TEST 2: SlotManager Direct Testing
✅ Expected allocated: 5, Got: 5
✅ Expected overflow: 1, Got: 1
✅ PASS: Slot allocation working correctly

✅ ALL TESTS COMPLETED
```

### 2. 전체 통합 테스트
```bash
python test/test_track_b_mock.py --mode=full
```

**출력 요약:**
```
TEST: TriggerEngine Trigger Detection
- Generated 150 snapshots
- Expected triggers: ~15
- Actual triggers: (varies by config)

TEST: SlotManager Allocation & Replacement
- Allocated slots: 5
- Available slots: 0
- Total overflows: 1

TEST: Integration - Trigger → Slot Manager → Logging
- Step 1: TriggerEngine detected X candidates
- Step 2: SlotManager allocated Y symbols to slots
- Step 3: Logged Z records to mock_scalp.jsonl
```

---

## 다음 단계 (거래 시간)

### 월요일 오전 9시 (거래 시작)
1. 실제 KIS WebSocket 연결
2. 실제 Track A 데이터 수집
3. 실제 Trigger 감지
4. 실제 WebSocket 구독
5. 실제 2Hz Tick 수집 및 Scalp 로깅

### 현재 준비 상태
- ✅ Code: TriggerEngine 및 SlotManager 구현 완료
- ✅ Compliance: KIS API 정준성 검증 완료
- ✅ Docker: Image 빌드 완료
- ✅ Tests: Mock 테스트 구현 완료
- ⏳ Real Data: 거래 시간 대기

---

## Troubleshooting

### Q: Python 인코딩 오류
```
UnicodeEncodeError: 'cp949' codec can't encode character
```

**해결:**
```bash
$env:PYTHONIOENCODING='utf-8'
python test/test_track_b_simple.py
```

### Q: SlotCandidate 오류
```
SlotCandidate.__init__() missing 1 required positional argument: 'detected_at'
```

**해결:** `detected_at=datetime.now(timezone.utc)` 필드 추가

### Q: TriggerEngine이 trigger를 감지하지 못함
**원인:** Mock 데이터의 가격/거래량 변화가 충분하지 않음

**해결:** 
- Volatility: 최소 5% 가격 변동 필요
- Volume: 최소 5배 거래량 증가 + 10분 평균 계산 필요

---

## 파일 위치

| 파일 | 용도 |
|------|------|
| `test/test_track_b_simple.py` | 간단한 강제 테스트 (권장) |
| `test/test_track_b_mock.py` | 전체 통합 테스트 |
| `test/test_track_b_integration.py` | 실시간 통합 테스트 |
| `test/test_websocket_mock.py` | Mock WebSocket Provider |
| `app/observer/src/trigger/trigger_engine.py` | TriggerEngine 구현 |
| `app/observer/src/slot/slot_manager.py` | SlotManager 구현 |

---

## KIS API Compliance 검증

이전에 식별된 모든 문제가 해결되었습니다:

✅ Approval Key 인증  
✅ WebSocket 엔드포인트 선택 (Virtual:31000, Real:21000)  
✅ Unsubscribe TR_TYPE ("0")  
✅ Pipe-delimited 메시지 파싱 (H0STCNT0)  
✅ PINGPONG Keep-Alive  
✅ Callback 등록 순서  
✅ Scalp 로그 필드 완성  

자세한 내용: [docs/TRACK_B_KIS_API_COMPLIANCE_REVIEW.md](../../docs/TRACK_B_KIS_API_COMPLIANCE_REVIEW.md)

---

## 요약

| 항목 | 상태 | 명령어 |
|------|------|--------|
| 즉시 테스트 | ✅ Ready | `python test/test_track_b_simple.py` |
| 전체 통합 | ✅ Ready | `python test/test_track_b_mock.py --mode=full` |
| 실시간 통합 | ✅ Ready | `python test/test_track_b_integration.py --duration=60` |
| 거래 시간 테스트 | ⏳ Waiting | 월요일 오전 9시 이후 |
