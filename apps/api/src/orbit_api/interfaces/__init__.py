"""Abstract contracts for Orbit's future subsystems.

Nothing in this package contains logic. Each module defines the narrow
interface a future package (see `packages/runtime`, `packages/planner`,
`packages/tools`, `packages/memory`, `packages/providers`) is expected to
implement. Defining these now lets the API's dependency-injection wiring
(`orbit_api.core`) reference stable contracts before any implementation
exists, so real implementations can be dropped in later without changing
route code or repository layout.
"""

from orbit_api.interfaces.memory import MemoryProvider
from orbit_api.interfaces.planner import Planner
from orbit_api.interfaces.provider import ModelProvider
from orbit_api.interfaces.runtime import Runtime
from orbit_api.interfaces.tools import ToolProvider

__all__ = [
    "MemoryProvider",
    "Planner",
    "ModelProvider",
    "Runtime",
    "ToolProvider",
]
