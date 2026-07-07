"""Context Engine endpoints: project summary, context generation, statistics.

Exposes `orbit_context.ContextEngine` over HTTP. Returns structured JSON
only — no AI, planner, or provider logic lives here or in the engine it
calls; this is the context-gathering layer future planners/providers will
consume instead of calling `search`/`filesystem` tools directly.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from orbit_context import ContextEngineError
from pydantic import BaseModel

from orbit_api.core.dependencies import ContextEngineDep

router = APIRouter(prefix="/context", tags=["context"])


class WorkspaceInfoResponse(BaseModel):
    root: str
    file_count: int
    indexed_at: float | None


class ExtensionBreakdownResponse(BaseModel):
    extension: str
    file_count: int
    total_size: int


class ProjectStatsResponse(BaseModel):
    total_files: int
    total_size: int
    by_extension: list[ExtensionBreakdownResponse]


class ProjectSummaryResponse(BaseModel):
    workspace: WorkspaceInfoResponse
    stats: ProjectStatsResponse


class SearchMatchResponse(BaseModel):
    path: str
    line: int | None
    column: int | None
    text: str


class SelectedFileResponse(BaseModel):
    path: str
    size: int
    content: str | None
    truncated: bool


class ContextBundleResponse(BaseModel):
    workspace: WorkspaceInfoResponse
    stats: ProjectStatsResponse
    files: list[SelectedFileResponse]
    matches: list[SearchMatchResponse]
    query: str | None
    generated_at: float
    truncated: bool


class GenerateContextRequest(BaseModel):
    query: str | None = None
    paths: list[str] | None = None
    mode: str = "text"
    case_sensitive: bool = False
    extensions: list[str] | None = None
    directory: str | None = None
    max_results: int = 100


@router.get("/summary", response_model=ProjectSummaryResponse, summary="Get project summary")
async def project_summary(engine: ContextEngineDep) -> ProjectSummaryResponse:
    try:
        summary = await engine.project_summary()
    except ContextEngineError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return ProjectSummaryResponse(**summary.to_dict())


@router.get("/stats", response_model=ProjectStatsResponse, summary="Get workspace statistics")
async def workspace_stats(engine: ContextEngineDep) -> ProjectStatsResponse:
    try:
        stats = await engine.project_stats()
    except ContextEngineError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return ProjectStatsResponse(**stats.to_dict())


@router.post("/generate", response_model=ContextBundleResponse, summary="Generate a context bundle")
async def generate_context(
    body: GenerateContextRequest, engine: ContextEngineDep
) -> ContextBundleResponse:
    if not body.query and not body.paths:
        raise HTTPException(status_code=400, detail="Provide 'query' and/or 'paths'")
    try:
        bundle = await engine.build_context(
            query=body.query,
            paths=body.paths,
            mode=body.mode,
            case_sensitive=body.case_sensitive,
            extensions=body.extensions,
            directory=body.directory,
            max_results=body.max_results,
        )
    except ContextEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ContextBundleResponse(**bundle.to_dict())
