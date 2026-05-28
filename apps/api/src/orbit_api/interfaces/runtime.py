"""Contract for the future agent execution runtime.

The implementation will live in `packages/runtime`. It is responsible for
scheduling and executing long-lived agent jobs — not implemented here.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Runtime(Protocol):
    """Coordinates the lifecycle of agent jobs.

    A concrete implementation will own job scheduling, cancellation, and
    status tracking. Intentionally left unimplemented in this phase.
    """

    async def start_job(self, job_id: str) -> None:
        """Start executing a previously submitted job."""
        ...

    async def cancel_job(self, job_id: str) -> None:
        """Request cancellation of a running job."""
        ...

    async def get_job_status(self, job_id: str) -> str:
        """Return the current status of a job."""
        ...
