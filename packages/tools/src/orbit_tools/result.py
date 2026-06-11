"""Standardized result object every tool invocation returns.

Produced by `Tool.run` (see `tool.py`) — tool authors never construct this
directly. Every future tool, no matter what it does, reports its outcome
through this same shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Outcome of a single tool invocation."""

    success: bool
    output: Any | None = None
    error: str | None = None
    execution_time: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Plain-dict form, convenient for JSON responses."""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
        }
