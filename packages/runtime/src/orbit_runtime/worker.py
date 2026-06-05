"""Worker: pulls queued task IDs and drives them through their lifecycle.

The worker contains no AI logic and no knowledge of what a task's `name`
means. It only: looks up the task, transitions its state, invokes whatever
handler is registered for its name, and emits events. All AI/tool/agent
logic lives in handlers registered by future subsystems.
"""

from __future__ import annotations

import asyncio

from orbit_runtime.events import Event, EventBus, EventType
from orbit_runtime.handlers import HandlerNotFoundError, HandlerRegistry
from orbit_runtime.queue import TaskQueue
from orbit_runtime.store import TaskStore
from orbit_runtime.task import TaskStatus

# How often the run loop wakes up to check for a stop request while the
# queue is empty.
_POLL_INTERVAL_SECONDS = 0.5


class Worker:
    """Consumes task IDs from a queue and executes them one at a time."""

    def __init__(
        self,
        worker_id: str,
        queue: TaskQueue,
        tasks: TaskStore,
        handlers: HandlerRegistry,
        events: EventBus,
    ) -> None:
        self.worker_id = worker_id
        self._queue = queue
        self._tasks = tasks
        self._handlers = handlers
        self._events = events

    async def run(self, stop_event: asyncio.Event) -> None:
        """Process tasks until `stop_event` is set."""
        while not stop_event.is_set():
            try:
                task_id = await asyncio.wait_for(self._queue.get(), timeout=_POLL_INTERVAL_SECONDS)
            except asyncio.TimeoutError:
                continue
            await self._process(task_id)

    async def _process(self, task_id: str) -> None:
        task = self._tasks.get(task_id)
        if task is None:
            return
        if task.status != TaskStatus.QUEUED:
            # Already cancelled (or otherwise moved) while it sat in the queue.
            return

        task.transition_to(TaskStatus.RUNNING)
        self._tasks.save(task)
        await self._events.publish(Event(EventType.TASK_STARTED, task.id))

        try:
            handler = self._handlers.get(task.name)
            if handler is None:
                raise HandlerNotFoundError(task.name)
            result = await handler(task)
        except Exception as exc:  # noqa: BLE001 - task failure is data, not a crash
            task.error = str(exc)
            task.transition_to(TaskStatus.FAILED)
            self._tasks.save(task)
            await self._events.publish(Event(EventType.TASK_FAILED, task.id, {"error": task.error}))
            return

        if task.cancel_requested:
            task.transition_to(TaskStatus.CANCELLED)
            self._tasks.save(task)
            await self._events.publish(Event(EventType.TASK_CANCELLED, task.id))
            return

        task.result = result
        task.transition_to(TaskStatus.COMPLETED)
        self._tasks.save(task)
        await self._events.publish(Event(EventType.TASK_COMPLETED, task.id, {"result": result}))
