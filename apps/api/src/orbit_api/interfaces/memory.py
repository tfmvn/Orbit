"""Contract for the future memory subsystem.

The implementation will live in `packages/memory`. It is responsible for
persisting and retrieving agent state/context across jobs — not implemented
here.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class MemoryProvider(Protocol):
    """Persists and retrieves agent memory.

    Intentionally left unimplemented in this phase.
    """

    async def get(self, key: str) -> Any | None:
        """Retrieve a stored value by key, or None if absent."""
        ...

    async def set(self, key: str, value: Any) -> None:
        """Store a value under a key."""
        ...

    async def delete(self, key: str) -> None:
        """Remove a stored value by key."""
        ...
