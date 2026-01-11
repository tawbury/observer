# src/ops/observer/inputs/replay_market_data_provider.py

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, TextIO

from .imarket_data_provider import IMarketDataProvider, MarketDataContract


@dataclass(frozen=True)
class ReplayStats:
    lines_read: int = 0
    lines_skipped: int = 0
    json_errors: int = 0


class ReplayMarketDataProvider(IMarketDataProvider):
    """
    ReplayMarketDataProvider

    목적:
    - 과거에 저장된 MarketDataContract JSONL을 '1줄=1스냅샷'으로 재생한다.
    - Observer는 이 Provider를 통해 과거 데이터를 실시간처럼 소비할 수 있다.

    입력 포맷(강제):
    - JSONL (UTF-8)
    - 각 라인은 MarketDataContract(dict) JSON 1개
    """

    def __init__(self, jsonl_path: Path, *, strict: bool = False) -> None:
        """
        Args:
            jsonl_path: replay 대상 JSONL 파일 경로
            strict: True면 JSON 파싱 에러를 치명으로 취급(즉시 EOF 처리). False면 해당 라인 skip.
        """
        self._path = Path(jsonl_path)
        self._strict = strict

        self._fp: Optional[TextIO] = None
        self._stats = ReplayStats()

    @property
    def path(self) -> Path:
        return self._path

    @property
    def stats(self) -> ReplayStats:
        return self._stats

    def _ensure_open(self) -> bool:
        if self._fp is not None:
            return True
        if not self._path.exists() or not self._path.is_file():
            return False
        self._fp = self._path.open("r", encoding="utf-8")
        return True

    def fetch(self) -> Optional[MarketDataContract]:
        """
        Returns:
            - MarketDataContract 1개
            - EOF 또는 열기 실패 시 None
        """
        try:
            if not self._ensure_open():
                return None

            assert self._fp is not None

            while True:
                line = self._fp.readline()
                if line == "":
                    return None  # EOF

                self._stats = ReplayStats(
                    lines_read=self._stats.lines_read + 1,
                    lines_skipped=self._stats.lines_skipped,
                    json_errors=self._stats.json_errors,
                )

                line = line.strip()
                if not line:
                    self._stats = ReplayStats(
                        lines_read=self._stats.lines_read,
                        lines_skipped=self._stats.lines_skipped + 1,
                        json_errors=self._stats.json_errors,
                    )
                    continue

                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    self._stats = ReplayStats(
                        lines_read=self._stats.lines_read,
                        lines_skipped=self._stats.lines_skipped + 1,
                        json_errors=self._stats.json_errors + 1,
                    )
                    if self._strict:
                        return None
                    continue

                if not isinstance(obj, dict):
                    self._stats = ReplayStats(
                        lines_read=self._stats.lines_read,
                        lines_skipped=self._stats.lines_skipped + 1,
                        json_errors=self._stats.json_errors,
                    )
                    continue

                # 최소 형태 검증(필드 누락은 Observer에서 처리할 수도 있지만, 여기서 1차로 방어)
                if "meta" not in obj or "instruments" not in obj:
                    self._stats = ReplayStats(
                        lines_read=self._stats.lines_read,
                        lines_skipped=self._stats.lines_skipped + 1,
                        json_errors=self._stats.json_errors,
                    )
                    continue

                return obj  # MarketDataContract

        except Exception:
            # Provider는 예외를 외부로 던지지 않는다.
            return None

    def reset(self) -> None:
        # 스트림 재시작
        self.close()
        self._stats = ReplayStats()

    def close(self) -> None:
        if self._fp is not None:
            try:
                self._fp.close()
            except Exception:
                pass
            finally:
                self._fp = None
