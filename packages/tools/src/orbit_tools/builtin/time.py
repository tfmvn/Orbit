"""TimeTool: returns the current UTC time. Takes no arguments."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from orbit_tools.context import ToolContext
from orbit_tools.tool import Tool, ToolMetadata


class TimeTool(Tool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="time",
            description="Returns the current UTC time.",
            parameters={"type": "object", "properties": {}},
        )

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> Any:
        return {"utc": datetime.now(timezone.utc).isoformat()}
