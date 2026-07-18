"""`ProviderManager`: registers, discovers, selects, and switches between model providers.

Mirrors `orbit_tools.ToolRegistry`'s "register once, look up by name"
shape. The runtime — and any future planner — should never instantiate a
provider directly; it goes through this manager instead, so adding a new
provider (e.g. an Anthropic or OpenAI adapter later) never requires
changing runtime or planner code.
"""

from __future__ import annotations

from orbit_providers.provider import ModelProvider


class ProviderNotFoundError(Exception):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"No provider registered with name '{name}'")


class ProviderAlreadyRegisteredError(Exception):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"A provider named '{name}' is already registered")


class NoActiveProviderError(Exception):
    """Raised when an operation needs an active provider but none is set."""


class ProviderManager:
    """Registers, discovers, selects, and switches between `ModelProvider`s."""

    def __init__(self) -> None:
        self._providers: dict[str, ModelProvider] = {}
        self._active: str | None = None

    def register(
        self, provider: ModelProvider, *, replace: bool = False, activate: bool = False
    ) -> None:
        """Register `provider` under its `.name`.

        Raises `ProviderAlreadyRegisteredError` unless `replace=True`. The
        first provider ever registered becomes active automatically;
        `activate=True` makes any later registration active too.
        """
        name = provider.name
        if not replace and name in self._providers:
            raise ProviderAlreadyRegisteredError(name)
        self._providers[name] = provider
        if self._active is None or activate:
            self._active = name

    def unregister(self, name: str) -> None:
        """Remove a provider by name. No-op if it isn't registered.

        Clears `active` if the removed provider was active — callers must
        `set_active(...)` again before reading `active_provider`.
        """
        self._providers.pop(name, None)
        if self._active == name:
            self._active = None

    def get(self, name: str) -> ModelProvider | None:
        """Look up a provider by name, or `None` if unregistered."""
        return self._providers.get(name)

    def list(self) -> list[str]:
        """Discover the names of all registered providers."""
        return sorted(self._providers)

    @property
    def active(self) -> str | None:
        """Name of the currently active provider, or `None` if none is set."""
        return self._active

    def set_active(self, name: str) -> None:
        """Switch the active provider. Raises `ProviderNotFoundError` if unregistered."""
        if name not in self._providers:
            raise ProviderNotFoundError(name)
        self._active = name

    @property
    def active_provider(self) -> ModelProvider:
        """The currently active provider. Raises `NoActiveProviderError` if none is set."""
        if self._active is None:
            raise NoActiveProviderError("No active provider is set")
        return self._providers[self._active]
