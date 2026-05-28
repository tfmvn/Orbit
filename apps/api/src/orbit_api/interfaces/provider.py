"""Contract for the future model/external provider adapters.

Implementations will live in `packages/providers` (e.g. an Anthropic adapter,
a local model adapter). Responsible for calling out to language models or
other external services — not implemented here.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ModelProvider(Protocol):
    """Adapts an external model API to a common interface.

    Intentionally left unimplemented in this phase.
    """

    async def complete(self, prompt: str, **kwargs: Any) -> str:
        """Return a completion for the given prompt."""
        ...
