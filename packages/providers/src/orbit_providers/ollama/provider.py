"""`OllamaProvider`: the first `ModelProvider` implementation, backed by a local Ollama server.

Talks to Ollama over HTTP via `OllamaClient` — no streaming in this
release (`stream: false` on every generate call). Every failure mode
(server unreachable, unknown model, malformed response) is normalized
into `ProviderError` or a `ProviderHealth(healthy=False, ...)`; a raw
`httpx` exception never escapes this module.
"""

from __future__ import annotations

import time

from orbit_providers.ollama.client import OllamaClient, OllamaConnectionError
from orbit_providers.provider import (
    GenerationRequest,
    GenerationResult,
    ModelInfo,
    ModelProvider,
    ProviderError,
    ProviderHealth,
)

_DEFAULT_MODEL = "llama3"


class OllamaProvider(ModelProvider):
    """Adapts a local Ollama server to the `ModelProvider` interface.

    `default_model` is used whenever a `GenerationRequest` doesn't specify
    one. `GenerationParameters` fields map onto Ollama's `options` object;
    unset (`None`) fields are omitted rather than sent through as `null`.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        *,
        default_model: str = _DEFAULT_MODEL,
        timeout: float = 60.0,
        client: OllamaClient | None = None,
    ) -> None:
        self._client = client or OllamaClient(base_url, timeout=timeout)
        self._default_model = default_model

    @property
    def name(self) -> str:
        return "ollama"

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        model = request.model or self._default_model
        options = {k: v for k, v in request.parameters.to_dict().items() if v is not None}
        started = time.monotonic()
        try:
            raw = await self._client.generate(model=model, prompt=request.combined_prompt(), options=options)
        except OllamaConnectionError as exc:
            raise ProviderError(f"Could not reach Ollama at {self._client.base_url}: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 - normalize any HTTP/parsing failure
            raise ProviderError(f"Ollama generation failed: {exc}") from exc

        if "response" not in raw:
            raise ProviderError("Unexpected Ollama response: missing 'response' field")

        return GenerationResult(
            text=raw["response"],
            model=model,
            provider=self.name,
            duration=time.monotonic() - started,
            raw=raw,
        )

    async def health(self) -> ProviderHealth:
        try:
            reachable = await self._client.ping()
        except Exception as exc:  # noqa: BLE001 - health checks never raise
            return ProviderHealth(healthy=False, provider=self.name, detail=str(exc))
        detail = None if reachable else f"Ollama server at {self._client.base_url} did not respond"
        return ProviderHealth(healthy=reachable, provider=self.name, detail=detail)

    async def list_models(self) -> list[ModelInfo]:
        try:
            models = await self._client.list_models()
        except OllamaConnectionError as exc:
            raise ProviderError(f"Could not reach Ollama at {self._client.base_url}: {exc}") from exc
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"Failed to list Ollama models: {exc}") from exc
        return [
            ModelInfo(name=m["name"], size=m.get("size"), modified_at=m.get("modified_at")) for m in models
        ]
