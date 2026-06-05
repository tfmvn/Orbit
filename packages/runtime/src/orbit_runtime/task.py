"""Task model and lifecycle state machine.

A `Task` is the runtime's only unit of work. It carries a `name` (an opaque
string identifying what kind of work it represents) and a `payload` (an
opaque dict of arguments). The runtime never inspects either — that is left
entirely to whatever handler is registered for the task's name by a future
subsystem (tools, agents, planner, ...).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    """Lifecycle states a task can be in."""

    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Valid state transitions. Terminal states map to an empty set.
_ALLOWED_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.CREATED: frozenset({TaskStatus.QUEUED, TaskStatus.CANCELLED}),
    TaskStatus.QUEUED: frozenset({TaskStatus.RUNNING, TaskStatus.CANCELLED}),
    TaskStatus.RUNNING: frozenset({TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}),
    TaskStatus.COMPLETED: frozenset(),
    TaskStatus.FAILED: frozenset(),
    TaskStatus.CANCELLED: frozenset(),
}


class InvalidTransitionError(Exception):
    """Raised when a task's status is moved to a state it cannot reach."""

    def __init__(self, current: TaskStatus, target: TaskStatus) -> None:
        self.current = current
        self.target = target
        super().__init__(f"Cannot transition task from '{current.value}' to '{target.value}'")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Task:
    """A unit of work managed by the runtime.

    The runtime and worker only ever read/write `status`, `result`, `error`,
    `cancel_requested`, and `updated_at`. Everything about *what* the task
    does lives outside this object, in a handler looked up by `name`.
    """

    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: TaskStatus = TaskStatus.CREATED
    result: Any | None = None
    error: str | None = None
    cancel_requested: bool = False
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def transition_to(self, target: TaskStatus) -> None:
        """Move this task to `target`, validating the transition first."""
        allowed = _ALLOWED_TRANSITIONS[self.status]
        if target not in allowed:
            raise InvalidTransitionError(self.status, target)
        self.status = target
        self.updated_at = _utcnow()

    @property
    def is_terminal(self) -> bool:
        return not _ALLOWED_TRANSITIONS[self.status]
