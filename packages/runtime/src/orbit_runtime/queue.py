"""Task queue abstraction.

`TaskQueue` defines the only contract the runtime relies on. `InMemoryTaskQueue`
is the Phase 1 implementation; a Redis-backed (or other) queue can later
implement the same interface and be swapped in without touching `Runtime` or
`Worker`.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod


class TaskQueue(ABC):
    """Contract for a FIFO queue of task IDs."""

    @abstractmethod
    async def put(self, task_id: str) -> None:
        """Enqueue a task ID for a worker to pick up."""

    @abstractmethod
    async def get(self) -> str:
        """Block until a task ID is available, then return it."""

    @abstractmethod
    def qsize(self) -> int:
        """Return the current number of queued task IDs."""


class InMemoryTaskQueue(TaskQueue):
    """Asyncio-backed, single-process queue. Not persisted across restarts."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[str] = asyncio.Queue()

    async def put(self, task_id: str) -> None:
        await self._queue.put(task_id)

    async def get(self) -> str:
        return await self._queue.get()

    def qsize(self) -> int:
        return self._queue.qsize()
