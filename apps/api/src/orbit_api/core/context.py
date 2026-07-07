"""Process-wide `ContextEngine` instance.

Mirrors `get_tool_registry()` in `orbit_api.core.tools`: a single cached
instance, injected into routes via `ContextEngineDep`. Built on top of the
same process-wide `ToolRegistry` — no separate tool wiring happens here.
"""

from __future__ import annotations

from functools import lru_cache

from orbit_context import ContextEngine

from orbit_api.core.tools import get_tool_registry


@lru_cache
def get_context_engine() -> ContextEngine:
    return ContextEngine(get_tool_registry())
