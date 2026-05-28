"""Liveness/readiness endpoint."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str = "ok"


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def get_health() -> HealthResponse:
    """Return a simple liveness signal.

    Kept intentionally dependency-free so it can answer even if downstream
    subsystems (once added) are degraded; use a future `/health/ready`
    endpoint for deeper readiness checks.
    """
    return HealthResponse(status="ok")
