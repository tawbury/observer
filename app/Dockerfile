FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy essential files for Observer deployment
COPY observer.py /app/
COPY paths.py /app/
COPY src/ /app/src/

# Create required directories
RUN mkdir -p /app/data/observer \
    && mkdir -p /app/logs \
    && mkdir -p /app/config

# Set environment variables for standalone mode
ENV QTS_OBSERVER_STANDALONE=1
ENV PYTHONPATH=/app/src:/app
ENV OBSERVER_DATA_DIR=/app/data/observer
ENV OBSERVER_LOG_DIR=/app/logs

# Create non-root user for security
RUN groupadd -r qts && useradd -r -g qts qts
RUN chown -R qts:qts /app
USER qts

# Health check endpoint (if implemented in future)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Expose port for future web interface
EXPOSE 8000

# Default command
CMD ["python", "observer.py"]
