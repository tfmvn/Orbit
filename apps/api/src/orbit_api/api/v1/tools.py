"""Tool endpoints: list, get metadata, execute.

These expose `orbit_tools.ToolRegistry` over HTTP. Only the built-in demo
tools (echo, time, system_info) are registered in this phase — no AI or
agent endpoints live here.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from orbit_tools import ToolNotFoundError
from pydantic import BaseModel, Field

from orbit_api.core.dependencies import ToolRegistryDep

router = APIRouter(prefix="/tools", tags=["tools"])


class ToolMetadataResponse(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]
    version: str


class ToolResultResponse(BaseModel):
    success: bool
    output: Any | None
    error: str | None
    execution_time: float
    metadata: dict[str, Any]


class ExecuteToolRequest(BaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)


@router.get("", response_model=list[ToolMetadataResponse], summary="List available tools")
async def list_tools(registry: ToolRegistryDep) -> list[ToolMetadataResponse]:
    return [ToolMetadataResponse(**meta.__dict__) for meta in registry.list()]


@router.get("/{name}", response_model=ToolMetadataResponse, summary="Get tool metadata")
async def get_tool(name: str, registry: ToolRegistryDep) -> ToolMetadataResponse:
    tool = registry.get(name)
    if tool is None:
        raise HTTPException(status_code=404, detail="Tool not found")
    return ToolMetadataResponse(**tool.metadata.__dict__)


@router.post("/{name}/execute", response_model=ToolResultResponse, summary="Execute a tool")
async def execute_tool(
    name: str, body: ExecuteToolRequest, registry: ToolRegistryDep
) -> ToolResultResponse:
    try:
        result = await registry.invoke(name, body.arguments)
    except ToolNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Tool not found") from exc
    return ToolResultResponse(**result.to_dict())
