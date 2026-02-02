"""
시간별 로테이션 로그 핸들러

매 시간 정각에 새 파일로 전환하는 커스텀 로그 핸들러.
TimedRotatingFileHandler와 달리 핸들러 생성 시점이 아닌 정각 기준으로 로테이션.
"""
import logging
import sys
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from .timezone import get_zoneinfo


class HourlyRotatingFileHandler(logging.FileHandler):
    """
    매 시간 정각에 새 파일로 전환하는 로그 핸들러.

    파일명 형식: {YYYYMMDD_HH}.log
    예: 20260129_14.log, 20260129_15.log

    특징:
    - 핸들러 생성 시 즉시 현재 시간대 파일 생성
    - 매 로그 기록 시 시간 체크하여 정각에 새 파일로 전환
    - 중간에 시작해도 해당 시간대 파일 자동 생성
    - 스레드 안전: 동시 접근 시 Lock으로 보호
    - 타임존 지원: Asia/Seoul 기준 로테이션 (Docker UTC 환경 대응)

    Args:
        log_dir: 로그 파일이 저장될 디렉토리 경로
        tz_name: 타임존 이름 (기본값: "Asia/Seoul")

    Example:
        handler = HourlyRotatingFileHandler("/app/logs/system")
        # 생성 파일: /app/logs/system/20260129_14.log (KST 기준)
    """

    def __init__(self, log_dir: str, tz_name: str = "Asia/Seoul") -> None:
        self.log_dir = Path(log_dir)
        self._tz_name = tz_name
        self._tz = get_zoneinfo(tz_name)
        self._rotate_lock = threading.Lock()

        # 디렉토리 생성 (예외 처리 포함)
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"[HourlyRotatingFileHandler] 디렉토리 생성 실패: {log_dir} - {e}", file=sys.stderr)
            raise

        self._current_hour: Optional[int] = None
        self._current_date: Optional[object] = None
        self._current_file: str = ""

        self._update_filename()
        super().__init__(self._current_file, mode='a', encoding='utf-8')

    def _now(self) -> datetime:
        """타임존 인식 현재 시간 반환"""
        if self._tz:
            return datetime.now(self._tz)
        return datetime.now(timezone.utc)

    def _update_filename(self) -> None:
        """현재 시간(타임존 적용) 기준으로 파일명 업데이트"""
        now = self._now()
        hour_str = now.strftime("%Y%m%d_%H")
        self._current_file = str(self.log_dir / f"{hour_str}.log")
        self._current_hour = now.hour
        self._current_date = now.date()
    
    def _should_rotate(self) -> bool:
        """로테이션 필요 여부 확인 (시간 또는 날짜 변경)"""
        now = self._now()
        return now.hour != self._current_hour or now.date() != self._current_date

    def emit(self, record: logging.LogRecord) -> None:
        """로그 레코드 출력 (시간 변경 시 새 파일로 전환)"""
        try:
            # 로테이션 체크 및 실행 (Lock으로 보호)
            with self._rotate_lock:
                if self._should_rotate():
                    try:
                        self.close()
                        self._update_filename()
                        # 디렉토리 재확인 (런타임 중 삭제된 경우 대비)
                        self.log_dir.mkdir(parents=True, exist_ok=True)
                        self.stream = self._open()
                    except OSError as e:
                        print(f"[HourlyRotatingFileHandler] 로테이션 실패: {e}", file=sys.stderr)
                        self.handleError(record)
                        return

            # 실제 로그 기록 (Lock 외부 - 성능 최적화)
            super().emit(record)
        except Exception:
            self.handleError(record)
