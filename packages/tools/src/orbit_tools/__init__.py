"""orbit_tools — Orbit's model-agnostic tool framework.

Defines the `Tool` interface, a `ToolRegistry` to register/discover/invoke
tools by name, a reusable `ToolContext`, and a standardized `ToolResult`.
Independent from `orbit_runtime`, any AI provider, or a planner — those are
future callers of this package, never dependencies of it.

`EchoTool`, `TimeTool`, and `SystemInfoTool` are lightweight demonstration
tools that prove the architecture works. `FilesystemTool` is Orbit's first
real capability tool — sandboxed file/directory access scoped to a
configurable workspace root (see `orbit_tools.filesystem.WorkspaceGuard`).
`SearchTool` is Orbit's first code-intelligence capability: non-semantic
filename/full-text/regex search backed by `WorkspaceIndex` (see
`orbit_tools.search`). Remaining capability tools (shell, git, browser,
...) and semantic/embeddings-based search belong to later phases.
"""

from orbit_tools.builtin import EchoTool, SystemInfoTool, TimeTool
from orbit_tools.context import ToolContext
from orbit_tools.filesystem import FilesystemTool, WorkspaceError, WorkspaceGuard
from orbit_tools.process import ExecutionRecord, ExecutionStore, ProcessExecutionTool
from orbit_tools.registry import ToolAlreadyRegisteredError, ToolNotFoundError, ToolRegistry
from orbit_tools.result import ToolResult
from orbit_tools.search import IndexedFile, SearchMatch, SearchTool, WorkspaceIndex
from orbit_tools.tool import Tool, ToolError, ToolMetadata

__version__ = "0.5.0"

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
    "FilesystemTool",
    "WorkspaceGuard",
    "WorkspaceError",
    "ProcessExecutionTool",
    "ExecutionStore",
    "ExecutionRecord",
    "SearchTool",
    "WorkspaceIndex",
    "IndexedFile",
    "SearchMatch",
    "__version__",
]
