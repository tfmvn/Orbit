from typing import Any

import pytest
from orbit_providers.ollama.client import OllamaConnectionError
from orbit_providers.ollama.provider import OllamaProvider
from orbit_providers.provider import GenerationRequest, ProviderError


class FakeClient:
    """Stand-in for `OllamaClient` — no real HTTP calls."""

    base_url = "http://localhost:11434"

    def __init__(self) -> None:
        self.generate_response: dict[str, Any] = {"response": "hi there"}
        self.models: list[dict[str, Any]] = [{"name": "llama3", "size": 123, "modified_at": "now"}]
        self.reachable = True
        self.raise_on_generate: Exception | None = None
        self.raise_on_list: Exception | None = None

    async def generate(self, *, model: str, prompt: str, options: dict[str, Any]) -> dict[str, Any]:
        if self.raise_on_generate:
            raise self.raise_on_generate
        return self.generate_response

    async def list_models(self) -> list[dict[str, Any]]:
        if self.raise_on_list:
            raise self.raise_on_list
        return self.models

    async def ping(self) -> bool:
        return self.reachable


async def test_generate_returns_text() -> None:
    client = FakeClient()
    provider = OllamaProvider(client=client, default_model="llama3")
    result = await provider.generate(GenerationRequest(prompt="hello"))
    assert result.text == "hi there"
    assert result.model == "llama3"
    assert result.provider == "ollama"


async def test_generate_wraps_connection_error() -> None:
    client = FakeClient()
    client.raise_on_generate = OllamaConnectionError("refused")
    provider = OllamaProvider(client=client)
    with pytest.raises(ProviderError):
        await provider.generate(GenerationRequest(prompt="hello"))


async def test_generate_rejects_malformed_response() -> None:
    client = FakeClient()
    client.generate_response = {"unexpected": "shape"}
    provider = OllamaProvider(client=client)
    with pytest.raises(ProviderError):
        await provider.generate(GenerationRequest(prompt="hello"))


async def test_health_reports_unreachable_without_raising() -> None:
    client = FakeClient()
    client.reachable = False
    provider = OllamaProvider(client=client)
    health = await provider.health()
    assert health.healthy is False
    assert health.provider == "ollama"


async def test_list_models_maps_fields() -> None:
    client = FakeClient()
    provider = OllamaProvider(client=client)
    models = await provider.list_models()
    assert models[0].name == "llama3"
    assert models[0].size == 123


async def test_list_models_wraps_connection_error() -> None:
    client = FakeClient()
    client.raise_on_list = OllamaConnectionError("refused")
    provider = OllamaProvider(client=client)
    with pytest.raises(ProviderError):
        await provider.list_models()
