"""orbit_context — Orbit's Context Engine.

Gathers and structures workspace context (project summaries, relevant
files, file contents, statistics) from the existing `search` and
`filesystem` tools, via `orbit_tools.ToolRegistry`. No AI, planner, or
memory logic lives here — this package is a future dependency of those,
never the other way around.
"""

from orbit_context.builder import ContextBuilder, ContextBuilderConfig
from orbit_context.engine import ContextEngine, ContextEngineError
from orbit_context.models import (
    ContextBundle,
    ExtensionBreakdown,
    ProjectStats,
    ProjectSummary,
    SearchMatchInfo,
    SelectedFile,
    WorkspaceInfo,
)

__version__ = "0.1.0"

__all__ = [
    "ContextEngine",
    "ContextEngineError",
    "ContextBuilder",
    "ContextBuilderConfig",
    "WorkspaceInfo",
    "ProjectStats",
    "ExtensionBreakdown",
    "SearchMatchInfo",
    "SelectedFile",
    "ContextBundle",
    "ProjectSummary",
    "__version__",
]
