"""orbit_tools — Orbit's model-agnostic tool framework.

Defines the `Tool` interface, a `ToolRegistry` to register/discover/invoke
tools by name, a reusable `ToolContext`, and a standardized `ToolResult`.
Independent from `orbit_runtime`, any AI provider, or a planner — those are
future callers of this package, never dependencies of it.

Only lightweight demonstration tools (`EchoTool`, `TimeTool`,
`SystemInfoTool`) are included here to prove the architecture. Real
capability tools (shell, filesystem, git, browser, ...) belong to later
phases.
"""

from orbit_tools.builtin import EchoTool, SystemInfoTool, TimeTool
from orbit_tools.context import ToolContext
from orbit_tools.registry import ToolAlreadyRegisteredError, ToolNotFoundError, ToolRegistry
from orbit_tools.result import ToolResult
from orbit_tools.tool import Tool, ToolError, ToolMetadata

__version__ = "0.2.0"

__all__ = [
    "Tool",
    "ToolMetadata",
    "ToolError",
    "ToolContext",
    "ToolResult",
    "ToolRegistry",
    "ToolNotFoundError",
    "ToolAlreadyRegisteredError",
    "EchoTool",
    "TimeTool",
    "SystemInfoTool",
    "__version__",
]
