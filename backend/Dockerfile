# Multi-stage build for GraphSentinel
# Stage 1: Dependencies
FROM python:3.13-slim AS deps

WORKDIR /build

# Install pip tools first for better caching
RUN pip install --no-cache-dir --upgrade pip pip-tools

# Copy only dependency files first for layer caching
COPY requirements.txt .
RUN pip-compile requirements.txt --output-file requirements-lock.txt || \
    cp requirements.txt requirements-lock.txt

# Stage 2: Builder (only if we need to build anything)
FROM python:3.13-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY --from=deps /build/requirements-lock.txt .
RUN pip install --no-cache-dir -r requirements-lock.txt

# Stage 3: Production runtime
FROM python:3.13-slim AS production

# Security: Create non-root user
RUN groupadd --gid 1001 --system graphsentinel && \
    useradd --uid 1001 --system --gid graphsentinel graphsentinel

WORKDIR /app

# Copy installed Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy only required files from source
COPY app/ ./app/
COPY config/ ./config/
COPY data/ ./data/
COPY demo_cache/ ./demo_cache/

# Create necessary directories
RUN mkdir -p /app/logs /app/cache && \
    chown -R graphsentinel:graphsentinel /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Switch to non-root user
USER 1001:1001

# Expose port
EXPOSE 8000

# Health check (use python instead of curl which is not installed)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

# Stage 4: Development (optional)
FROM production AS development

# Install development dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    curl \
    && rm -rf /var/lib/apt/lists/*
USER 1001:1001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]