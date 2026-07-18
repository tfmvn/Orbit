import pytest
from orbit_providers.manager import (
    NoActiveProviderError,
    ProviderAlreadyRegisteredError,
    ProviderManager,
    ProviderNotFoundError,
)
from orbit_providers.provider import (
    GenerationRequest,
    GenerationResult,
    ModelInfo,
    ModelProvider,
    ProviderHealth,
)


class FakeProvider(ModelProvider):
    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        return GenerationResult(text="ok", model="fake", provider=self._name, duration=0.0)

    async def health(self) -> ProviderHealth:
        return ProviderHealth(healthy=True, provider=self._name)

    async def list_models(self) -> list[ModelInfo]:
        return [ModelInfo(name="fake-model")]


def test_first_registration_becomes_active() -> None:
    manager = ProviderManager()
    manager.register(FakeProvider("a"))
    assert manager.active == "a"
    assert manager.active_provider.name == "a"


def test_second_registration_does_not_change_active_unless_requested() -> None:
    manager = ProviderManager()
    manager.register(FakeProvider("a"))
    manager.register(FakeProvider("b"))
    assert manager.active == "a"
    manager.register(FakeProvider("c"), activate=True)
    assert manager.active == "c"


def test_duplicate_registration_raises_unless_replace() -> None:
    manager = ProviderManager()
    manager.register(FakeProvider("a"))
    with pytest.raises(ProviderAlreadyRegisteredError):
        manager.register(FakeProvider("a"))
    manager.register(FakeProvider("a"), replace=True)


def test_list_and_get() -> None:
    manager = ProviderManager()
    manager.register(FakeProvider("b"))
    manager.register(FakeProvider("a"))
    assert manager.list() == ["a", "b"]
    assert manager.get("a") is not None
    assert manager.get("missing") is None


def test_set_active_unknown_provider_raises() -> None:
    manager = ProviderManager()
    manager.register(FakeProvider("a"))
    with pytest.raises(ProviderNotFoundError):
        manager.set_active("missing")


def test_unregister_active_clears_active() -> None:
    manager = ProviderManager()
    manager.register(FakeProvider("a"))
    manager.unregister("a")
    assert manager.active is None
    with pytest.raises(NoActiveProviderError):
        manager.active_provider
