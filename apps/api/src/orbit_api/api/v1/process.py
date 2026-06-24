"""Process execution endpoints: execute, status, result, cancel.

`ProcessExecutionTool` is invoked through `orbit_tools.ToolRegistry` like any
other tool (see `tools.py` for the generic `/api/v1/tools/{name}/execute`
path), but because a process execution outlives that single call, this
router talks to the tool's `ExecutionStore` directly for status/result/
cancel — no registry changes were needed for that.

Generic and independent of any AI functionality; nothing here assumes a
particular future caller (git, python, build tools, ...).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from orbit_tools import ProcessExecutionTool, ToolContext
from pydantic import BaseModel, Field

from orbit_api.core.dependencies import ToolRegistryDep

router = APIRouter(prefix="/process", tags=["process"])


class ExecuteProcessRequest(BaseModel):
    command: list[str]
    cwd: str = "."
    env: dict[str, str] = Field(default_factory=dict)
    timeout: float = 30.0


class ProcessStatusResponse(BaseModel):
    id: str
    command: list[str]
    cwd: str
    status: str
    pid: int | None
    started_at: float
    duration: float | None


class ProcessResultResponse(ProcessStatusResponse):
    stdout: str
    stderr: str
    exit_code: int | None


def _get_process_tool(registry: ToolRegistryDep) -> ProcessExecutionTool:
    tool = registry.get("process_execute")
    if not isinstance(tool, ProcessExecutionTool):
        raise HTTPException(status_code=500, detail="Process execution tool not registered")
    return tool


@router.post("/execute", response_model=ProcessStatusResponse, summary="Start a command execution")
async def execute_process(
    body: ExecuteProcessRequest, registry: ToolRegistryDep
) -> ProcessStatusResponse:
    tool = _get_process_tool(registry)
    result = await tool.run(body.model_dump(), ToolContext())
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    record = tool.get_status(result.output["execution_id"])
    assert record is not None  # just created above
    return ProcessStatusResponse(**record.to_status_dict())


@router.get("/{execution_id}/status", response_model=ProcessStatusResponse, summary="Get execution status")
async def get_execution_status(execution_id: str, registry: ToolRegistryDep) -> ProcessStatusResponse:
    tool = _get_process_tool(registry)
    record = tool.get_status(execution_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return ProcessStatusResponse(**record.to_status_dict())


@router.get("/{execution_id}/result", response_model=ProcessResultResponse, summary="Get execution result")
async def get_execution_result(execution_id: str, registry: ToolRegistryDep) -> ProcessResultResponse:
    tool = _get_process_tool(registry)
    record = tool.get_result(execution_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return ProcessResultResponse(**record.to_result_dict())


@router.post("/{execution_id}/cancel", response_model=ProcessStatusResponse, summary="Cancel a running execution")
async def cancel_execution(execution_id: str, registry: ToolRegistryDep) -> ProcessStatusResponse:
    tool = _get_process_tool(registry)
    if tool.get_status(execution_id) is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    if not tool.cancel(execution_id):
        raise HTTPException(status_code=409, detail="Execution already finished")
    record = tool.get_status(execution_id)
    assert record is not None
    return ProcessStatusResponse(**record.to_status_dict())
