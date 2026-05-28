# @orbit/providers (reserved)

This package is a placeholder. It is not implemented in the foundation
phase of Orbit.

## Future purpose
Providers — adapters for model APIs and other external services (e.g. Anthropic, local models, vector stores). Implements the `ModelProvider` interface defined in `apps/api/src/orbit_api/interfaces/provider.py`.

## When adding the real implementation
- Add a proper `pyproject.toml` (or `package.json`, if this ends up being a
  TS package) here.
- Depend on the corresponding interface from `orbit_api.interfaces` — don't
  redefine the contract.
- Wire the concrete implementation into `apps/api/src/orbit_api/core/dependencies.py`
  as a new `Depends(...)` provider. Route handlers should not import this
  package directly.
