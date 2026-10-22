# Unified Multi-Stage Production Dockerfile for HeatSense
# Stage 1: Build React + TypeScript Frontend SPA
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend Dependency Resolution
FROM python:3.12-slim AS backend-builder

WORKDIR /build

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .python-version ./

RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip install -e .

# Stage 3: Hardened Runtime Container
FROM python:3.12-slim AS runtime

WORKDIR /app

# Create unprivileged non-root user
RUN groupadd -g 10001 heatsense && \
    useradd -u 10001 -g heatsense -m -s /bin/bash heatsense

COPY --from=backend-builder /opt/venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend source, ml models, data, and static frontend build
COPY --chown=heatsense:heatsense backend/ backend/
COPY --chown=heatsense:heatsense ml/ ml/
COPY --chown=heatsense:heatsense data/ data/
COPY --chown=heatsense:heatsense artifacts/ artifacts/
COPY --chown=heatsense:heatsense --from=frontend-builder /app/frontend/dist /app/frontend_dist
COPY --chown=heatsense:heatsense pyproject.toml .python-version ./

RUN pip install --no-deps -e .

USER heatsense

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "heatsense_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
