"""Process-wide `ProviderManager` instance, seeded with the Ollama provider.

Mirrors `get_tool_registry()` in `orbit_api.core.tools`: a single cached
instance, injected into routes via `ProviderManagerDep`. Additional
providers (Anthropic, OpenAI, other local runtimes, ...) get registered
here alongside the existing `register(...)` call — no runtime or route
code needs to change.
"""

from __future__ import annotations

from functools import lru_cache

from orbit_providers import OllamaProvider, ProviderManager

from orbit_api.config import get_settings


@lru_cache
def get_provider_manager() -> ProviderManager:
    settings = get_settings()
    manager = ProviderManager()
    manager.register(
        OllamaProvider(
            settings.ollama_base_url,
            default_model=settings.ollama_default_model,
            timeout=settings.ollama_timeout,
        )
    )
    return manager
