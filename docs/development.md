# Local development

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker + Docker Compose (optional)

## Setup

```bash
make setup
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env
```

`make setup` installs:

- the API package in editable mode with dev dependencies
  (`pip install -e ".[dev]"` inside `apps/api`)
- Node dependencies for the whole workspace (`apps/web`, `packages/shared`)

## Running

```bash
make dev      # API on :8000, web on :3000, concurrently
make api      # API only
make web      # web only
make docker-up  # everything via Docker Compose
```

## Quality checks

```bash
make lint     # ruff + black --check + eslint + prettier --check
make format   # ruff --fix + black + prettier --write
make test     # pytest (apps/api) + any integration tests under tests/
```

CI (`.github/workflows/ci.yml`) runs the same lint and test commands on every
push and pull request.

## Adding a new backend dependency

Add it to `apps/api/pyproject.toml` under `[project.dependencies]` (or
`[project.optional-dependencies].dev` for dev-only tools), then reinstall:

```bash
cd apps/api && pip install -e ".[dev]"
```

## Adding a new frontend dependency

```bash
npm install <package> --workspace=@orbit/web
```

## Adding a future subsystem package

See [`docs/architecture.md`](architecture.md#why-interfaces-before-implementations)
and the `README.md` inside each `packages/<name>` placeholder
(`runtime`, `planner`, `tools`, `memory`, `providers`) for what belongs
where.
