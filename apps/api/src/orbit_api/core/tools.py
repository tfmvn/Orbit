"""Process-wide `ToolRegistry` instance, seeded with the built-in demo tools.

Mirrors the `get_runtime()` pattern in `orbit_api.core.runtime`: a single
cached instance, injected into routes via `ToolRegistryDep`. Real tools
(shell, filesystem, git, browser, ...) will be registered here in later
phases — this phase only wires the lightweight demonstration tools.
"""

from __future__ import annotations

from functools import lru_cache

from orbit_tools import EchoTool, SystemInfoTool, TimeTool, ToolRegistry


@lru_cache
def get_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(EchoTool())
    registry.register(TimeTool())
    registry.register(SystemInfoTool())
    return registry
