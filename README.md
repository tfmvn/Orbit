# Orbit

Orbit is a **local-first autonomous AI runtime** — infrastructure for running AI
agents, not a chatbot. Where a chat app renders a conversation, Orbit is meant
to run as a long-lived system: it plans work, executes tools, manages memory,
and keeps jobs running over time. Think of it as an *operating system for AI
agents* rather than a single assistant.

> **Phase status:** this repository currently contains the **project
> foundation only** — the monorepo layout, backend/frontend scaffolding, and
> developer tooling. No agent, planner, memory, or tool-execution logic has
> been implemented yet. Those will land as separate packages behind the
> interfaces already defined in `apps/api/src/orbit_api/interfaces`.

---

## Philosophy

A few principles guide how Orbit is built:

1. **Runtime, not a chatbot.** Orbit is designed around long-lived processes,
   background jobs, and durable state — not a single request/response chat
   turn. The API is async-first for this reason.
2. **Local-first.** Orbit should run comfortably on a developer's own machine
   with no required cloud dependency. Cloud providers (model APIs, hosted
   vector stores, etc.) are optional plug-ins, not requirements.
3. **Boring, explicit foundations.** The scaffolding favors small, well-named
   modules, explicit dependency injection, and structured logging over clever
   abstractions. Complexity should live in the agent logic that gets added
   later, not in the plumbing.
4. **Interfaces before implementations.** Every subsystem Orbit will
   eventually need — a planner, tool execution, memory, model providers — is
   represented today as a narrow abstract interface with no implementation.
   This lets the real implementations be added later as new packages, without
   restructuring anything that already exists.
5. **No premature architecture.** We do not build speculative flexibility
   into subsystems that don't exist yet. We only make sure *the seams are in
   the right place* so future work slots in cleanly.

---

## Repository layout

```
orbit/
├── apps/
│   ├── api/                 # FastAPI backend (async, DI-based)
│   │   ├── src/orbit_api/
│   │   │   ├── main.py          # app factory / entrypoint
│   │   │   ├── config.py        # settings (pydantic-settings)
│   │   │   ├── logging.py       # structured logging setup
│   │   │   ├── core/            # DI container, app-wide wiring
│   │   │   ├── api/v1/          # versioned HTTP routes
│   │   │   └── interfaces/      # abstract contracts for future subsystems
│   │   └── tests/               # backend unit tests
│   └── web/                 # Next.js + TypeScript + Tailwind + shadcn/ui
│       └── src/
│           ├── app/             # App Router pages/layouts
│           ├── components/ui/   # shadcn/ui components
│           └── lib/             # frontend utilities
├── packages/
│   ├── shared/               # TS types/constants shared by web (and future clients)
│   ├── runtime/              # reserved — the agent execution runtime
│   ├── planner/              # reserved — task planning subsystem
│   ├── tools/                # reserved — tool execution subsystem
│   ├── memory/               # reserved — memory/storage subsystem
│   └── providers/            # reserved — model & external provider adapters
├── docs/                     # architecture & contributor docs
├── scripts/                  # dev/setup/lint helper scripts
├── tests/                    # cross-app integration/e2e tests
├── docker/                   # docker-compose and shared container config
└── .github/workflows/        # CI
```

The `packages/runtime`, `packages/planner`, `packages/tools`, `packages/memory`,
and `packages/providers` directories are intentionally created now, each with
a short `README.md` describing its future contract, so that the eventual
agent logic has an obvious, pre-agreed home and doesn't force a reorganization
of `apps/`.

---

## Backend (`apps/api`)

- **Framework:** FastAPI, async-first (no blocking I/O in request handlers).
- **Dependency injection:** FastAPI's `Depends()` is used throughout; app-wide
  singletons (settings, logger) are constructed once in `core/` and injected,
  never imported as globals inside route handlers.
- **Configuration:** `pydantic-settings`, loaded from environment variables /
  `.env`, exposed via a cached `get_settings()` dependency.
- **Logging:** structured (JSON in production, readable console in dev) via
  `structlog`, configured once at startup.
- **Interfaces:** `orbit_api/interfaces/` defines `Runtime`, `Planner`,
  `ToolProvider`, `MemoryProvider`, and `ModelProvider` as `Protocol`/`ABC`
  contracts only. Nothing implements them yet — they exist so future packages
  can be wired in via dependency injection without touching route code.

Endpoints implemented in this phase:

| Method | Path                | Purpose                          |
|--------|---------------------|-----------------------------------|
| GET    | `/api/v1/health`    | Liveness/readiness check          |
| GET    | `/api/v1/version`   | Service name, version, git commit |

## Frontend (`apps/web`)

- **Framework:** Next.js (App Router) + TypeScript.
- **Styling:** Tailwind CSS + shadcn/ui.
- **Contents:** a minimal dashboard placeholder page that calls the API's
  `/health` and `/version` endpoints, plus the standard shadcn/ui setup
  (`components.json`, `lib/utils.ts`, a couple of base components) so future
  UI can be added with `npx shadcn add ...` without extra setup.

## Shared package (`packages/shared`)

A small TypeScript package (`@orbit/shared`) holding types/constants that are
safe to share between the web app and any future client (CLI, desktop shell,
etc.) — e.g. the shape of the `/version` response. It intentionally contains
no business logic.

---

## Local development

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker + Docker Compose (optional, for containerized dev)

### Quick start

```bash
# one-time setup: installs backend + frontend deps
make setup

# run both apps in dev mode (API on :8000, web on :3000)
make dev

# run everything via Docker Compose instead
make docker-up
```

### Common tasks

| Command          | Description                                  |
|-------------------|-----------------------------------------------|
| `make setup`      | Install Python + Node dependencies            |
| `make dev`        | Run API and web app concurrently (local)      |
| `make api`        | Run only the FastAPI app (`uvicorn --reload`) |
| `make web`        | Run only the Next.js dev server               |
| `make lint`       | Run Ruff, Black --check, ESLint, Prettier --check |
| `make format`     | Auto-format Python and TypeScript             |
| `make test`       | Run backend and integration tests             |
| `make docker-up`  | Build and start all services via Compose      |
| `make docker-down`| Stop Compose services                         |

### Environment variables

Each app ships an `.env.example`:

- `apps/api/.env.example` — backend settings (host, port, log level, env name)
- `apps/web/.env.example` — frontend settings (API base URL)

Copy them to `.env` before running locally:

```bash
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env
```

---

## Architecture rules for contributors

- Keep layers separated: routes → services/interfaces → providers. Routes
  should never reach into a provider implementation directly.
- No circular imports between `apps/api`, `apps/web`, and `packages/*`.
  `packages/shared` may be depended on by `apps/web`; `apps/*` must never be
  imported by `packages/*`.
- New subsystems (a real planner, tool executor, memory store, model
  provider) should be added as new packages under `packages/`, implementing
  the interfaces in `apps/api/src/orbit_api/interfaces`, and wired into the
  API via dependency injection in `core/`. This should never require moving
  existing files.
- Prefer small, explicit modules and interfaces over large "god" modules.

See [`docs/architecture.md`](docs/architecture.md) for more detail and
[`docs/philosophy.md`](docs/philosophy.md) for the reasoning behind these
choices.

---

## License

TBD.
