"""In-memory tracking of process executions.

Unlike other tools, a process execution outlives the single `Tool.run` call
that starts it — the caller polls status/result separately, and may cancel
it, while it runs in the background. `ExecutionStore` is the shared state
that makes that possible; it holds no subprocess logic itself (see
`executor.py`).
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

ExecutionStatus = Literal["running", "completed", "failed", "timeout", "cancelled"]


@dataclass
class ExecutionRecord:
    """State of a single tracked process execution."""

    id: str
    command: list[str]
    cwd: str
    status: ExecutionStatus = "running"
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    pid: int | None = None
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None

    @property
    def duration(self) -> float | None:
        """Seconds elapsed so far (running) or total (finished)."""
        end = self.finished_at if self.finished_at is not None else time.time()
        return end - self.started_at

    def to_status_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "command": self.command,
            "cwd": self.cwd,
            "status": self.status,
            "pid": self.pid,
            "started_at": self.started_at,
            "duration": self.duration,
        }

    def to_result_dict(self) -> dict[str, Any]:
        return {
            **self.to_status_dict(),
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
        }


class ExecutionStore:
    """Process-local registry of `ExecutionRecord`s, keyed by execution id.

    Deliberately simple (a dict behind no lock — CPython's single-threaded
    event loop makes read/replace of a dict entry atomic enough here).
    Future streaming can extend `ExecutionRecord` with a subscriber list
    without changing this store's shape.
    """

    def __init__(self) -> None:
        self._records: dict[str, ExecutionRecord] = {}

    def create(self, command: list[str], cwd: str) -> ExecutionRecord:
        record = ExecutionRecord(id=uuid.uuid4().hex, command=command, cwd=cwd)
        self._records[record.id] = record
        return record

    def get(self, execution_id: str) -> ExecutionRecord | None:
        return self._records.get(execution_id)

    def list(self) -> list[ExecutionRecord]:
        return list(self._records.values())
