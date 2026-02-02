# Observer app image. Build context: repo root. Copies src/ into /app/src.
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY src /app/src

RUN mkdir -p /app/data/scalp /app/data/swing \
    && mkdir -p /app/logs/scalp /app/logs/swing /app/logs/system /app/logs/maintenance \
    && mkdir -p /app/config/scalp /app/config/swing /app/config/symbols /app/config/universe \
    && mkdir -p /app/secrets/.kis_cache

ENV OBSERVER_STANDALONE=1
ENV PYTHONPATH=/app/src
ENV TZ=Asia/Seoul
ENV OBSERVER_DATA_DIR=/app/data
ENV OBSERVER_LOG_DIR=/app/logs
ENV OBSERVER_SYSTEM_LOG_DIR=/app/logs/system
ENV OBSERVER_MAINTENANCE_LOG_DIR=/app/logs/maintenance
ENV OBSERVER_CONFIG_DIR=/app/config
ENV KIS_TOKEN_CACHE_DIR=/app/secrets/.kis_cache
ENV OBSERVER_ENV_FILE=/app/secrets/.env

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN groupadd -r observer && useradd -r -g observer observer
RUN chown -R observer:observer /app

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=2 \
    CMD ["python","-c","import urllib.request,sys; r=urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=3); sys.exit(0 if r.getcode()==200 else 1)"]

EXPOSE 8000
USER observer

CMD ["python", "-m", "observer"]
