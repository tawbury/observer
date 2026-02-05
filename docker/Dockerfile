# Stage 1: Builder
# Uses python:3.11-slim for minimal base image.
# Installs dependencies to be copied to the final stage.
FROM python:3.11-slim AS builder

# Set build-time environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install build dependencies if needed
# (Currently not mandatory as we use psycopg2-binary, but included for completeness)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install packages to a local directory for easy copying
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production
# Minimal runtime image
FROM python:3.11-slim

# Set runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Seoul \
    OBSERVER_STANDALONE=1 \
    PYTHONPATH=/app/src \
    OBSERVER_DATA_DIR=/opt/platform/runtime/observer/data \
    OBSERVER_LOG_DIR=/opt/platform/runtime/observer/logs \
    OBSERVER_SYSTEM_LOG_DIR=/opt/platform/runtime/observer/logs/system \
    OBSERVER_MAINTENANCE_LOG_DIR=/opt/platform/runtime/observer/logs/maintenance \
    OBSERVER_CONFIG_DIR=/opt/platform/runtime/observer/config \
    KIS_TOKEN_CACHE_DIR=/opt/platform/runtime/observer/data/cache

# Install runtime dependencies (tzdata for timezone support)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# Security: Create a non-root user with a specific UID/GID
# Using 1000:1000 as a standard non-privileged user.
RUN groupadd -g 1000 observer && \
    useradd -u 1000 -g observer -m -s /bin/bash observer

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /root/.local /home/observer/.local
# Update PATH to include the local bin directory
ENV PATH="/home/observer/.local/bin:${PATH}"

# Copy source code
# We copy to /app/src as per requirement
COPY src /app/src

# Setup PVC mount point permissions
# Note: Since this is often a mount point, we just ensure the parent directory
# has the correct ownership for the observer user.
RUN mkdir -p /opt/platform/runtime/observer && \
    chown -R observer:observer /app /opt/platform/runtime/observer /home/observer/.local

# Switch to non-root user
USER observer

# Healthcheck: Verifies the /health endpoint on port 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; \
    try: \
    res = urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5); \
    exit(0) if res.status == 200 else exit(1); \
    except: \
    exit(1)"

# Expose port (metadata only, K8s will use Service/Ingress)
EXPOSE 8000

# Execution Command
CMD ["python", "-m", "observer"]
