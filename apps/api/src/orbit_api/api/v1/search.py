"""Search and workspace-index endpoints.

`SearchTool` is invoked through `orbit_tools.ToolRegistry` like any other
tool (`POST /api/v1/tools/search/execute` also works), but index status and
refresh aren't single tool invocations — this router talks to the tool's
`WorkspaceIndex` directly, the same way `orbit_api.api.v1.process` talks to
`ProcessExecutionTool`'s `ExecutionStore` directly.

Generic and independent of any AI functionality — nothing here assumes a
particular future caller (planner, LLM provider, ...).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from orbit_tools import SearchTool, ToolContext
from pydantic import BaseModel

from orbit_api.core.dependencies import ToolRegistryDep

router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    query: str
    mode: str = "text"
    case_sensitive: bool = False
    extensions: list[str] | None = None
    directory: str | None = None
    max_results: int = 100


class SearchMatchResponse(BaseModel):
    path: str
    line: int | None
    column: int | None
    text: str


class SearchResponse(BaseModel):
    query: str
    mode: str
    matches: list[SearchMatchResponse]
    match_count: int
    files_searched: int
    search_duration: float


class IndexStatusResponse(BaseModel):
    root: str
    file_count: int
    built_at: float | None
    ignore_dirs: list[str]


def _get_search_tool(registry: ToolRegistryDep) -> SearchTool:
    tool = registry.get("search")
    if not isinstance(tool, SearchTool):
        raise HTTPException(status_code=500, detail="Search tool not registered")
    return tool


@router.post("", response_model=SearchResponse, summary="Search the workspace")
async def search(body: SearchRequest, registry: ToolRegistryDep) -> SearchResponse:
    tool = _get_search_tool(registry)
    result = await tool.run(body.model_dump(exclude_none=True), ToolContext())
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    output: dict[str, Any] = result.output
    return SearchResponse(**output)


@router.get("/index", response_model=IndexStatusResponse, summary="Get workspace index status")
async def index_status(registry: ToolRegistryDep) -> IndexStatusResponse:
    tool = _get_search_tool(registry)
    return IndexStatusResponse(**tool.index_status())


@router.post("/index/refresh", response_model=IndexStatusResponse, summary="Re-index the workspace")
async def refresh_index(registry: ToolRegistryDep) -> IndexStatusResponse:
    tool = _get_search_tool(registry)
    return IndexStatusResponse(**tool.refresh_index())
