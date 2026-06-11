"""Generic `Tool` interface every future tool implements.

Tools are self-contained, model-agnostic units of capability. They never
import from `orbit_runtime`, a future AI provider, or a planner — the
`ToolRegistry` and its callers depend only on this interface, never on a
concrete tool class.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from orbit_tools.context import ToolContext
from orbit_tools.result import ToolResult


@dataclass(frozen=True)
class ToolMetadata:
    """Static description of a tool: identity and its argument shape.

    `parameters` is a JSON-Schema-like dict, e.g.
    `{"type": "object", "properties": {...}, "required": [...]}`. Kept as a
    plain dict rather than a Pydantic model so tools stay dependency-light.
    """

    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"


class ToolError(Exception):
    """Raised by a tool when arguments are invalid or execution fails."""


class Tool(ABC):
    """Base class every tool implements."""

    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """Static description of this tool: name, description, parameters."""

    def validate(self, arguments: dict[str, Any]) -> None:
        """Validate `arguments` before execution.

        Default: checks every key in `metadata.parameters["required"]` is
        present. Override for richer validation. Raise `ToolError` on
        failure.
        """
        required = self.metadata.parameters.get("required", [])
        missing = [key for key in required if key not in arguments]
        if missing:
            raise ToolError(f"Missing required argument(s): {', '.join(missing)}")

    @abstractmethod
    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> Any:
        """Perform the tool's work and return a raw result.

        Only called after `validate` succeeds. Raise `ToolError` (or let any
        other exception propagate) on failure — `run` below converts both
        into a `ToolResult`.
        """

    async def run(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        """Validate, execute, and wrap the outcome in a `ToolResult`.

        Callers should use this, not `execute` directly — it never raises;
        failures come back as `ToolResult.success = False`.
        """
        started = time.monotonic()
        try:
            self.validate(arguments)
            output = await self.execute(arguments, context)
            return ToolResult(success=True, output=output, execution_time=time.monotonic() - started)
        except ToolError as exc:
            return ToolResult(success=False, error=str(exc), execution_time=time.monotonic() - started)
        except Exception as exc:  # noqa: BLE001 - convert any tool failure into a result
            return ToolResult(
                success=False,
                error=f"{type(exc).__name__}: {exc}",
                execution_time=time.monotonic() - started,
            )
