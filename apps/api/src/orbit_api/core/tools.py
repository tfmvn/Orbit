"""Process-wide `ToolRegistry` instance, seeded with the built-in demo tools.

Mirrors the `get_runtime()` pattern in `orbit_api.core.runtime`: a single
cached instance, injected into routes via `ToolRegistryDep`. Remaining
capability tools (shell, git, browser, ...) will be registered here in
later phases.
"""

from __future__ import annotations

from functools import lru_cache

from orbit_tools import EchoTool, FilesystemTool, SystemInfoTool, TimeTool, ToolRegistry

from orbit_api.core.workspace import get_workspace_root


@lru_cache
def get_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(EchoTool())
    registry.register(TimeTool())
    registry.register(SystemInfoTool())
    registry.register(FilesystemTool(workspace_root=get_workspace_root()))
    return registry
