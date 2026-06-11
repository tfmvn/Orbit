"""SystemInfoTool: returns basic host platform information. No arguments."""

from __future__ import annotations

import platform
from typing import Any

from orbit_tools.context import ToolContext
from orbit_tools.tool import Tool, ToolMetadata


class SystemInfoTool(Tool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="system_info",
            description="Returns basic host system information (OS, Python version).",
            parameters={"type": "object", "properties": {}},
        )

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> Any:
        return {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
        }
