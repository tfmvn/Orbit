# @orbit/providers — `orbit_providers`

Orbit's Model Provider system: the abstraction layer future planners and
autonomous workflows use to talk to language models, without depending on
any specific model API. Orbit remains model-agnostic — nothing outside
this package (runtime, tools, context, and eventually the planner) knows
which provider is active.

## Contents

- **`ModelProvider`** (`provider.py`) — the generic async interface every
  provider implements: `generate`, `health`, `list_models`. Deliberately
  excludes chat-specific APIs (conversations, message roles, streaming) —
  those belong to a future planner/chat release. `GenerationRequest`
  accepts an optional `orbit_context.ContextBundle`; this package only
  combines prompt and context into a single request, it never reasons
  about what to include.
- **`ProviderManager`** (`manager.py`) — registers, discovers, selects, and
  switches between providers by name, mirroring
  `orbit_tools.ToolRegistry`. Callers (the API layer, and later a planner)
  never instantiate a provider directly.
- **`OllamaProvider`** (`ollama/`) — the first provider, backed by a local
  Ollama server. `ollama/client.py` is the thin async HTTP client;
  `ollama/provider.py` adapts it to `ModelProvider`. No streaming in this
  release — every generation call uses `stream: false`.

## Adding a new provider

Implement `ModelProvider` in a new submodule (mirroring `ollama/`), then
register an instance with the process-wide `ProviderManager` in
`apps/api/src/orbit_api/core/providers.py` — no runtime or planner code
needs to change.
