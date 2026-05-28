"""Service version metadata endpoint."""

from __future__ import annotations

import os

from fastapi import APIRouter
from pydantic import BaseModel

from orbit_api import __version__
from orbit_api.core.dependencies import SettingsDep

router = APIRouter(tags=["version"])


class VersionResponse(BaseModel):
    name: str
    version: str
    environment: str
    git_commit: str | None = None


@router.get("/version", response_model=VersionResponse, summary="Service version")
async def get_version(settings: SettingsDep) -> VersionResponse:
    """Return service name, version, environment, and git commit if known."""
    return VersionResponse(
        name=settings.app_name,
        version=__version__,
        environment=settings.environment,
        git_commit=os.getenv("ORBIT_GIT_COMMIT"),
    )
