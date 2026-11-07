FROM node:24-bookworm-slim@sha256:0e0ff40c39bc087845bfb27465a0df4ea419520094bc35842ff83dd8cbe6f9b6 AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM ghcr.io/astral-sh/uv:0.9.17@sha256:5cb6b54d2bc3fe2eb9a8483db958a0b9eebf9edff68adedb369df8e7b98711a2 AS uv

FROM python:3.12.12-slim-bookworm@sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c AS dependencies
WORKDIR /app
ENV UV_PYTHON_DOWNLOADS=never UV_LINK_MODE=copy
COPY --from=uv /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
COPY backend/worldfork/ backend/worldfork/
RUN uv sync --locked --no-dev --no-editable

FROM dependencies AS checks
COPY backend/tests/ backend/tests/
COPY scripts/ scripts/
COPY evidence/ evidence/
RUN uv sync --locked --no-editable && \
    uv run --no-sync ruff check backend/worldfork backend/tests scripts && \
    uv run --no-sync pytest -q && \
    uv run --no-sync python scripts/verify_evidence.py evidence/pilot-manifest.json && \
    uv run --no-sync python scripts/evaluate_team.py --verify

FROM python:3.12.12-slim-bookworm@sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY --from=dependencies /app/.venv /app/.venv
COPY --from=frontend /build/dist frontend/dist
COPY backend/worldfork/ backend/worldfork/
COPY scripts/ scripts/
COPY evidence/ evidence/
USER 65532:65532
EXPOSE 8001
HEALTHCHECK --interval=10s --timeout=2s --start-period=15s CMD ["python", "-c", "from urllib.request import urlopen; urlopen('http://127.0.0.1:8001/api/health', timeout=1).close()"]
CMD ["python", "scripts/replay_server.py", "--host", "0.0.0.0"]
