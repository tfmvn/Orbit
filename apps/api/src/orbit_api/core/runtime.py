"""Process-wide `Runtime` instance.

Mirrors the `get_settings()` pattern in `orbit_api.config`: a single cached
instance, injected into routes via `RuntimeDep`, started/stopped once from
`main.lifespan`. Handler registration for real work (tools, agents, ...)
happens here in the future, once those packages exist — this phase runs an
empty handler registry, so submitted tasks execute through the runtime's
full lifecycle but fail with "no handler registered" until one is added.
"""

from __future__ import annotations

from functools import lru_cache

from orbit_runtime import Runtime


@lru_cache
def get_runtime() -> Runtime:
    return Runtime(num_workers=1)
