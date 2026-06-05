"""Registry mapping a task's `name` to the callable that performs the work.

The runtime deliberately has no built-in handlers. Future subsystems (tools,
agents, planner) register their own handlers by name; the runtime and worker
never know what a handler does.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from orbit_runtime.task import Task

TaskHandler = Callable[[Task], Awaitable[Any]]


class HandlerNotFoundError(Exception):
    """Raised when a task names a handler that was never registered."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"No handler registered for task type '{name}'")


class HandlerRegistry:
    """Simple name -> handler map."""

    def __init__(self) -> None:
        self._handlers: dict[str, TaskHandler] = {}

    def register(self, name: str, handler: TaskHandler) -> None:
        self._handlers[name] = handler

    def get(self, name: str) -> TaskHandler | None:
        return self._handlers.get(name)
