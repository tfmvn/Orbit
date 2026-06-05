# Build context for this Dockerfile is the monorepo root (see
# docker/docker-compose.yml), since the API depends on the local
# packages/runtime package.

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /repo

COPY packages/runtime ./packages/runtime
COPY apps/api/pyproject.toml ./apps/api/pyproject.toml
COPY apps/api/src ./apps/api/src

RUN pip install --upgrade pip \
    && pip install ./packages/runtime \
    && pip install ./apps/api

EXPOSE 8000

CMD ["uvicorn", "orbit_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
