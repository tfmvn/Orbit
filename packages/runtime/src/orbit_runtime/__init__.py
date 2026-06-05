"""orbit_runtime — the generic async execution engine for Orbit.

This package is intentionally independent from any LLM, planner, memory
system, or tool implementation. It knows how to run tasks; it has no idea
what a task does. Future subsystems depend on this package and register
handlers with a `Runtime` instance — this package never depends on them.
"""

from orbit_runtime.events import Event, EventBus, EventType
from orbit_runtime.handlers import HandlerNotFoundError, HandlerRegistry, TaskHandler
from orbit_runtime.queue import InMemoryTaskQueue, TaskQueue
from orbit_runtime.runtime import Runtime, TaskNotFoundError
from orbit_runtime.task import InvalidTransitionError, Task, TaskStatus

__version__ = "0.2.0"

__all__ = [
    "Runtime",
    "Task",
    "TaskStatus",
    "TaskHandler",
    "HandlerRegistry",
    "HandlerNotFoundError",
    "TaskQueue",
    "InMemoryTaskQueue",
    "Event",
    "EventBus",
    "EventType",
    "InvalidTransitionError",
    "TaskNotFoundError",
    "__version__",
]
