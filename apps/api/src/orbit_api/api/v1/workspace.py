"""Workspace endpoint: reports the sandboxed root the filesystem tool uses.

Generic and independent of any AI functionality — it only describes where
filesystem operations (`/api/v1/tools/filesystem/execute`) are scoped to.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from orbit_api.core.dependencies import WorkspaceRootDep

router = APIRouter(prefix="/workspace", tags=["workspace"])


class WorkspaceInfoResponse(BaseModel):
    root: str
    exists: bool


@router.get("", response_model=WorkspaceInfoResponse, summary="Get workspace root info")
async def get_workspace_info(root: WorkspaceRootDep) -> WorkspaceInfoResponse:
    return WorkspaceInfoResponse(root=str(root), exists=root.exists())
