"""Contract for the future tool-execution subsystem.

The implementation will live in `packages/tools`. It is responsible for
registering and invoking tools available to agents — not implemented here.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ToolProvider(Protocol):
    """Registers and executes tools available to agents.

    Intentionally left unimplemented in this phase.
    """

    async def list_tools(self) -> list[str]:
        """Return the names of all registered tools."""
        ...

    async def invoke_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Invoke a registered tool by name with the given arguments."""
        ...
