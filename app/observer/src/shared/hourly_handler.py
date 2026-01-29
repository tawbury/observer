"""
시간별 로테이션 로그 핸들러

매 시간 정각에 새 파일로 전환하는 커스텀 로그 핸들러.
TimedRotatingFileHandler와 달리 핸들러 생성 시점이 아닌 정각 기준으로 로테이션.
"""
import logging
from pathlib import Path
from datetime import datetime


class HourlyRotatingFileHandler(logging.FileHandler):
    """
    매 시간 정각에 새 파일로 전환하는 로그 핸들러.
    
    파일명 형식: {YYYYMMDD_HH}.log
    예: 20260129_14.log, 20260129_15.log
    
    특징:
    - 핸들러 생성 시 즉시 현재 시간대 파일 생성
    - 매 로그 기록 시 시간 체크하여 정각에 새 파일로 전환
    - 중간에 시작해도 해당 시간대 파일 자동 생성
    
    Args:
        log_dir: 로그 파일이 저장될 디렉토리 경로
    
    Example:
        handler = HourlyRotatingFileHandler("/app/logs/system")
        # 생성 파일: /app/logs/system/20260129_14.log
    """
    
    def __init__(self, log_dir):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._current_hour = None
        self._current_date = None
        self._update_filename()
        super().__init__(self._current_file, mode='a', encoding='utf-8')
    
    def _update_filename(self):
        """현재 시간 기준으로 파일명 업데이트"""
        now = datetime.now()
        hour_str = now.strftime("%Y%m%d_%H")
        self._current_file = str(self.log_dir / f"{hour_str}.log")
        self._current_hour = now.hour
        self._current_date = now.date()
    
    def _should_rotate(self) -> bool:
        """로테이션이 필요한지 확인 (시간 또는 날짜 변경)"""
        now = datetime.now()
        return now.hour != self._current_hour or now.date() != self._current_date
    
    def emit(self, record):
        """로그 레코드 출력 (시간 변경 시 새 파일로 전환)"""
        try:
            # 시간이 바뀌면 새 파일로 전환
            if self._should_rotate():
                self.close()
                self._update_filename()
                self.stream = self._open()
            super().emit(record)
        except Exception:
            self.handleError(record)
