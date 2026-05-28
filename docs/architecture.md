# Architecture

This document describes the foundation-phase architecture of Orbit. It will
grow as the runtime, planner, tools, and memory subsystems are implemented.

## Layers

Orbit is organized into three layers, each with a single responsibility:

1. **HTTP layer** (`apps/api/src/orbit_api/api/`) — request/response
   handling, validation, and versioning. Routes depend only on things
   provided through `orbit_api.core.dependencies`; they never construct
   settings, loggers, or (in the future) subsystem clients themselves.
2. **Wiring layer** (`apps/api/src/orbit_api/core/`) — turns configuration
   and interfaces into concrete objects and exposes them as FastAPI
   dependencies. This is the only layer allowed to know about concrete
   implementations of `Runtime`, `Planner`, `ToolProvider`, `MemoryProvider`,
   and `ModelProvider`.
3. **Subsystem layer** (`packages/runtime`, `packages/planner`,
   `packages/tools`, `packages/memory`, `packages/providers`) — the actual
   agent logic. Not implemented yet; each package will implement the
   matching interface from `orbit_api.interfaces` and nothing else needs to
   change to add it.

```
 HTTP layer  →  Wiring layer (DI)  →  Subsystem layer (interfaces today,
 (api/v1/*)     (core/*)              real packages later)
```

Dependencies only ever point downward. `packages/*` never imports from
`apps/*`, and `apps/api` never imports a concrete subsystem package directly
— only through the interfaces in `orbit_api.interfaces`, resolved by
`core/dependencies.py`.

## Why interfaces before implementations

Orbit's hardest problems — planning, tool execution, memory — don't exist in
this repository yet. Rather than guess at their internals now, this phase
defines the *shape* each subsystem must have (`Runtime`, `Planner`,
`ToolProvider`, `MemoryProvider`, `ModelProvider` — see
`apps/api/src/orbit_api/interfaces/`) so:

- HTTP routes and DI wiring can be written and tested today, against the
  interface.
- The real implementation can be built independently, in its own package,
  and swapped in later by changing one function in `core/dependencies.py`.
- No future refactor needs to move files around — `packages/runtime`,
  `packages/planner`, `packages/tools`, `packages/memory`, and
  `packages/providers` already exist as the agreed home for that code.

## Configuration and logging

- **Configuration**: a single `pydantic-settings` `Settings` class
  (`orbit_api/config.py`), populated from environment variables prefixed
  `ORBIT_`, and exposed via the cached `get_settings()` dependency. There is
  no other place in the codebase that should read `os.environ` directly.
- **Logging**: `structlog` configured once in `configure_logging()`,
  producing readable console output locally and JSON in
  non-local environments (`ORBIT_LOG_JSON=true`). Route handlers obtain a
  logger via the `LoggerDep` dependency rather than calling
  `structlog.get_logger()` themselves, so logging can be intercepted or
  extended centrally.

## Frontend

`apps/web` is a standard Next.js App Router project. It talks to the API
over plain `fetch` using `NEXT_PUBLIC_API_BASE_URL`. Types describing the
API's response shapes live in `packages/shared` so the frontend (and any
future client) doesn't need to redefine them.

## Testing

- `apps/api/tests` — unit tests for the FastAPI app, run with `pytest`
  against an in-process ASGI transport (no network, no external services).
- `tests/` (repo root) — reserved for cross-app integration/e2e tests once
  there's meaningful behavior to test end-to-end.
