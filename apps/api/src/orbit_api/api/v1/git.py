"""Git Workspace endpoints: repository status, branch, commit history, diff.

`GitTool` is invoked through `orbit_tools.ToolRegistry` like any other tool
(`POST /api/v1/tools/git/execute` also works); this router exposes the same
read-only operations under more specific, generic paths, the same way
`orbit_api.api.v1.search` sits alongside the generic `/tools` endpoint.

Nothing here mutates a repository — every route maps to a non-mutating
`GitTool` operation. Generic and independent of any AI functionality;
nothing here assumes a particular future caller (planner, LLM provider,
...).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from orbit_tools import GitTool, ToolContext
from pydantic import BaseModel

from orbit_api.core.dependencies import ToolRegistryDep

router = APIRouter(prefix="/git", tags=["git"])


class GitStatusResponse(BaseModel):
    staged: list[str]
    modified: list[str]
    untracked: list[str]
    ignored: list[str]
    clean: bool


class GitBranchResponse(BaseModel):
    branch: str | None
    detached: bool
    head_commit: str | None


class GitCommitResponse(BaseModel):
    commit: str
    short_commit: str
    author_name: str
    author_email: str
    date: str
    subject: str


class GitLogResponse(BaseModel):
    commits: list[GitCommitResponse]
    count: int


class GitDiffFileResponse(BaseModel):
    path: str
    added: int | None
    removed: int | None
    binary: bool


class GitDiffSummaryResponse(BaseModel):
    staged: bool
    files: list[GitDiffFileResponse]
    files_changed: int
    total_added: int
    total_removed: int


class GitMetadataResponse(BaseModel):
    root: str
    branch: str | None
    detached: bool
    head_commit: str | None
    clean: bool
    remotes: dict[str, str]


def _get_git_tool(registry: ToolRegistryDep) -> GitTool:
    tool = registry.get("git")
    if not isinstance(tool, GitTool):
        raise HTTPException(status_code=500, detail="Git tool not registered")
    return tool


async def _run(tool: GitTool, **arguments: Any) -> dict[str, Any]:
    result = await tool.run(arguments, ToolContext())
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return result.output


@router.get("/status", response_model=GitStatusResponse, summary="Get repository status")
async def status(
    registry: ToolRegistryDep, path: str = Query(default=".")
) -> GitStatusResponse:
    tool = _get_git_tool(registry)
    output = await _run(tool, operation="status", path=path)
    return GitStatusResponse(**output)


@router.get("/branch", response_model=GitBranchResponse, summary="Get current branch")
async def branch(
    registry: ToolRegistryDep, path: str = Query(default=".")
) -> GitBranchResponse:
    tool = _get_git_tool(registry)
    output = await _run(tool, operation="branch", path=path)
    return GitBranchResponse(**output)


@router.get("/log", response_model=GitLogResponse, summary="Get recent commit history")
async def log(
    registry: ToolRegistryDep, path: str = Query(default="."), limit: int = Query(default=20)
) -> GitLogResponse:
    tool = _get_git_tool(registry)
    output = await _run(tool, operation="log", path=path, limit=limit)
    return GitLogResponse(**output)


@router.get("/diff", response_model=GitDiffSummaryResponse, summary="Get diff summary")
async def diff(
    registry: ToolRegistryDep,
    path: str = Query(default="."),
    staged: bool = Query(default=False),
) -> GitDiffSummaryResponse:
    tool = _get_git_tool(registry)
    output = await _run(tool, operation="diff", path=path, staged=staged)
    return GitDiffSummaryResponse(**output)


@router.get("/metadata", response_model=GitMetadataResponse, summary="Get repository metadata")
async def metadata(
    registry: ToolRegistryDep, path: str = Query(default=".")
) -> GitMetadataResponse:
    tool = _get_git_tool(registry)
    output = await _run(tool, operation="metadata", path=path)
    return GitMetadataResponse(**output)
