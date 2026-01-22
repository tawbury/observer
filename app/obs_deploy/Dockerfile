FROM python:3.11-slim as builder

# 빌드 스테이지: 의존성 설치
WORKDIR /build

# requirements.txt 복사 및 의존성 설치 (캐시 최적화)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 런타임 스테이지: 최소 이미지
FROM python:3.11-slim

WORKDIR /app

# 빌더 스테이지에서 의존성 복사
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 애플리케이션 파일 복사 (소스는 ./app 하위에 위치)
COPY app/observer.py /app/
COPY app/paths.py /app/
COPY app/src/ /app/src/

# 필수 디렉토리 생성
RUN mkdir -p /app/data/observer \
    && mkdir -p /app/logs/system \
    && mkdir -p /app/logs/maintenance \
    && mkdir -p /app/config/observer \
    && mkdir -p /app/secrets/.kis_cache

# 환경 변수 설정 (Standalone 모드)
ENV OBSERVER_STANDALONE=1
ENV PYTHONPATH=/app/src:/app

# 경로 환경변수 (paths.py에서 사용)
ENV OBSERVER_DATA_DIR=/app/data/observer
ENV OBSERVER_LOG_DIR=/app/logs
ENV OBSERVER_SYSTEM_LOG_DIR=/app/logs/system
ENV OBSERVER_MAINTENANCE_LOG_DIR=/app/logs/maintenance
ENV OBSERVER_CONFIG_DIR=/app/config
ENV KIS_TOKEN_CACHE_DIR=/app/secrets/.kis_cache
ENV OBSERVER_ENV_FILE=/app/secrets/.env

# 보안: 비-root 사용자로 실행
RUN groupadd -r observer && useradd -r -g observer observer
RUN chown -R observer:observer /app
USER observer

# 헬스체크: 컨테이너 내부 127.0.0.1:8000/health 호출
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /bin/sh -c "python - <<'PY'\nimport sys\nimport urllib.request\nurl = 'http://127.0.0.1:8000/health'\ntry:\n    with urllib.request.urlopen(url, timeout=5) as resp:\n        sys.exit(0 if resp.getcode() == 200 else 1)\nexcept Exception:\n    sys.exit(1)\nPY"

# 포트 노출
EXPOSE 8000

# 기본 실행 명령
CMD ["python", "observer.py"]
