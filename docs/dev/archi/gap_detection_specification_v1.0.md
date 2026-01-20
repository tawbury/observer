# Gap Detection 및 Gap-Marker 명세서

**Document ID**: SPEC-GAP-DETECTION-001
**Version**: 1.0.0
**Date**: 2026-01-20
**Parent Document**: data_pipeline_architecture_observer_v1.0.md
**Status**: Draft

---

## 1. 개요

본 문서는 Stock Trading Observer에서 데이터 수집 중단(Gap) 감지 및 Gap-marker 기록 정책을 정의합니다.

### 1.1 Gap-Marker 철학

> **"Record gap evidence, don't restore"**
>
> 갭 발생 시 복원을 시도하지 않고 증거만 기록합니다.

**근거**:
- **안정성**: 복원 시도가 시스템 부하 가중 및 추가 장애 유발 가능
- **정확성**: 실시간 데이터와 복원 데이터 혼재 방지
- **투명성**: 갭을 명확히 표시하여 데이터 품질 신뢰도 향상
- **분석 용이**: 갭 구간을 인지하고 백테스팅/분석 수행

---

## 2. Gap 정의 및 분류

### 2.1 Gap 정의

**Gap (데이터 공백)**: 정상적으로 데이터가 수신되어야 하는 시점에 데이터가 수신되지 않은 상태

### 2.2 Gap 유형 분류

| Gap 유형 | 정의 | 임계값 | 영향 범위 |
|---------|------|--------|---------|
| **Minor Gap** | 짧은 데이터 공백 | 10~60초 | 경고 로그만 기록 |
| **Major Gap** | 중간 데이터 공백 | 60초~5분 | Gap-marker 생성 |
| **Critical Gap** | 장시간 데이터 공백 | 5분 이상 | Gap-marker + 이상일 마킹 |

### 2.3 Scope별 Gap

| Scope | 설명 | 감지 대상 |
|-------|------|---------|
| **scalp** | Track B (WebSocket) 데이터 공백 | 특정 종목 또는 전체 슬롯 |
| **swing** | Track A (REST) 데이터 공백 | 전체 Universe 또는 특정 종목 |
| **all** | 전체 시스템 데이터 공백 | Track A + Track B 모두 |

---

## 3. Gap 감지 알고리즘

### 3.1 Track B (WebSocket/Scalp) Gap 감지

#### 알고리즘: Last-Seen Timestamp 기반

```python
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

class ScalpGapDetector:
    """
    Track B (WebSocket) Gap 감지기

    각 슬롯별로 마지막 수신 시각을 추적하고,
    임계값 초과 시 Gap 이벤트 생성
    """

    def __init__(self, gap_threshold_seconds: int = 60):
        self.gap_threshold = timedelta(seconds=gap_threshold_seconds)
        self.last_seen: Dict[str, datetime] = {}  # symbol -> last_timestamp
        self.active_gaps: Dict[str, GapContext] = {}  # symbol -> gap_context

    def record_tick(self, symbol: str, timestamp: datetime):
        """
        틱 데이터 수신 기록

        Args:
            symbol: 종목 코드
            timestamp: 수신 시각
        """
        # 기존 Gap이 진행 중이면 종료
        if symbol in self.active_gaps:
            self._close_gap(symbol, timestamp)

        # 마지막 수신 시각 업데이트
        self.last_seen[symbol] = timestamp

    def check_gaps(self, current_time: datetime) -> List[GapEvent]:
        """
        모든 활성 슬롯의 Gap 검사

        Args:
            current_time: 현재 시각 (시스템 시각)

        Returns:
            감지된 Gap 이벤트 리스트
        """
        gaps = []

        for symbol, last_ts in self.last_seen.items():
            elapsed = current_time - last_ts

            # Gap 감지
            if elapsed > self.gap_threshold:
                # 새로운 Gap 시작
                if symbol not in self.active_gaps:
                    gap_context = GapContext(
                        symbol=symbol,
                        gap_start_ts=last_ts,
                        scope="scalp",
                        reason="no_data_received"
                    )
                    self.active_gaps[symbol] = gap_context

                    # Minor Gap (10~60초): 로그만
                    if elapsed < timedelta(seconds=60):
                        self._log_minor_gap(symbol, elapsed)

                    # Major Gap (60초~5분): Gap-marker 생성
                    elif elapsed < timedelta(minutes=5):
                        gap_event = self._create_gap_marker(
                            gap_context,
                            current_time,
                            severity="MAJOR"
                        )
                        gaps.append(gap_event)

                    # Critical Gap (5분 이상): Gap-marker + 이상일 마킹
                    else:
                        gap_event = self._create_gap_marker(
                            gap_context,
                            current_time,
                            severity="CRITICAL"
                        )
                        gaps.append(gap_event)
                        self._mark_anomaly_day(symbol, current_time)

        return gaps

    def _close_gap(self, symbol: str, resume_ts: datetime):
        """
        Gap 종료 처리

        Args:
            symbol: 종목 코드
            resume_ts: 데이터 재수신 시각
        """
        if symbol not in self.active_gaps:
            return

        gap_ctx = self.active_gaps[symbol]
        gap_seconds = (resume_ts - gap_ctx.gap_start_ts).total_seconds()

        # Gap 종료 이벤트 로깅
        logger.info(
            "Gap closed",
            extra={
                "symbol": symbol,
                "gap_start": gap_ctx.gap_start_ts.isoformat(),
                "gap_end": resume_ts.isoformat(),
                "gap_seconds": gap_seconds,
                "reason": gap_ctx.reason
            }
        )

        # Gap 컨텍스트 제거
        del self.active_gaps[symbol]

    def _create_gap_marker(
        self,
        gap_ctx: GapContext,
        current_time: datetime,
        severity: str
    ) -> GapEvent:
        """
        Gap-marker 이벤트 생성

        Args:
            gap_ctx: Gap 컨텍스트
            current_time: 현재 시각
            severity: 심각도 (MAJOR, CRITICAL)

        Returns:
            GapEvent 객체
        """
        gap_seconds = (current_time - gap_ctx.gap_start_ts).total_seconds()

        return GapEvent(
            event_type="gap_marker",
            symbol=gap_ctx.symbol,
            gap_start_ts=gap_ctx.gap_start_ts,
            gap_end_ts=current_time,  # 현재까지의 갭 (진행 중)
            gap_seconds=int(gap_seconds),
            scope=gap_ctx.scope,
            reason=gap_ctx.reason,
            severity=severity,
            session_id=get_current_session_id()
        )
```

#### Gap 감지 주기

- **체크 주기**: 5초마다 `check_gaps()` 호출
- **임계값**: 60초 (기본값, 설정 가능)
- **예시**:
  - 09:30:00 마지막 틱 수신
  - 09:31:00 체크 → 60초 경과 → Major Gap 발생
  - 09:35:00 체크 → 5분 경과 → Critical Gap으로 승격

### 3.2 Track A (REST/Swing) Gap 감지

#### 알고리즘: 예상 수집 시각 기반

```python
class SwingGapDetector:
    """
    Track A (REST) Gap 감지기

    10분 주기 수집 기준, 예상 시각 대비 지연 감지
    """

    def __init__(self, collection_interval_minutes: int = 10):
        self.interval = timedelta(minutes=collection_interval_minutes)
        self.last_collection_time: Optional[datetime] = None
        self.expected_next_time: Optional[datetime] = None

    def record_collection(self, timestamp: datetime):
        """
        수집 완료 기록

        Args:
            timestamp: 수집 완료 시각
        """
        self.last_collection_time = timestamp
        self.expected_next_time = timestamp + self.interval

    def check_gap(self, current_time: datetime) -> Optional[GapEvent]:
        """
        예상 수집 시각 대비 지연 검사

        Args:
            current_time: 현재 시각

        Returns:
            Gap 감지 시 GapEvent, 아니면 None
        """
        if self.expected_next_time is None:
            return None

        # 예상 시각 + 여유 시간(2분) 초과 시 Gap
        grace_period = timedelta(minutes=2)
        threshold = self.expected_next_time + grace_period

        if current_time > threshold:
            gap_seconds = (current_time - self.expected_next_time).total_seconds()

            # Major Gap (2~10분)
            if gap_seconds < 600:
                severity = "MAJOR"
            # Critical Gap (10분 이상)
            else:
                severity = "CRITICAL"

            return GapEvent(
                event_type="gap_marker",
                symbol=None,  # Track A는 전체 Universe
                gap_start_ts=self.expected_next_time,
                gap_end_ts=current_time,
                gap_seconds=int(gap_seconds),
                scope="swing",
                reason="collection_delayed",
                severity=severity,
                session_id=get_current_session_id()
            )

        return None
```

### 3.3 WebSocket 연결 끊김 감지

#### 알고리즘: Reconnection Event 연계

```python
class WebSocketGapDetector:
    """
    WebSocket 연결 끊김으로 인한 Gap 감지
    """

    def on_disconnect(self, disconnect_time: datetime, reason: str):
        """
        WebSocket 연결 끊김 이벤트 처리

        Args:
            disconnect_time: 끊김 시각
            reason: 끊김 사유
        """
        # Gap 시작 기록
        self.gap_start = disconnect_time
        self.disconnect_reason = reason

    def on_reconnect(self, reconnect_time: datetime) -> GapEvent:
        """
        WebSocket 재연결 이벤트 처리

        Args:
            reconnect_time: 재연결 시각

        Returns:
            Gap 이벤트
        """
        if self.gap_start is None:
            return None

        gap_seconds = (reconnect_time - self.gap_start).total_seconds()

        gap_event = GapEvent(
            event_type="gap_marker",
            symbol=None,  # 전체 WebSocket 연결
            gap_start_ts=self.gap_start,
            gap_end_ts=reconnect_time,
            gap_seconds=int(gap_seconds),
            scope="scalp",  # WebSocket = scalp
            reason=f"ws_disconnect: {self.disconnect_reason}",
            severity="CRITICAL" if gap_seconds > 300 else "MAJOR",
            session_id=get_current_session_id()
        )

        # Gap 컨텍스트 초기화
        self.gap_start = None
        self.disconnect_reason = None

        return gap_event
```

---

## 4. Gap-Marker 데이터 스키마

### 4.1 JSONL 파일 저장

**파일 경로**: `data/observer/system/events/{provider}/YYYYMMDD.jsonl`

**예시**:
```
data/observer/system/events/kis/20260120.jsonl
```

### 4.2 Gap-Marker 이벤트 스키마

```json
{
  "event_type": "gap_marker",
  "timestamp": "2026-01-20T09:32:00.000+09:00",
  "symbol": "005930",
  "gap_start_ts": "2026-01-20T09:30:00.000+09:00",
  "gap_end_ts": "2026-01-20T09:32:00.000+09:00",
  "gap_seconds": 120,
  "scope": "scalp",
  "reason": "ws_disconnect: timeout",
  "severity": "MAJOR",
  "session_id": "sess_20260120_093000",
  "metadata": {
    "reconnect_attempt": 3,
    "slot_number": 15,
    "provider": "kis",
    "market": "kr_stocks"
  }
}
```

### 4.3 필드 정의

| 필드 | 타입 | 필수 | 설명 | 예시 |
|-----|------|------|------|------|
| `event_type` | string | O | 이벤트 유형 (고정값) | "gap_marker" |
| `timestamp` | ISO8601 | O | Gap 감지 시각 | "2026-01-20T09:32:00+09:00" |
| `symbol` | string | - | 종목 코드 (Track B만, null 가능) | "005930" 또는 null |
| `gap_start_ts` | ISO8601 | O | Gap 시작 시각 | "2026-01-20T09:30:00+09:00" |
| `gap_end_ts` | ISO8601 | O | Gap 종료 시각 | "2026-01-20T09:32:00+09:00" |
| `gap_seconds` | int | O | Gap 지속 시간 (초) | 120 |
| `scope` | string | O | 영향 범위 | "scalp", "swing", "all" |
| `reason` | string | O | Gap 발생 사유 | "ws_disconnect", "api_error" |
| `severity` | string | O | 심각도 | "MINOR", "MAJOR", "CRITICAL" |
| `session_id` | string | O | 세션 식별자 | "sess_20260120_093000" |
| `metadata` | object | - | 추가 메타데이터 | {...} |

### 4.4 Gap Reason 코드

| Reason 코드 | 설명 | 발생 상황 |
|-----------|------|---------|
| `ws_disconnect` | WebSocket 연결 끊김 | 네트워크 장애, 서버 재시작 |
| `ws_timeout` | WebSocket PING 무응답 | PING 10초 내 PONG 미수신 |
| `api_error` | REST API 호출 실패 | 5xx 오류, 타임아웃 |
| `rate_limit` | Rate Limit 초과 | 429 응답 수신 |
| `no_data_received` | 데이터 미수신 | 예상 시각에 데이터 없음 |
| `slot_manager_error` | 슬롯 관리 오류 | 슬롯 할당/해제 실패 |
| `system_error` | 시스템 내부 오류 | 예외 발생, 버그 |
| `manual_stop` | 수동 중지 | 운영자 개입 |

---

## 5. Gap 후 데이터 처리

### 5.1 Gap 후 첫 데이터 Quality Flag

Gap 종료 후 첫 번째 수신 데이터는 `quality_flag: "gap"`으로 마킹:

```python
def process_post_gap_data(symbol: str, data: MarketDataContract) -> PatternRecordContract:
    """
    Gap 후 첫 데이터 처리

    Args:
        symbol: 종목 코드
        data: 수신 데이터

    Returns:
        quality_flag="gap"으로 마킹된 레코드
    """
    is_after_gap = gap_detector.was_in_gap(symbol)

    record = PatternRecordContract(
        session_id=get_current_session_id(),
        generated_at=datetime.now(timezone.utc).isoformat(),
        observation=data,
        schema={"version": "1.0.0", "field_count": 12},
        quality={
            "validation_passed": True,
            "guard_passed": True,
            "quality_flag": "gap" if is_after_gap else "normal"
        },
        interpretation={
            "mitigation_level": 0,
            "track": "scalp",
            "slot_number": 15,
            "post_gap": is_after_gap
        }
    )

    # Gap 상태 해제
    if is_after_gap:
        gap_detector.clear_gap_state(symbol)

    return record
```

### 5.2 Gap 분석 시 처리

백테스팅 또는 전략 분석 시 Gap 구간 처리:

```python
def load_data_for_analysis(
    start_date: str,
    end_date: str,
    exclude_gaps: bool = True
) -> pd.DataFrame:
    """
    분석용 데이터 로드 (Gap 제외 옵션)

    Args:
        start_date: 시작일
        end_date: 종료일
        exclude_gaps: Gap 구간 제외 여부

    Returns:
        DataFrame
    """
    # 데이터 로드
    df = load_raw_data(start_date, end_date)

    if exclude_gaps:
        # Gap-marker 이벤트 로드
        gap_events = load_gap_markers(start_date, end_date)

        # Gap 구간 데이터 제외
        for gap in gap_events:
            mask = (
                (df['timestamp'] >= gap['gap_start_ts']) &
                (df['timestamp'] <= gap['gap_end_ts'])
            )
            df = df[~mask]

        # quality_flag="gap" 데이터 제외
        df = df[df['quality_flag'] != 'gap']

    return df
```

---

## 6. Gap 모니터링 및 알림

### 6.1 Gap 메트릭

**수집 메트릭**:
- `gap_count_daily`: 일일 Gap 발생 건수
- `gap_total_seconds_daily`: 일일 총 Gap 시간 (초)
- `gap_by_severity`: 심각도별 Gap 분포 (MINOR/MAJOR/CRITICAL)
- `gap_by_scope`: Scope별 Gap 분포 (scalp/swing/all)
- `gap_by_reason`: 사유별 Gap 분포

**목표**:
- **Track A Gap**: 0건/일 (10분 주기이므로 Gap 거의 발생하지 않아야 함)
- **Track B Gap (MAJOR+)**: < 5건/일
- **Track B Gap (CRITICAL)**: 0건/일
- **총 Gap 시간**: < 5분/일

### 6.2 알림 정책

| 조건 | 알림 레벨 | 채널 | 조치 |
|-----|----------|------|------|
| MINOR Gap (10~60초) | INFO | Log only | 모니터링 |
| MAJOR Gap (1~5분) | WARNING | Telegram | 확인 필요 |
| CRITICAL Gap (5분 이상) | CRITICAL | Telegram | 즉시 조치 |
| Gap 5회 이상/시간 | CRITICAL | Telegram | 시스템 점검 |
| 총 Gap 시간 > 10분/일 | WARNING | Telegram | 인프라 점검 |

**Telegram 알림 포맷**:
```
🔴 CRITICAL Gap Detected

Symbol: 005930 (삼성전자)
Duration: 7분 23초
Scope: scalp (Track B)
Reason: ws_disconnect: timeout
Time: 2026-01-20 09:30:00 ~ 09:37:23

Action Required: Check network and WebSocket connection
```

---

## 7. 이상일(Anomaly Day) 마킹

### 7.1 이상일 조건

다음 조건 중 하나라도 만족 시 해당 날짜를 이상일로 마킹:

| 조건 | 임계값 | 설명 |
|-----|--------|------|
| **WS 재연결 횟수** | ≥ 20회/일 | WebSocket 불안정 |
| **WS 끊김 누적 시간** | ≥ 10분/일 | 총 Gap 시간 과다 |
| **로그 공백 60초 이상** | ≥ 2회/일 | CRITICAL Gap 발생 |
| **Scalp 기록률** | < 97% (5분 이상) | 데이터 수집 품질 저하 |
| **CPU 사용률** | ≥ 85% (10분 이상) | 시스템 부하 |
| **디스크 사용률** | > 80% | 디스크 부족 |

### 7.2 이상일 처리

```python
class AnomalyDayManager:
    """
    이상일 마킹 및 관리
    """

    def mark_anomaly_day(self, date: str, reason: str):
        """
        이상일 마킹

        Args:
            date: 날짜 (YYYYMMDD)
            reason: 이상일 사유
        """
        anomaly_record = {
            "date": date,
            "marked_at": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "extended_retention": True,
            "retention_days": 7  # 기본 3일 → 7일 연장
        }

        # 이상일 기록 파일 저장
        self._save_anomaly_marker(date, anomaly_record)

        # 로그 기록
        logger.warning(
            "Anomaly day marked",
            extra={
                "date": date,
                "reason": reason,
                "retention_extended_to": 7
            }
        )

        # 알림 전송
        self._send_anomaly_alert(date, reason)

    def is_anomaly_day(self, date: str) -> bool:
        """
        해당 날짜가 이상일인지 확인
        """
        return os.path.exists(f"data/observer/system/anomaly/{date}.json")

    def get_retention_days(self, date: str) -> int:
        """
        해당 날짜의 보관 기간 반환

        Returns:
            이상일: 7일, 정상일: 3일
        """
        if self.is_anomaly_day(date):
            return 7
        else:
            return 3
```

**이상일 파일 경로**:
```
data/observer/system/anomaly/20260120.json
```

**이상일 파일 내용**:
```json
{
  "date": "20260120",
  "marked_at": "2026-01-20T15:45:30.000+09:00",
  "reason": "ws_reconnect_count >= 20 (actual: 23)",
  "extended_retention": true,
  "retention_days": 7,
  "gap_count": 23,
  "total_gap_seconds": 720,
  "critical_gap_count": 2
}
```

---

## 8. 테스트 시나리오

### 8.1 Gap 감지 테스트

```python
@pytest.mark.unit
def test_scalp_gap_detection():
    """Scalp Gap 감지 테스트"""
    detector = ScalpGapDetector(gap_threshold_seconds=60)

    # 1. 정상 틱 수신
    t0 = datetime.now(timezone.utc)
    detector.record_tick("005930", t0)

    # 2. 30초 후 체크 (Gap 없음)
    gaps = detector.check_gaps(t0 + timedelta(seconds=30))
    assert len(gaps) == 0

    # 3. 65초 후 체크 (MAJOR Gap 발생)
    gaps = detector.check_gaps(t0 + timedelta(seconds=65))
    assert len(gaps) == 1
    assert gaps[0].severity == "MAJOR"
    assert gaps[0].gap_seconds == 65

    # 4. 6분 후 체크 (CRITICAL Gap으로 승격)
    gaps = detector.check_gaps(t0 + timedelta(minutes=6))
    assert len(gaps) == 1
    assert gaps[0].severity == "CRITICAL"
```

### 8.2 Gap 종료 테스트

```python
@pytest.mark.unit
def test_gap_closure():
    """Gap 종료 테스트"""
    detector = ScalpGapDetector()

    # 1. Gap 발생
    t0 = datetime.now(timezone.utc)
    detector.record_tick("005930", t0)
    gaps = detector.check_gaps(t0 + timedelta(seconds=70))
    assert len(gaps) == 1

    # 2. 데이터 재수신 (Gap 종료)
    t1 = t0 + timedelta(seconds=90)
    detector.record_tick("005930", t1)

    # 3. Gap 상태 확인 (종료됨)
    assert "005930" not in detector.active_gaps
```

### 8.3 통합 테스트

```python
@pytest.mark.integration
async def test_gap_end_to_end():
    """Gap 종단 간 테스트"""
    # 1. WebSocket 연결
    ws_client = KISWebSocketClient()
    await ws_client.connect()

    # 2. 종목 구독
    await ws_client.subscribe("005930")

    # 3. 30초 동안 정상 수신
    await asyncio.sleep(30)
    gap_markers = load_gap_markers_today()
    assert len(gap_markers) == 0

    # 4. WebSocket 강제 연결 끊기
    await ws_client.disconnect()

    # 5. 90초 대기 (Gap 발생 예상)
    await asyncio.sleep(90)

    # 6. Gap-marker 생성 확인
    gap_markers = load_gap_markers_today()
    assert len(gap_markers) == 1
    assert gap_markers[0]['scope'] == 'scalp'
    assert gap_markers[0]['reason'] == 'ws_disconnect'
```

---

## 9. Gap 분석 도구

### 9.1 Gap 리포트 생성

```python
def generate_gap_report(date: str) -> dict:
    """
    일일 Gap 리포트 생성

    Args:
        date: 날짜 (YYYYMMDD)

    Returns:
        Gap 통계 딕셔너리
    """
    gap_events = load_gap_markers(date, date)

    report = {
        "date": date,
        "total_gap_count": len(gap_events),
        "total_gap_seconds": sum(g['gap_seconds'] for g in gap_events),
        "by_severity": {
            "MINOR": len([g for g in gap_events if g['severity'] == 'MINOR']),
            "MAJOR": len([g for g in gap_events if g['severity'] == 'MAJOR']),
            "CRITICAL": len([g for g in gap_events if g['severity'] == 'CRITICAL'])
        },
        "by_scope": {
            "scalp": len([g for g in gap_events if g['scope'] == 'scalp']),
            "swing": len([g for g in gap_events if g['scope'] == 'swing']),
            "all": len([g for g in gap_events if g['scope'] == 'all'])
        },
        "by_reason": {},
        "longest_gap": max(gap_events, key=lambda g: g['gap_seconds']) if gap_events else None,
        "is_anomaly_day": AnomalyDayManager().is_anomaly_day(date)
    }

    # Reason별 집계
    for gap in gap_events:
        reason = gap['reason']
        report['by_reason'][reason] = report['by_reason'].get(reason, 0) + 1

    return report
```

**리포트 예시**:
```json
{
  "date": "20260120",
  "total_gap_count": 5,
  "total_gap_seconds": 420,
  "by_severity": {
    "MINOR": 2,
    "MAJOR": 2,
    "CRITICAL": 1
  },
  "by_scope": {
    "scalp": 4,
    "swing": 1,
    "all": 0
  },
  "by_reason": {
    "ws_disconnect": 3,
    "no_data_received": 2
  },
  "longest_gap": {
    "gap_seconds": 310,
    "symbol": "005930",
    "reason": "ws_disconnect: timeout"
  },
  "is_anomaly_day": false
}
```

### 9.2 Gap 시각화

```python
import pandas as pd
import matplotlib.pyplot as plt

def visualize_gaps(date: str):
    """
    Gap 타임라인 시각화

    Args:
        date: 날짜 (YYYYMMDD)
    """
    gaps = load_gap_markers(date, date)

    # DataFrame 생성
    df = pd.DataFrame(gaps)
    df['gap_start_ts'] = pd.to_datetime(df['gap_start_ts'])
    df['gap_end_ts'] = pd.to_datetime(df['gap_end_ts'])

    # 타임라인 플롯
    fig, ax = plt.subplots(figsize=(12, 6))

    for idx, row in df.iterrows():
        color = {
            'MINOR': 'yellow',
            'MAJOR': 'orange',
            'CRITICAL': 'red'
        }[row['severity']]

        ax.barh(
            y=idx,
            width=(row['gap_end_ts'] - row['gap_start_ts']).total_seconds(),
            left=row['gap_start_ts'],
            color=color,
            alpha=0.7,
            label=row['severity']
        )

    ax.set_xlabel('Time')
    ax.set_ylabel('Gap Event')
    ax.set_title(f'Gap Timeline - {date}')
    plt.tight_layout()
    plt.savefig(f'gap_timeline_{date}.png')
```

---

## 10. 참고 자료

- **Parent Document**: data_pipeline_architecture_observer_v1.0.md (Section 2.7, AD-004)
- **Related**: obs_architecture.md (Section 2.14.2 System Events 스키마)

---

## 11. 변경 이력

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-20 | Initial gap detection specification (C-003 해결용) |

---

**문서 상태**: Draft - C-003 이슈 해결용
