# Multi-stage Dockerfile for ducku
# Build stage
FROM python:3.13-slim-bookworm AS builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/
COPY bin/ ./bin/
COPY config/ ./config/

# Install build tools and build the package
RUN pip install build wheel && \
    python -m build

# Runtime stage
FROM python:3.13-slim-bookworm AS runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user
RUN groupadd --gid 1000 ducku && \
    useradd --uid 1000 --gid ducku --shell /bin/bash --create-home ducku

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy built wheel from builder stage
COPY --from=builder /app/dist/*.whl /tmp/

# Install the package
RUN pip install /tmp/*.whl && \
    rm /tmp/*.whl

# Switch to non-root user
USER ducku

# Set working directory for analysis
WORKDIR /workspace

# Set default command
ENTRYPOINT ["ducku"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ducku --help > /dev/null || exit 1

# Labels
LABEL org.opencontainers.image.title="Ducku" \
      org.opencontainers.image.description="Documentation analysis and code quality tool" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.authors="duckuio" \
      org.opencontainers.image.url="https://github.com/duckuio/ducku_cli" \
      org.opencontainers.image.source="https://github.com/duckuio/ducku_cli" \
      org.opencontainers.image.licenses="MIT"
