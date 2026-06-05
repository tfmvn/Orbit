"""Task endpoints: submit, get, list, cancel.

These expose the generic `orbit_runtime.Runtime` over HTTP. They know
nothing about what a task's `name` means — the runtime doesn't either. No AI
endpoints live here.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from orbit_runtime import Task, TaskNotFoundError, TaskStatus
from pydantic import BaseModel, Field

from orbit_api.core.dependencies import RuntimeDep

router = APIRouter(prefix="/tasks", tags=["tasks"])


class SubmitTaskRequest(BaseModel):
    name: str = Field(
        ..., description="Identifies the kind of work to perform. Opaque to the runtime."
    )
    payload: dict[str, Any] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    id: str
    name: str
    status: TaskStatus
    payload: dict[str, Any]
    result: Any | None
    error: str | None
    created_at: str
    updated_at: str

    @classmethod
    def from_task(cls, task: Task) -> TaskResponse:
        return cls(
            id=task.id,
            name=task.name,
            status=task.status,
            payload=task.payload,
            result=task.result,
            error=task.error,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
        )


@router.post("", response_model=TaskResponse, status_code=201, summary="Submit a task")
async def submit_task(body: SubmitTaskRequest, runtime: RuntimeDep) -> TaskResponse:
    task = await runtime.submit(body.name, body.payload)
    return TaskResponse.from_task(task)


@router.get("", response_model=list[TaskResponse], summary="List tasks")
async def list_tasks(runtime: RuntimeDep, status: TaskStatus | None = None) -> list[TaskResponse]:
    return [TaskResponse.from_task(t) for t in runtime.list(status)]


@router.get("/{task_id}", response_model=TaskResponse, summary="Get a task")
async def get_task(task_id: str, runtime: RuntimeDep) -> TaskResponse:
    task = runtime.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse.from_task(task)


@router.post("/{task_id}/cancel", response_model=TaskResponse, summary="Cancel a task")
async def cancel_task(task_id: str, runtime: RuntimeDep) -> TaskResponse:
    try:
        task = await runtime.cancel(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
    return TaskResponse.from_task(task)
