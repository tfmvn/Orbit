"""In-memory storage for task state.

Kept separate from `Runtime` so the storage mechanism can be swapped (e.g.
for a persistent store) without changing how the runtime schedules work.
"""

from __future__ import annotations

from orbit_runtime.task import Task, TaskStatus


class TaskStore:
    """Process-local task registry, keyed by task ID."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def save(self, task: Task) -> None:
        self._tasks[task.id] = task

    def get(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def list(self, status: TaskStatus | None = None) -> list[Task]:
        tasks = list(self._tasks.values())
        if status is not None:
            tasks = [t for t in tasks if t.status == status]
        return sorted(tasks, key=lambda t: t.created_at)
