"""Lightweight demonstration tools proving the tool architecture works.

These exist to exercise `Tool`, `ToolRegistry`, `ToolContext`, and
`ToolResult` end-to-end. They are intentionally trivial — real capability
tools (shell, filesystem, git, browser, ...) belong to later phases.
"""

from orbit_tools.builtin.echo import EchoTool
from orbit_tools.builtin.system_info import SystemInfoTool
from orbit_tools.builtin.time import TimeTool

__all__ = ["EchoTool", "SystemInfoTool", "TimeTool"]
