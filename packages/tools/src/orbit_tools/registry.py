"""Registry mapping tool names to `Tool` instances.

Mirrors `orbit_runtime.HandlerRegistry`'s "register once, look up by name"
shape. The runtime (and any future agent/planner layer) should never
instantiate a tool directly — it looks one up here by name instead.
"""

from __future__ import annotations

from typing import Any

from orbit_tools.context import ToolContext
from orbit_tools.result import ToolResult
from orbit_tools.tool import Tool, ToolMetadata


class ToolNotFoundError(Exception):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"No tool registered with name '{name}'")


class ToolAlreadyRegisteredError(Exception):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"A tool named '{name}' is already registered")


class ToolRegistry:
    """Registers, discovers, and invokes tools by name."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool, *, replace: bool = False) -> None:
        """Register `tool` under its `metadata.name`.

        Raises `ToolAlreadyRegisteredError` unless `replace=True`.
        """
        name = tool.metadata.name
        if not replace and name in self._tools:
            raise ToolAlreadyRegisteredError(name)
        self._tools[name] = tool

    def unregister(self, name: str) -> None:
        """Remove a tool by name. No-op if it isn't registered."""
        self._tools.pop(name, None)

    def get(self, name: str) -> Tool | None:
        """Look up a tool by name, or `None` if unregistered."""
        return self._tools.get(name)

    def list(self) -> list[ToolMetadata]:
        """Discover all registered tools' metadata."""
        return [tool.metadata for tool in self._tools.values()]

    async def invoke(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        context: ToolContext | None = None,
    ) -> ToolResult:
        """Look up `name` and run it, raising `ToolNotFoundError` if missing."""
        tool = self._tools.get(name)
        if tool is None:
            raise ToolNotFoundError(name)
        return await tool.run(arguments or {}, context or ToolContext())
