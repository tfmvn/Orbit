"""Runtime: the single entry point future subsystems schedule work through.

The runtime does not know what kind of work a task performs — it only
creates, queues, and tracks tasks, and starts workers that execute them via
handlers registered with `register_handler`. Swapping the queue for a
Redis-backed one, or adding persistence, should never require changing this
class's public API.
"""

from __future__ import annotations

import asyncio
from typing import Any

from orbit_runtime.events import Event, EventBus, EventType
from orbit_runtime.handlers import HandlerRegistry, TaskHandler
from orbit_runtime.queue import InMemoryTaskQueue, TaskQueue
from orbit_runtime.store import TaskStore
from orbit_runtime.task import Task, TaskStatus
from orbit_runtime.worker import Worker


class TaskNotFoundError(Exception):
    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        super().__init__(f"No task with id '{task_id}'")


class Runtime:
    """Generic async execution runtime. No AI, planner, or tool logic."""

    def __init__(self, num_workers: int = 1, queue: TaskQueue | None = None) -> None:
        self._queue = queue or InMemoryTaskQueue()
        self._events = EventBus()
        self._tasks = TaskStore()
        self._handlers = HandlerRegistry()
        self._num_workers = num_workers
        self._worker_tasks: list[asyncio.Task[None]] = []
        self._stop_event = asyncio.Event()

    @property
    def events(self) -> EventBus:
        """Subscribe here to observe task lifecycle events."""
        return self._events

    def register_handler(self, name: str, handler: TaskHandler) -> None:
        """Register the callable that performs work for tasks named `name`."""
        self._handlers.register(name, handler)

    async def start(self) -> None:
        """Start the worker pool. Safe to call once per runtime instance."""
        self._stop_event.clear()
        for i in range(self._num_workers):
            worker = Worker(f"worker-{i}", self._queue, self._tasks, self._handlers, self._events)
            self._worker_tasks.append(asyncio.create_task(worker.run(self._stop_event)))

    async def stop(self) -> None:
        """Signal all workers to stop and wait for them to finish."""
        self._stop_event.set()
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()

    async def submit(self, name: str, payload: dict[str, Any] | None = None) -> Task:
        """Create a task and enqueue it for execution."""
        task = Task(name=name, payload=payload or {})
        self._tasks.save(task)
        await self._events.publish(Event(EventType.TASK_CREATED, task.id))

        task.transition_to(TaskStatus.QUEUED)
        self._tasks.save(task)
        await self._events.publish(Event(EventType.TASK_QUEUED, task.id))

        await self._queue.put(task.id)
        return task

    def get(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def list(self, status: TaskStatus | None = None) -> list[Task]:
        return self._tasks.list(status)

    async def cancel(self, task_id: str) -> Task:
        """Cancel a task.

        Tasks still `created`/`queued` are cancelled immediately. A `running`
        task is cooperatively cancelled: `cancel_requested` is set, and the
        worker finalizes the `cancelled` state once its handler returns.
        Terminal tasks are returned unchanged.
        """
        task = self._tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)

        if task.is_terminal:
            return task

        if task.status == TaskStatus.RUNNING:
            task.cancel_requested = True
            self._tasks.save(task)
            return task

        task.transition_to(TaskStatus.CANCELLED)
        self._tasks.save(task)
        await self._events.publish(Event(EventType.TASK_CANCELLED, task.id))
        return task
