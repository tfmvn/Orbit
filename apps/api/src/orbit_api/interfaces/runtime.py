"""Contract for the future agent-job orchestration layer.

This is a higher-level, agent-specific contract than `orbit_runtime.Runtime`
(implemented in `packages/runtime`). The generic engine schedules opaque
tasks; a future agent layer will likely be built on top of it and expose
this narrower "job" surface — not implemented here.
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
