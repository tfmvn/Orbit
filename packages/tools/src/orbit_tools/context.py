"""Reusable execution context passed to every tool invocation.

Structure only — no AI-specific logic. This is deliberately generic so a
future agent/planner layer can populate it with task information,
permissions, and configuration without this package knowing anything about
tasks, agents, or planners.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolContext:
    """Per-invocation context for a tool execution.

    Every field is optional so callers can supply as much or as little as
    they have today; this package never interprets any of them beyond the
    cooperative-cancellation check below.
    """

    task_id: str | None = None
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    permissions: frozenset[str] = field(default_factory=frozenset)
    config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    cancel_requested: bool = False

    def is_cancelled(self) -> bool:
        """Cooperative cancellation check long-running tools may poll."""
        return self.cancel_requested
