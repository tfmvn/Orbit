# @orbit/planner (reserved)

This package is a placeholder. It is not implemented in the foundation
phase of Orbit.

## Future purpose
Planner — turns a high-level goal into an ordered, executable plan. Implements the `Planner` interface defined in `apps/api/src/orbit_api/interfaces/planner.py`.

## When adding the real implementation
- Add a proper `pyproject.toml` (or `package.json`, if this ends up being a
  TS package) here.
- Depend on the corresponding interface from `orbit_api.interfaces` — don't
  redefine the contract.
- Wire the concrete implementation into `apps/api/src/orbit_api/core/dependencies.py`
  as a new `Depends(...)` provider. Route handlers should not import this
  package directly.
