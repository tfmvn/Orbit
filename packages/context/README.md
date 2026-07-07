# @orbit/context

Orbit's Context Engine. Coordinates the existing `search` and `filesystem`
tools (via `orbit_tools.ToolRegistry`) to gather and structure workspace
context — project summaries, relevant files, file contents, and workspace
statistics — as reusable, JSON-serializable models. No AI, reasoning, or
summarization logic lives here; future planners and model providers consume
`ContextEngine`'s output rather than calling tools directly.

## Install (editable, local development)

```bash
pip install -e ".[dev]"
```

## Concepts

- **`ContextEngine`** — the coordinating service. Given a `ToolRegistry`
  already seeded with `search` and `filesystem` tools, it exposes
  `project_summary()`, `search_matches(query, ...)`, `load_files(paths)`,
  and `build_context(query=..., paths=..., ...)`, each returning one of the
  models below. It never imports or constructs tools itself — only calls
  `registry.invoke(...)` — so it stays decoupled from how those tools work
  internally.
- **`ContextBuilder`** — pure, I/O-free logic for turning a candidate file
  list into a bounded, deterministically ordered selection: caps file
  count (`max_files`), clips content over `max_file_size`, and drops paths
  under configured `ignore_paths` prefixes. `ContextEngine` uses one
  internally; it does no filtering of its own.
- **Context models** (`orbit_context.models`) — frozen dataclasses:
  `WorkspaceInfo`, `ProjectStats`, `SelectedFile`, `SearchMatchInfo`, and
  the top-level `ContextBundle`. Each has a `to_dict()` for JSON responses,
  mirroring `orbit_tools.ToolResult.to_dict()`.

## Usage

```python
from orbit_context import ContextEngine
from orbit_tools import FilesystemTool, SearchTool, ToolRegistry

registry = ToolRegistry()
registry.register(SearchTool(workspace_root="./workspace"))
registry.register(FilesystemTool(workspace_root="./workspace"))

engine = ContextEngine(registry)
summary = await engine.project_summary()
bundle = await engine.build_context(query="def main")
bundle.files, bundle.matches, bundle.stats, bundle.truncated
```

## Extension points

- A future planner calls `ContextEngine` instead of the `ToolRegistry`
  directly — the engine's models are the shape planners/providers are
  expected to consume.
- A future semantic-search release can add a new `ContextEngine` method
  (e.g. ranking or embeddings-backed selection) without changing
  `ContextBuilder` or the existing models; this package makes no
  relevance judgments itself, it only assembles what `search`/`filesystem`
  return.
