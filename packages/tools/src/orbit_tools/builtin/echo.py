"""EchoTool: returns whatever message it was given.

Simplest possible tool — proves argument validation and the execute/result
round-trip work.
"""

from __future__ import annotations

from typing import Any

from orbit_tools.context import ToolContext
from orbit_tools.tool import Tool, ToolMetadata


class EchoTool(Tool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="echo",
            description="Echoes back the provided message.",
            parameters={
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"],
            },
        )

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> Any:
        return {"echo": arguments["message"]}
