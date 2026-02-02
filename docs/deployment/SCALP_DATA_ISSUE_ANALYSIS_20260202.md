# 스켈프 데이터 수집 부족 원인 분석 및 해결 방안

**분석 일시**: 2026-02-02  
**서버**: oracle-obs-vm-01 (134.185.117.22)  
**배포 이미지**: ghcr.io/tawbury/observer:build-20260130-143831  
**분석자**: AI Assistant

---

## 1. 문제 현황

### 1.1 증상
- **기대**: 스켈프 데이터 1시간당 10~15MB
- **실제 (2/2 09~11시)**: 약 48KB (3시간 합계)
  - `20260202_09.jsonl`: 12KB (30 lines)
  - `20260202_10.jsonl`: 20KB (49 lines)
  - `20260202_11.jsonl`: 16KB (37 lines)
- **정상 참고**: `20260130_13.jsonl` ≈ 9.1MB (23,661 lines)

### 1.2 비교 분석
| 날짜/시간 | 파일 크기 | 라인 수 | 시간당 예상 |
|-----------|-----------|---------|-------------|
| 2026-01-30 13시 | 9.1 MB | 23,661 | 정상 |
| 2026-01-30 14시 | 19.3 MB | 50,287 | 정상 |
| 2026-02-02 09시 | 12 KB | 30 | **비정상** |
| 2026-02-02 10시 | 20 KB | 49 | **비정상** |
| 2026-02-02 11시 | 16 KB | 37 | **비정상** |

**데이터 감소율**: 약 **99.8%** (정상 대비 1/500 수준)

---

## 2. 서버 실태 조사 결과

### 2.1 컨테이너 및 배포 정보
```bash
# 실행 중인 컨테이너
NAMES               IMAGE                                            STATUS
observer            ghcr.io/tawbury/observer:build-20260130-143831   Up 4 hours (healthy)
observer-postgres   postgres:15-alpine                               Up 4 hours (healthy)

# 컨테이너 사용자
uid=999(observer) gid=999(observer) groups=999(observer)

# 배포 이미지 생성 시간
2026-01-30T03:59:25.338765607Z (1월 30일 빌드)
```

### 2.2 디렉터리 권한 상태

#### 스윙 디렉터리 (`~/observer/config/swing/`)
```bash
drwxrwxrwx 2 lxd       999     4096 Feb  2 02:26 .
-rw-r--r-- 1 lxd       999 10065559 Jan 30 06:28 20260130.jsonl
-rw-r--r-- 1 lxd       999 43571712 Jan 31 06:30 20260131.jsonl
-rw-r--r-- 1 lxd       999 31095680 Feb  1 06:26 20260201.jsonl
-rw-rw-r-- 1 lxd       999  8315564 Feb  2 03:51 20260202.jsonl  ← 현재 쓰기 중
```

**상태**: 
- 디렉터리: `lxd:999` (777 권한)
- 파일: `lxd:999` (644/664 권한)
- **Track A는 정상 동작 중** (12:51 최종 업데이트 확인)

#### 스켈프 디렉터리 (`~/observer/config/scalp/`)
```bash
drwxrwxrwx 2 lxd       999     4096 Feb  2 02:00 .
-rw-r--r-- 1 lxd       999  9516165 Jan 30 04:59 20260130_13.jsonl  ← 정상
-rw-r--r-- 1 lxd       999 20222213 Jan 30 05:59 20260130_14.jsonl  ← 정상
-rw-r--r-- 1 lxd       999    97289 Jan 30 06:00 20260130_15.jsonl
-rw-r--r-- 1 lxd       999    11744 Feb  2 00:55 20260202_09.jsonl  ← 비정상
-rw-r--r-- 1 lxd       999    19260 Feb  2 01:59 20260202_10.jsonl  ← 비정상
-rw-r--r-- 1 lxd       999    14627 Feb  2 02:47 20260202_11.jsonl  ← 비정상
```

**상태**: 
- 디렉터리: `lxd:999` (777 권한)
- 파일: `lxd:999` (644 권한)
- **권한 문제 없음** (uid 999가 쓰기 가능)

### 2.3 Track B 동작 상태

#### 환경 변수
```bash
TRACK_A_ENABLED=true
TRACK_B_ENABLED=true
```

#### Track B 로그 분석
```
2026-02-02 09:12:25 | Track B Collector will be enabled
2026-02-02 09:12:25 | TriggerEngine initialized
2026-02-02 09:12:27 | WebSocket provider started

2026-02-02 09:30:27 | 📡 Subscribed: 005930 (slot 0)
2026-02-02 09:30:27 | 📡 Subscribed: 000660 (slot 1)
2026-02-02 09:30:27 | 📡 Subscribed: 373220 (slot 2)
2026-02-02 09:30:27 | 📡 Subscribed: 051910 (slot 3)
2026-02-02 09:30:27 | 📡 Subscribed: 068270 (slot 4)
2026-02-02 09:30:27 | 📡 Subscribed: 035720 (slot 5)

2026-02-02 12:53:59 | 🎯 Generated 6 bootstrap candidates (Track A independent mode)
2026-02-02 12:53:59 | ✅ Slot 0-5 할당 완료
```

**핵심 발견**:
- Track B는 **부트스트랩 독립 모드**로 정상 동작 중
- 6개 종목 (005930, 000660, 373220, 051910, 068270, 035720) 구독 완료
- WebSocket 연결 정상 (PINGPONG 수신 확인)

#### WebSocket 수신 통계
```bash
# WS 수신 메시지 총 개수
97,329 건 (09:12 ~ 12:54 기준)

# Price update 콜백 호출 로그
4건만 기록 (50번마다 1회 로그 정책)
→ 실제 콜백 호출: 약 200건 추정

# 스켈프 저장 로그 ("[저장]")
1건만 기록 (최근 5000줄 기준)
```

---

## 3. 근본 원인 분석

### 3.1 초기 가정 vs 실제 상황

| 항목 | 초기 분석 문서 가정 | 실제 서버 상황 | 결론 |
|------|---------------------|----------------|------|
| Track B 아키텍처 | 스윙 JSONL 의존 | **부트스트랩 독립** | ❌ 가정 불일치 |
| Track A 권한 | Permission denied | **정상 동작** | ❌ 가정 불일치 |
| 스켈프 권한 | 1001:1001, 0644 | **lxd:999, 644** | ❌ 가정 불일치 |
| WebSocket 구독 | 트리거 0 → 구독 없음 | **6종목 구독 완료** | ❌ 가정 불일치 |

### 3.2 실제 문제: WebSocket 데이터 수신 → 파일 저장 단절

#### 증거 1: WebSocket은 정상 수신 중
- WS 수신 메시지: **97,329건** (3시간 45분)
- 시간당 약 26,000건 수신
- PINGPONG 정상 응답

#### 증거 2: 콜백은 호출되지만 저장은 안 됨
- Price update 콜백 호출: 약 **200건** (추정)
- 스켈프 파일 저장: **116 라인** (실제)
- **저장 로그 "[저장]"**: 1건만 발견

#### 증거 3: 스켈프 파일에는 부트스트랩 외 종목 다수
```json
// 20260202_11.jsonl 샘플
{"symbol": "028300", ...}  // 부트스트랩 아님
{"symbol": "354200", ...}  // 부트스트랩 아님
{"symbol": "038460", ...}  // 부트스트랩 아님
{"symbol": "005930", ...}  // 부트스트랩 (삼성전자)
{"symbol": "001450", ...}  // 부트스트랩 아님
```

→ **부트스트랩 6종목 외에도 다른 종목 데이터가 수신되고 있음**  
→ 하지만 **저장이 거의 안 되고 있음**

### 3.3 근본 원인: `_log_scalp_data()` 호출 누락

코드 분석 결과, `_log_scalp_data()`는 **콜백 내에서만 호출**됩니다:

```python
# track_b_collector.py
def _register_websocket_callback(self) -> None:
    def on_price_update(data: Dict[str, Any]) -> None:
        try:
            callback_count[0] += 1
            symbol = data.get('symbol', 'UNKNOWN')
            
            # 50번마다 1회만 로그
            if callback_count[0] % 50 == 1:
                log.info(f"📊 Price update callback #{callback_count[0]}: {symbol}")
            
            self._log_scalp_data(data)  # ← 여기서 저장
        except Exception as e:
            log.error(f"Error handling price update: {e}", exc_info=True)
```

**문제점**:
1. 콜백이 호출되어도 `_log_scalp_data()`에서 **예외 발생 시 조용히 실패**
2. 로그에 `"[저장]"` 메시지가 거의 없음 → 저장 성공이 거의 없음
3. 예외는 `log.error()`로만 기록 → 로그에서 에러 확인 필요

---

## 4. 추가 조사 필요 항목

### 4.1 에러 로그 확인
```bash
# Permission denied 확인
docker logs observer 2>&1 | grep -i 'permission' | tail -20

# 스켈프 저장 에러 확인
docker logs observer 2>&1 | grep -E 'Error logging scalp|scalp.*error' -i | tail -20

# 예외 스택 트레이스 확인
docker logs observer 2>&1 | grep -A 10 'Error handling price update' | tail -50
```

### 4.2 콜백 데이터 형식 확인
```bash
# 콜백으로 전달되는 데이터 구조 확인
docker logs observer 2>&1 | grep 'Price update callback' -A 5 | tail -30
```

### 4.3 파일 쓰기 권한 재확인
```bash
# 컨테이너 내부에서 직접 쓰기 테스트
docker exec observer touch /app/config/scalp/test_write.txt
docker exec observer ls -la /app/config/scalp/test_write.txt
docker exec observer rm /app/config/scalp/test_write.txt
```

---

## 5. 임시 해결 방안

### 5.1 즉시 조치 (서버에서 실행)

#### Step 1: 상세 에러 로그 수집
```bash
# 스켈프 관련 에러 전체 추출
docker logs observer 2>&1 | grep -E 'scalp|_log_scalp_data|Error handling price' -i > ~/scalp_error_analysis.log

# 파일 확인
cat ~/scalp_error_analysis.log | tail -100
```

#### Step 2: 디버그 모드 활성화 (재시작 필요)
```bash
cd ~/observer-deploy

# .env에 디버그 로그 추가
echo "LOG_LEVEL=DEBUG" >> ~/observer/secrets/.env

# 컨테이너 재시작
docker compose -f docker-compose.server.yml restart observer

# 로그 실시간 모니터링
docker logs observer -f | grep -E 'scalp|저장|Price update'
```

#### Step 3: 권한 재확인 및 수정 (예방 차원)
```bash
# 현재 권한 확인
ls -la ~/observer/config/scalp/

# 만약 문제가 있다면 (현재는 정상)
# sudo chown -R 999:999 ~/observer/config/scalp
# sudo chmod -R 755 ~/observer/config/scalp
```

### 5.2 코드 레벨 개선 (로컬 개발)

#### 개선 1: `_log_scalp_data()` 예외 처리 강화
```python
def _log_scalp_data(self, data: Dict[str, Any]) -> None:
    try:
        # ... 기존 로직 ...
        
        # 1) 아카이브: JSONL 기록
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()
        
        # 성공 로그 추가 (현재 누락)
        log.info(f"[저장] {symbol} @ {price:,}원 → {log_file}")
        
    except PermissionError as e:
        log.error(f"❌ Permission denied writing scalp data: {log_file} - {e}")
    except OSError as e:
        log.error(f"❌ OS error writing scalp data: {log_file} - {e}")
    except Exception as e:
        log.error(f"❌ Error logging scalp data: {e}", exc_info=True)
```

#### 개선 2: 콜백 데이터 검증 추가
```python
def on_price_update(data: Dict[str, Any]) -> None:
    try:
        callback_count[0] += 1
        
        # 데이터 검증
        if not data or 'symbol' not in data:
            log.warning(f"Invalid price update data: {data}")
            return
        
        symbol = data.get('symbol', 'UNKNOWN')
        
        # 로그 빈도 조정 (디버깅용)
        if callback_count[0] % 10 == 1:  # 50 → 10으로 변경
            log.info(f"📊 Price update #{callback_count[0]}: {symbol}")
        
        self._log_scalp_data(data)
        
    except Exception as e:
        log.error(f"Error in price update callback: {e}", exc_info=True)
```

---

## 6. 최종 결론

### 6.1 문제 요약
| 구분 | 내용 |
|------|------|
| **증상** | 스켈프 데이터가 정상 대비 1/500 수준 (99.8% 감소) |
| **근본 원인** | WebSocket 수신은 정상이나, `_log_scalp_data()` 저장 실패 |
| **직접 원인** | 미확인 (에러 로그 분석 필요) |
| **권한 문제** | 없음 (lxd:999, 644 권한으로 쓰기 가능) |
| **Track A 의존** | 없음 (부트스트랩 독립 모드 정상 동작) |

### 6.2 초기 분석 문서 평가
| 항목 | 초기 분석 | 실제 상황 | 평가 |
|------|-----------|-----------|------|
| Track B 아키텍처 | 스윙 JSONL 의존 | 부트스트랩 독립 | ❌ 오류 |
| Track A Permission denied | 1001:1001, 0644 | lxd:999, 정상 동작 | ❌ 오류 |
| 스켈프 권한 문제 | 1001:1001, 0644 | lxd:999, 644 | ❌ 오류 |
| 해결 방안 (chown) | 적절 | 불필요 (이미 999) | ⚠️ 불필요 |

**결론**: 초기 분석 문서는 **구버전 아키텍처 기반**으로 작성되었거나, 실제 서버 상태를 확인하지 않고 작성된 것으로 판단됩니다.

### 6.3 다음 단계

#### 우선순위 1: 에러 로그 분석 (즉시)
```bash
ssh oracle-obs-vm-01
docker logs observer 2>&1 | grep -E 'Error|Exception|scalp' -i > ~/scalp_debug.log
cat ~/scalp_debug.log | less
```

#### 우선순위 2: 디버그 모드 활성화 (1시간 이내)
- `LOG_LEVEL=DEBUG` 설정
- 컨테이너 재시작
- 실시간 로그 모니터링

#### 우선순위 3: 코드 개선 (1~2일)
- `_log_scalp_data()` 예외 처리 강화
- 저장 성공/실패 로그 명확화
- 콜백 데이터 검증 추가

#### 우선순위 4: 모니터링 강화 (1주일)
- 스켈프 파일 크기 알림 설정
- 저장 실패율 메트릭 추가
- WebSocket 수신/저장 비율 대시보드

---

## 7. 참고 자료

### 7.1 서버 정보
- **호스트**: oracle-obs-vm-01 (134.185.117.22)
- **배포 이미지**: ghcr.io/tawbury/observer:build-20260130-143831
- **컨테이너 사용자**: uid=999(observer)
- **볼륨 마운트**: `~/observer/config:/app/config`

### 7.2 관련 파일
- 코드: `app/observer/src/collector/track_b_collector.py`
- 스켈프 경로: `/app/config/scalp/YYYYMMDD_HH.jsonl`
- 로그: `docker logs observer`

### 7.3 정상 동작 기준
- 1시간당 10~15MB (약 20,000~30,000 라인)
- WebSocket 수신 대비 저장 비율: 80% 이상
- "[저장]" 로그: 분당 100건 이상 (장중 기준)

---

## 8. 디버깅 계획 구현 요약 (2026-02-02)

### Phase 1–2: 서버 로그 분석 결과
- `[엔진] 가격 업데이트 수신`: 116건 (provider_engine 콜백 호출)
- WS 수신: 7,813건 / H0STCNT0: 7,579건 / PINGPONG: 214건
- `Error logging scalp data` / `AttributeError` 로그: 미확인 (에러 로그 없음)

### Phase 3–4: 코드 변경 사항
- **진단 로깅**: 콜백 100건마다 INFO 로그, 데이터 검증(symbol 필수)
- **형식 호환**: `volume` int/dict, `bid_ask` top-level fallback 처리
- **예외 처리**: `PermissionError`, `OSError` 별도 처리, `repr(data)` 샘플 출력

### 다음 단계
- 이미지 빌드 및 서버 배포 후 장중 1시간 모니터링
- `[저장]` vs `Error logging scalp` 비율 확인

---

**작성**: 2026-02-02  
**최종 업데이트**: 2026-02-02 12:54 UTC (21:54 KST)
