FROM python:3.11-slim as builder

# 빌드 스테이지: 의존성 설치
WORKDIR /build

# requirements.txt 복사 및 의존성 설치 (캐시 최적화)
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt || true

# 런타임 스테이지: 최소 이미지
FROM python:3.11-slim

WORKDIR /app

# 빌더 스테이지에서 의존성 복사
COPY --from=builder /root/.local /root/.local

# 애플리케이션 파일 복사
COPY observer.py /app/
COPY paths.py /app/
COPY src/ /app/src/

# 필수 디렉토리 생성
RUN mkdir -p /app/data/observer \
    && mkdir -p /app/logs \
    && mkdir -p /app/config

# 환경 변수 설정 (Standalone 모드)
ENV QTS_OBSERVER_STANDALONE=1
ENV PYTHONPATH=/app/src:/app
ENV OBSERVER_DATA_DIR=/app/data/observer
ENV OBSERVER_LOG_DIR=/app/logs
ENV PATH=/root/.local/bin:$PATH

# 보안: 비-root 사용자로 실행
RUN groupadd -r qts && useradd -r -g qts qts
RUN chown -R qts:qts /app
USER qts

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# 포트 노출
EXPOSE 8000

# 기본 실행 명령
CMD ["python", "observer.py"]
