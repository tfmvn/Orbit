# Architecture

This document describes the foundation-phase architecture of Orbit. It will
grow as the runtime, planner, tools, and memory subsystems are implemented.

As of this release, Orbit's tool surface is: `EchoTool`, `TimeTool`,
`SystemInfoTool` (demonstration), `FilesystemTool` (sandboxed file I/O),
`ProcessExecutionTool` (sandboxed external command execution),
`SearchTool` (non-semantic workspace indexing and code search), and
`GitTool` (read-only Git repository inspection — this release). On top of
these, `packages/context` (`orbit_context`) adds the Context Engine, which
gathers and structures workspace context from the tools above, including
an optional Git snapshot. No AI, planner, memory, or agent functionality
exists yet.

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
   `packages/tools`, `packages/context`, `packages/memory`,
   `packages/providers`) — the actual agent logic. `packages/runtime`,
   `packages/tools`, and `packages/context` are implemented; the rest are
   not implemented yet. Each package implements the matching interface
   from `orbit_api.interfaces` (or, like `orbit_runtime`, `orbit_tools`,
   and `orbit_context`, is wired directly in `core/` when the interface
   would only add indirection) and nothing else needs to change to add it.

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
  architecture works end-to-end.
- **`FilesystemTool`** — Orbit's first real capability tool. See
  "Filesystem tool & workspace security" below.
- **`SearchTool`** — Orbit's first code-intelligence capability. See
  "Search tool & workspace index" below.

`apps/api` wires a single process-wide `ToolRegistry` (see
`orbit_api/core/tools.py`), seeded with the built-in tools, and exposes it
over HTTP at `/api/v1/tools` (list, get metadata, execute) — no AI or agent
endpoints exist yet. `apps/web`'s `/tools` page lists registered tools and
lets you run them, showing the resulting `ToolResult`.

## Filesystem tool & workspace security

`FilesystemTool` (`orbit_tools.filesystem`) reads, writes, and manages files
and directories through a single `operation` argument (`read`, `write`,
`create`, `delete`, `create_directory`, `delete_directory`,
`list_directory`, `copy`, `move`, `metadata`, `exists`). It's registered
under the name `filesystem` and invoked the same way as any other tool —
`POST /api/v1/tools/filesystem/execute` with `{"arguments": {"operation":
..., ...}}` — so no new AI-specific endpoints were needed.

**Security model — `WorkspaceGuard`** (`orbit_tools.filesystem.workspace`):
every path argument is resolved through this before any I/O happens.

- All paths are relative to a single configurable workspace root
  (`ORBIT_WORKSPACE_ROOT`, default `./workspace`; see `orbit_api.config` and
  `orbit_api.core.workspace.get_workspace_root`).
- Paths are normalized (`..` segments collapse) and the result is checked
  against the resolved root — traversal outside it raises `WorkspaceError`,
  surfaced to callers as a normal `ToolResult(success=False, ...)`, never a
  raw exception.
- Absolute-looking input (`/etc/passwd`, `C:\Windows`) is reinterpreted as
  relative to the workspace root rather than the host filesystem.
- `delete_directory` refuses to remove a non-empty directory unless
  `recursive=true`, and always refuses to remove the workspace root itself.
- Blocking filesystem calls run via `asyncio.to_thread` so the tool is
  non-blocking under `Tool.execute`'s async contract.

This is deliberately the pattern future filesystem-adjacent tools (shell,
git, ...) should reuse for their own sandboxing, rather than each
reimplementing path validation.

`apps/api` exposes one additional, generic endpoint — `GET
/api/v1/workspace` — returning the resolved workspace root and whether it
exists, via `orbit_api.core.workspace.get_workspace_root()` (the same root
`FilesystemTool` is constructed with in `core/tools.py`). `apps/web`'s
`/tools` page includes a minimal file explorer (`FileExplorer` in
`apps/web/src/components/file-explorer.tsx`) built entirely on these two
endpoints: browse directories, view file contents and metadata, create
files, and delete files. It intentionally has no code editor.

## Process execution tool & execution lifecycle

`ProcessExecutionTool` (`orbit_tools.process`) executes external commands
asynchronously, sandboxed to the same workspace root `FilesystemTool` uses.
It's the execution foundation future tools (git, python, package managers,
Docker, build systems, ...) are expected to build on — none of those are
implemented in this release.

**Why it doesn't block like other tools.** Every other tool's `execute`
runs to completion before `Tool.run` returns a `ToolResult`. A process can
run far longer than an HTTP request should wait on, so
`ProcessExecutionTool.execute` instead starts the command as a background
`asyncio.Task` and returns immediately with an `execution_id`. Callers poll
for progress and final output separately. `orbit_tools.process.store` holds
this state:

- **`ExecutionRecord`** — one tracked execution: `id`, `command`, `cwd`,
  `status`, `stdout`, `stderr`, `exit_code`, `pid`, timestamps, and a
  computed `duration`.
- **`ExecutionStore`** — an in-memory `id → ExecutionRecord` map, owned by
  the `ProcessExecutionTool` instance (one store per process, like
  `ToolRegistry`).
- **`orbit_tools.process.executor.run_execution`** — the coroutine that
  actually spawns the subprocess (`asyncio.create_subprocess_exec`, no
  shell — `command` is an argv list, so shell metacharacters are never
  interpreted), captures stdout/stderr, and mutates the `ExecutionRecord` in
  place as it progresses.

**Execution lifecycle.** An execution moves through exactly one path:
`running → completed` (process exited, any exit code), `running → failed`
(couldn't even spawn — e.g. unknown executable), `running → timeout`
(exceeded its `timeout` and was killed), or `running → cancelled`
(cancelled via the tool's `cancel(execution_id)`, which cancels the backing
`asyncio.Task` and kills the process). Every terminal state records
`finished_at`, so `duration` is stable once execution ends.

**Security.** Validation happens in `ProcessExecutionTool.validate` before
anything spawns, mirroring `FilesystemTool`: `command` must be a non-empty
list of strings; `cwd` is resolved through the same `WorkspaceGuard` the
filesystem tool uses, so it can never point outside the workspace root;
`env` must be a flat string-to-string mapping; `timeout` must be a positive
number no greater than a fixed cap (300s). Any violation raises `ToolError`
before a process is spawned, surfaced as a normal `ToolResult(success=False,
...)` (or, over HTTP, a 400) — never a raw exception.

**Streaming — supported by the architecture, not yet implemented.** Output
is captured in full and attached to the `ExecutionRecord` once the process
finishes rather than streamed incrementally. Nothing about this shape
forecloses it: a later phase can append output to the record as it arrives
and expose it over a websocket/SSE endpoint that tails the same record the
polling endpoints already read from, without changing `ExecutionRecord`,
`ExecutionStore`, or the tool's public methods.

**Backend API** (`apps/api/src/orbit_api/api/v1/process.py`, mounted at
`/api/v1/process`):

- `POST /execute` — validates and starts a command, returns its initial
  status.
- `GET /{id}/status` — lightweight poll (no stdout/stderr).
- `GET /{id}/result` — status plus `stdout`, `stderr`, `exit_code`.
- `POST /{id}/cancel` — requests cancellation of a running execution.

These sit alongside (not instead of) the generic `POST
/api/v1/tools/process_execute/execute` path every registered tool already
gets from `tools.py` — the dedicated router exists because status/result
polling needs to reach the tool's `ExecutionStore` directly, which the
generic single-shot `ToolRegistry.invoke` doesn't expose. The registry
itself required no changes.

`apps/web`'s `/tools` page includes a minimal `ProcessExecutor` component
(`apps/web/src/components/process-executor.tsx`) that runs a command, polls
status while it runs, and displays stdout, stderr, exit code, and duration.

## Search tool & workspace index

`SearchTool` (`orbit_tools.search`) is Orbit's first code-intelligence
capability: locating files and text within a workspace without any AI
model. It's the retrieval foundation future planners and LLM providers are
expected to call for context — none of those exist in this release, and
nothing here does embeddings, vector storage, or semantic ranking.

**`WorkspaceIndex`** (`orbit_tools.search.index`) is a lightweight,
non-semantic file catalog:

- Recursively walks a workspace root via `os.walk`, pruning ignored
  directory names (default: `.git`, `node_modules`, `.venv`, `venv`,
  `__pycache__`, `dist`, `build`, plus a few tool-cache directories) before
  descending into them, and skipping filenames matching ignored glob
  patterns (default: compiled/bytecode artifacts).
- Both `ignore_dirs` and `ignore_patterns` are constructor arguments, so a
  future caller can override them per workspace without editing this
  package.
- Stores only path, size, and modified time per file — no content, no
  embeddings. `refresh()` re-walks and replaces the cached snapshot;
  `files`/`status()` read the cache, building it lazily on first access if
  `refresh()` hasn't been called yet.

**Search flow.** `SearchTool.execute` (via `orbit_tools.search.engine`):

1. Reads `WorkspaceIndex.files` (building the index on first use).
2. Narrows candidates with `filter_files` by `extensions` and/or
   `directory`, both optional.
3. Dispatches by `mode`: `filename` (`search_filenames` — substring match
   against each candidate's relative path) or `text`/`regex`
   (`search_contents` — line-by-line match, `text` via a literal
   `re.escape`d pattern and `regex` via the query compiled directly),
   both honoring `case_sensitive` and stopping at `max_results`.
4. Returns `query`, `mode`, `matches` (each with `path`, `line`, `column`,
   `text`), `match_count`, `files_searched`, and `search_duration` (search
   time only, separate from `ToolResult.execution_time`).

Files that fail to decode as UTF-8, or disappear between indexing and
search, are skipped rather than raising — consistent with `FilesystemTool`
and `ProcessExecutionTool` converting failures into structured results, not
exceptions.

**Extension points.** A future semantic-search release can add a parallel
`mode` (e.g. `"semantic"`) or a new tool entirely that also reads from
`WorkspaceIndex`, without changing `WorkspaceIndex` or the existing
filename/text/regex modes. A future planner can call `SearchTool` through
the same `ToolRegistry.invoke("search", ...)` path any other caller does.

**Backend API** (`apps/api/src/orbit_api/api/v1/search.py`, mounted at
`/api/v1/search`):

- `POST /` — runs a search (delegates to `SearchTool` via the registry).
- `GET /index` — current index status (`root`, `file_count`, `built_at`,
  `ignore_dirs`).
- `POST /index/refresh` — re-indexes the workspace and returns the new
  status.

These sit alongside the generic `POST /api/v1/tools/search/execute` path
every registered tool already gets — the dedicated router exists because
index status/refresh need to reach `SearchTool`'s `WorkspaceIndex`
directly, the same reasoning `process.py` uses for `ExecutionStore`.

`apps/web`'s `/tools` page includes a minimal `SearchPanel` component
(`apps/web/src/components/search-panel.tsx`) with a query input, mode/
case-sensitivity/extension/directory filters, a manual re-index button, and
a results list showing matching files, lines, and search duration.

## Context Engine

`packages/context` (`orbit_context`) is Orbit's Context Engine: the layer
between raw tools and future AI consumers. It gathers and structures
workspace context — it does not reason, rank, summarize, or make any
AI-related decision. Future planners and model providers are expected to
call `ContextEngine` instead of `search`/`filesystem` tools directly,
so those tools' internals (how search matches are found, how files are
read) stay hidden behind a stable, typed interface.

**Responsibilities** (`orbit_context.ContextEngine`):

- `workspace_info()` / `project_stats()` / `project_summary()` — workspace
  identity and aggregate statistics (file count, total size, breakdown by
  extension), read from the `search` tool's `WorkspaceIndex` — no new
  filesystem walk happens here.
- `search_matches(query, ...)` — runs a search via
  `ToolRegistry.invoke("search", ...)` and returns typed
  `SearchMatchInfo` objects.
- `load_files(paths)` — reads each path via
  `ToolRegistry.invoke("filesystem", operation="read", ...)`, deduplicating
  and sorting paths first so output order never depends on call order.
  Unreadable paths are skipped, not raised.
- `build_context(query=..., paths=..., ...)` — the full assembly: runs a
  search if `query` is given, merges its matches' paths with any explicit
  `paths`, bounds that candidate set through `ContextBuilder` *before*
  reading anything (so limits cut down on tool calls, not just output),
  then loads the survivors and packages everything into a `ContextBundle`.

**Interaction with existing capabilities.** `ContextEngine` only depends on
`orbit_tools.ToolRegistry` — it calls `registry.get("search")` (typed as
`SearchTool`, to reach `index_status()`/`index.files` for statistics) and
`registry.invoke(...)` for both `search` and `filesystem`. It never
imports `FilesystemTool` or duplicates path/sandboxing logic; every read
still goes through `WorkspaceGuard` inside `FilesystemTool`. A
`ContextEngineError` wraps any tool failure (missing tool, `ToolResult`
with `success=False`) so callers see one exception type.

**Context models** (`orbit_context.models`, frozen dataclasses with
`to_dict()`, mirroring `ToolResult.to_dict()`):

- **`WorkspaceInfo`** — root, indexed file count, index build time.
- **`ExtensionBreakdown`** / **`ProjectStats`** — file count and total size,
  overall and per extension.
- **`SearchMatchInfo`** — one search match (path, line, column, text).
- **`SelectedFile`** — one gathered file (path, size, content or `None` if
  unreadable, `truncated` if content was clipped).
- **`ContextBundle`** — the full result: `workspace`, `stats`, `files`,
  `matches`, the originating `query`, `generated_at`, and `truncated`
  (whether `ContextBuilder`'s limits dropped any candidates).
- **`ProjectSummary`** — `workspace` + `stats` only, for a summary view
  without reading any file content.

**`ContextBuilder`** (`orbit_context.builder`) keeps all filtering/limiting
logic pure and separate from tool I/O:

- `select_files(candidates)` — drops paths under configured
  `ignore_paths` prefixes, sorts by path (deterministic ordering), and
  caps the result at `max_files`, reporting whether anything was cut.
- `clip_content(content)` — truncates content over `max_file_size` bytes
  (UTF-8-safe), reporting whether it clipped.

Both are driven by `ContextBuilderConfig` (`max_files`, `max_file_size`,
`ignore_paths`), so a caller can construct a `ContextEngine` with a custom
`ContextBuilder` without changing the engine itself.

**Extension points for future planners.** A planner/provider package can
depend on `orbit_context` and call `ContextEngine.build_context(...)`
without knowing `search`/`filesystem` exist — swapping or adding tools
later (git, embeddings-backed search, ...) only changes what
`ContextEngine` calls internally, not its public models. A future
semantic-search release can add relevance ranking as a new method or an
optional `ContextBuilder` strategy without touching the existing
deterministic file-count/size-based selection.

**Backend API** (`apps/api/src/orbit_api/api/v1/context.py`, mounted at
`/api/v1/context`):

- `GET /summary` — `ProjectSummary` (workspace + stats, no files).
- `GET /stats` — `ProjectStats` alone.
- `POST /generate` — full `ContextBundle` from a `query` and/or explicit
  `paths` (at least one required); mirrors `SearchTool`'s search
  parameters (`mode`, `case_sensitive`, `extensions`, `directory`,
  `max_results`).

All three return structured JSON only — no AI-shaped response fields.
`apps/web`'s new `/context` page lists indexed files (via the existing
generic `filesystem` `list_directory` endpoint), lets you select files,
optionally enter a search query, and displays the resulting
`ContextBundle` (workspace, stats, files, matches) as a JSON preview.

## Git Workspace

`orbit_tools.git` (`GitTool`) is Orbit's first Git capability: read-only
repository inspection, sandboxed to the same workspace root as
`FilesystemTool` and `ProcessExecutionTool`. **This release is
intentionally read-only** — no operation registered anywhere in this
package can modify a repository.

**Repository inspection flow.** `GitTool` never parses `.git` internals
itself; every operation shells out to the `git` executable via
`orbit_tools.git.runner.run_git` (an `asyncio.create_subprocess_exec`
wrapper, mirroring `orbit_tools.process.executor`) and `orbit_tools.git.
repository` turns that plumbing/porcelain output into plain dicts:

- `detect` — is `path` inside a Git working tree, *and* is that
  repository's root inside the configured workspace.
- `root` — the repository's top-level directory (relative to the
  workspace root).
- `branch` — current branch name (or `null` if `HEAD` is detached) and the
  short HEAD commit.
- `status` — `git status --porcelain=v2 --ignored`, split into `staged`,
  `modified`, `untracked`, `ignored`, plus a derived `clean` flag.
- `log` — recent commit history (`commit`, `short_commit`, author, date,
  `subject`), most recent first, bounded by `limit` (max 200).
- `diff` — `git diff --numstat` (or `--staged`), per-file added/removed
  line counts plus totals.
- `metadata` — a combined overview: root, branch, `clean`, and remotes.

**Security model.** Every `path` argument is resolved through the same
`WorkspaceGuard` `FilesystemTool` uses, so a caller can never point `GitTool`
outside the workspace root. That alone isn't sufficient for Git, though:
`git` searches *upward* through parent directories for a `.git` folder, so
a directory inside the workspace could still belong to a repository rooted
above it. `GitTool` closes this by resolving the actual repository root
(`git rev-parse --show-toplevel`) and rejecting the operation — with a
structured `ToolResult`, never a raw exception — unless that root also
falls inside the workspace. `detect` reports `is_repository: false` in
this case rather than erroring, since "no repository here" is a normal
answer for that operation.

**Extension points for future write operations.** Mutating operations
(`commit`, `add`, `push`, `pull`, `merge`, `rebase`, ...) are out of scope
for this release and are not implemented, stubbed, or referenced anywhere
in `orbit_tools.git`. Adding them later means adding new `_op_*`-style
branches to `GitTool.execute` and new read/write functions to
`orbit_tools.git.repository` — the `WorkspaceGuard` sandboxing, the
`run_git` subprocess wrapper, and the workspace-root containment check
above are all designed to be reused unchanged by that future work.

**Context integration.** `ContextEngine.git_info()` (`packages/context`)
calls the `git` tool's `detect`/`status`/`log`/`branch` operations and
folds them into a minimal `GitInfo` (`branch`, `clean`, `modified_files`,
`recent_commits`) — no AI summarization, just gathered facts. It returns
`None` if `git` isn't registered or the workspace isn't a repository, and
is included as the optional `git` field on both `ProjectSummary` and
`ContextBundle`.

**Backend API** (`apps/api/src/orbit_api/api/v1/git.py`, mounted at
`/api/v1/git`, alongside the generic `POST /api/v1/tools/git/execute`):

- `GET /status` — staged/modified/untracked/ignored files and `clean`.
- `GET /branch` — current branch and HEAD commit.
- `GET /log?limit=` — recent commit history.
- `GET /diff?staged=` — diff summary (working tree or staged).
- `GET /metadata` — combined root/branch/clean/remotes overview.

All read-only, all returning structured JSON — no AI-shaped response
fields, matching `search`/`context`. `apps/web`'s new `/git` page displays
branch, cleanliness, staged/modified/untracked files, and recent commits
for the workspace root.

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
