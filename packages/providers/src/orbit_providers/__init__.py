"""orbit_providers — Orbit's Model Provider system.

Defines the `ModelProvider` interface every provider implements, a
`ProviderManager` for registration/discovery/selection/switching, and the
first concrete provider (`OllamaProvider`, backed by a local Ollama
server). No planner, chat, conversation, or memory logic lives here — this
package only turns a prompt (plus an optional `orbit_context.ContextBundle`)
into a single completion. Independent from `orbit_runtime`; the runtime and
any future planner depend on this package, never the other way around.
"""

from orbit_providers.manager import (
    NoActiveProviderError,
    ProviderAlreadyRegisteredError,
    ProviderManager,
    ProviderNotFoundError,
)
from orbit_providers.ollama import OllamaClient, OllamaConnectionError, OllamaProvider
from orbit_providers.provider import (
    GenerationParameters,
    GenerationRequest,
    GenerationResult,
    ModelInfo,
    ModelProvider,
    ProviderError,
    ProviderHealth,
)

__version__ = "0.1.0"

__all__ = [
    "ModelProvider",
    "ProviderError",
    "GenerationParameters",
    "GenerationRequest",
    "GenerationResult",
    "ModelInfo",
    "ProviderHealth",
    "ProviderManager",
    "ProviderNotFoundError",
    "ProviderAlreadyRegisteredError",
    "NoActiveProviderError",
    "OllamaProvider",
    "OllamaClient",
    "OllamaConnectionError",
    "__version__",
]
