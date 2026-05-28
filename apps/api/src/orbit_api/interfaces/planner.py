"""Contract for the future task-planning subsystem.

The implementation will live in `packages/planner`. It is responsible for
turning a high-level goal into a sequence of executable steps — not
implemented here.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Planner(Protocol):
    """Produces an executable plan from a goal.

    Intentionally left unimplemented in this phase.
    """

    async def create_plan(self, goal: str, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Return an ordered list of steps that accomplish `goal`."""
        ...
