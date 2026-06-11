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
   agent logic. `packages/runtime` and `packages/tools` are implemented;
   the rest are not implemented yet. Each package implements the matching
   interface from `orbit_api.interfaces` (or, like `orbit_runtime` and
   `orbit_tools`, is wired directly in `core/` when the interface would
   only add indirection) and nothing else needs to change to add it.

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

## Runtime engine

`packages/runtime` (`orbit_runtime`) is a generic async execution engine. It
is deliberately independent from any LLM, planner, memory system, or tool
implementation — those are future subsystems that will *depend on* this
package, never the other way around.

- **Task** — the only unit of work. Carries an opaque `name` and `payload`;
  the runtime never interprets either. Moves through a validated state
  machine: `created → queued → running → {completed, failed, cancelled}`.
  Invalid transitions raise `InvalidTransitionError` rather than silently
  succeeding.
- **Queue** — `TaskQueue` is an abstract contract (`put`/`get`/`qsize`).
  `InMemoryTaskQueue` is the Phase 1 implementation, backed by
  `asyncio.Queue`. A Redis-backed (or other) queue can implement the same
  contract later without changing `Runtime` or `Worker`.
- **Worker** — pulls task IDs off the queue one at a time, transitions the
  task through its lifecycle, and calls whatever handler is registered for
  its `name` via `Runtime.register_handler(name, handler)`. Contains no AI
  logic; if no handler is registered the task fails with a clear error.
- **Event bus** — a minimal async pub/sub (`EventBus`), emitting
  `TaskCreated`, `TaskQueued`, `TaskStarted`, `TaskCompleted`, `TaskFailed`,
  and `TaskCancelled`. Future UI or logging subscribes without the runtime
  knowing they exist.
- **Runtime** — the façade future subsystems and the API depend on:
  `submit`, `cancel`, `get`, `list`, plus `start`/`stop` for the worker pool.
  It owns the task store, queue, event bus, and handler registry, but knows
  nothing about what any task actually does.

`apps/api` wires a single process-wide `Runtime` (see
`orbit_api/core/runtime.py`), started/stopped from the app's lifespan, and
exposes it over HTTP at `/api/v1/tasks` (submit, get, list, cancel) — no AI
endpoints exist yet. `apps/web`'s `/tasks` page is a placeholder view over
that same API.

## Tool framework

`packages/tools` (`orbit_tools`) is Orbit's model-agnostic tool framework —
the infrastructure future tools (shell, filesystem, git, browser, ...) will
plug into. It has no dependency on `orbit_runtime`, any AI provider, or a
planner; those are future callers of this package, never the other way
around.

- **`Tool`** — the abstract base every tool implements: a `metadata`
  property (`ToolMetadata`: name, description, JSON-Schema-like
  `parameters`, version), `validate(arguments)`, and
  `async execute(arguments, context)`. `Tool.run(...)` wraps validation and
  execution and never raises — failures come back as a `ToolResult` with
  `success=False`.
- **`ToolContext`** — reusable per-invocation context (task id, request id,
  permissions, config, metadata, a cooperative cancellation flag).
  Structure only, populated by future callers; this package never
  interprets it.
- **`ToolResult`** — the standardized outcome every tool returns:
  `success`, `output`, `error`, `execution_time`, `metadata`.
- **`ToolRegistry`** — registers, unregisters, discovers (`list()`), and
  invokes (`invoke(name, arguments, context)`) tools by name, mirroring
  `orbit_runtime.HandlerRegistry`'s "register once, look up by name" shape.
  Callers never instantiate a tool directly.
- **Built-in demonstration tools** — `EchoTool`, `TimeTool`,
  `SystemInfoTool`. Trivial by design; they exist only to prove the
  architecture works end-to-end. Real capability tools belong to later
  phases.

`apps/api` wires a single process-wide `ToolRegistry` (see
`orbit_api/core/tools.py`), seeded with the built-in tools, and exposes it
over HTTP at `/api/v1/tools` (list, get metadata, execute) — no AI or agent
endpoints exist yet. `apps/web`'s `/tools` page lists registered tools and
lets you run them, showing the resulting `ToolResult`.

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
