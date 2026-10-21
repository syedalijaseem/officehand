# syntax=docker/dockerfile:1.7

# --- Frontend build ---------------------------------------------------------------------------
FROM node:24.22-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npx ng build

# --- Backend dependencies ---------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS backend-deps
COPY --from=ghcr.io/astral-sh/uv:0.12.1 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/app/.venv
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# --- Runtime ----------------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime
RUN groupadd --system --gid 10001 app && useradd --system --uid 10001 --gid app --no-create-home app \
    && mkdir -p /data && chown app:app /data
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data \
    FRONTEND_DIST=/app/static \
    SAMPLE_DATA_DIR=/app/sample_data \
    ENV=prod
COPY --from=backend-deps /app/.venv /app/.venv
COPY backend/app ./app
COPY sample_data ./sample_data
COPY --from=frontend /build/dist/frontend/browser ./static
USER app
EXPOSE 8000
# One worker: embedded Chroma and in-memory rate limits require a single process (ARCHITECTURE §7).
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers", "--no-server-header"]
