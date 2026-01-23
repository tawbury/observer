FROM python:3.11-slim AS builder

# 빌드 스테이지: 의존성 설치
WORKDIR /build

# requirements.txt 복사 및 의존성 설치 (캐시 최적화)
# 빌드 컨텍스트: 리포지토리 루트 (따라서 app/obs_deploy/ 경로 사용)
COPY app/obs_deploy/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 런타임 스테이지: 최소 이미지
FROM python:3.11-slim

WORKDIR /app

# 빌더 스테이지에서 의존성 복사
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 애플리케이션 파일 복사 (소스는 app/obs_deploy/app/ 하위에 위치)
# 빌드 컨텍스트: 리포지토리 루트
COPY app/obs_deploy/app/observer.py /app/
COPY app/obs_deploy/app/paths.py /app/
COPY app/obs_deploy/app/src/ /app/src/
COPY app/obs_deploy/app/__init__.py /app/
COPY app/obs_deploy/app/__main__.py /app/

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

# 보안: 비-root 사용자 생성 (아직 USER는 root로 유지 - healthcheck와 CMD 실행용)
RUN groupadd -r observer && useradd -r -g observer observer
RUN chown -R observer:observer /app

# 헬스체크: 간단한 HTTP GET 요청
# Note: 컨테이너 시작 후 API 응답까지 약 10-20초 소요
# JSON 배열 형식 사용 (쉘 우회, syntax error 방지)
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=2 \
    CMD ["python","-c","import urllib.request,sys; r=urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=3); sys.exit(0 if r.getcode()==200 else 1)"]

# 포트 노출
EXPOSE 8000

# 비-root 사용자로 실행 (CMD/entrypoint 실행 시)
USER observer

# 기본 실행 명령
CMD ["python", "-m", "observer"]
