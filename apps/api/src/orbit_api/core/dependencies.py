"""FastAPI dependency providers.

Route handlers should depend on these functions rather than importing
`Settings` or loggers directly. This keeps route code decoupled from how
those objects are constructed, and gives us a single place to swap in real
implementations of `Runtime`, `Planner`, `ToolProvider`, `MemoryProvider`,
and `ModelProvider` once those packages exist.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from orbit_api.config import Settings, get_settings
from orbit_api.logging import get_logger

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_app_logger() -> object:
    """Provide the application logger.

    Returns a structlog bound logger. Typed as `object` at the boundary to
    avoid leaking the structlog type into every route signature; callers can
    rely on the standard `.info/.warning/.error(...)` interface.
    """
    return get_logger("orbit_api")


LoggerDep = Annotated[object, Depends(get_app_logger)]

# Future dependency providers will be added here, e.g.:
#
#   def get_runtime(settings: SettingsDep) -> Runtime: ...
#   RuntimeDep = Annotated[Runtime, Depends(get_runtime)]
#
# wiring a concrete implementation from `packages/runtime` once it exists.
