"""Orbit API — the backend runtime service.

This package currently contains only foundational scaffolding: app wiring,
configuration, logging, and health/version endpoints. Agent logic (planning,
tool execution, memory, providers) is deliberately not implemented here yet —
see `orbit_api.interfaces` for the contracts those subsystems will fulfill.
"""

__version__ = "0.1.0"
