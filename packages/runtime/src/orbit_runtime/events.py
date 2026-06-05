"""Lightweight async publish/subscribe event bus.

Decouples the runtime/worker from anything that wants to observe task
lifecycle changes (a future UI, logging, metrics, ...). Publishers and
subscribers never reference each other directly.
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EventType(str, Enum):
    TASK_CREATED = "task_created"
    TASK_QUEUED = "task_queued"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"


@dataclass
class Event:
    type: EventType
    task_id: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


Handler = Callable[[Event], Any | Awaitable[Any]]


class EventBus:
    """Minimal pub/sub bus. Subscribers may be sync or async callables."""

    def __init__(self) -> None:
        self._subscribers: dict[EventType, list[Handler]] = {}
        self._global_subscribers: list[Handler] = []

    def subscribe(self, event_type: EventType, handler: Handler) -> Callable[[], None]:
        """Subscribe to a single event type. Returns an unsubscribe callback."""
        self._subscribers.setdefault(event_type, []).append(handler)

        def unsubscribe() -> None:
            self._subscribers[event_type].remove(handler)

        return unsubscribe

    def subscribe_all(self, handler: Handler) -> Callable[[], None]:
        """Subscribe to every event type. Returns an unsubscribe callback."""
        self._global_subscribers.append(handler)

        def unsubscribe() -> None:
            self._global_subscribers.remove(handler)

        return unsubscribe

    async def publish(self, event: Event) -> None:
        """Notify all matching subscribers, awaiting async handlers."""
        handlers = self._global_subscribers + self._subscribers.get(event.type, [])
        for handler in handlers:
            result = handler(event)
            if inspect.isawaitable(result):
                await result
