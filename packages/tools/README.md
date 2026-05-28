# @orbit/tools (reserved)

This package is a placeholder. It is not implemented in the foundation
phase of Orbit.

## Future purpose
Tools — registers and invokes tools available to agents (filesystem, shell, HTTP, custom tools, etc). Implements the `ToolProvider` interface defined in `apps/api/src/orbit_api/interfaces/tools.py`.

## When adding the real implementation
- Add a proper `pyproject.toml` (or `package.json`, if this ends up being a
  TS package) here.
- Depend on the corresponding interface from `orbit_api.interfaces` — don't
  redefine the contract.
- Wire the concrete implementation into `apps/api/src/orbit_api/core/dependencies.py`
  as a new `Depends(...)` provider. Route handlers should not import this
  package directly.
