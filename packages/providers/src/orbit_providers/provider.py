"""Generic asynchronous provider interface every model provider implements.

Mirrors `orbit_tools.tool.Tool`: a small abstract surface future callers
(a planner, the API layer) depend on, never a concrete provider class
directly. Deliberately excludes chat-specific APIs (conversations, message
roles, streaming) — those belong to a future planner/chat release, not
this one.

`GenerationRequest.context` accepts an optional structured
`orbit_context.ContextBundle`. This module only combines prompt and
context into a single string before it reaches a provider — no planning,
ranking, or summarization happens here.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from orbit_context import ContextBundle


class ProviderError(Exception):
    """Raised when a provider operation fails (network, unknown model, malformed response, ...)."""


@dataclass(frozen=True)
class GenerationParameters:
    """Model-agnostic generation knobs. Providers map these onto their own API shape."""

    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    stop: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "stop": self.stop,
        }


def _render_context(context: ContextBundle) -> str:
    """Plain-text rendering of a `ContextBundle` — mechanical concatenation only.

    File contents and search matches are included as-is; nothing is
    summarized, ranked, or reasoned about. A future planner is expected to
    shape `context` before it reaches a `GenerationRequest`, not this
    function.
    """
    parts = [f"# Workspace: {context.workspace.root}"]
    if context.git is not None:
        parts.append(f"# Git: branch={context.git.branch} clean={context.git.clean}")
    if context.matches:
        match_lines = "\n".join(f"{m.path}:{m.line}: {m.text}" for m in context.matches)
        parts.append(f"# Search matches for {context.query!r}:\n{match_lines}")
    for selected_file in context.files:
        if selected_file.content is not None:
            parts.append(f"## {selected_file.path}\n{selected_file.content}")
    return "\n\n".join(parts)


@dataclass(frozen=True)
class GenerationRequest:
    """A single completion request.

    `model` is `None` when the caller wants the provider's default model.
    `context`, if given, is folded into the final prompt sent to the model
    via `combined_prompt()`.
    """

    prompt: str
    model: str | None = None
    context: ContextBundle | None = None
    parameters: GenerationParameters = field(default_factory=GenerationParameters)

    def combined_prompt(self) -> str:
        """`prompt`, prefixed with a plain-text rendering of `context` if present."""
        if self.context is None:
            return self.prompt
        return f"{_render_context(self.context)}\n\n{self.prompt}"


@dataclass(frozen=True)
class GenerationResult:
    """Outcome of a single `generate()` call."""

    text: str
    model: str
    provider: str
    duration: float
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "model": self.model,
            "provider": self.provider,
            "duration": self.duration,
            "raw": self.raw,
        }


@dataclass(frozen=True)
class ModelInfo:
    """One model available from a provider."""

    name: str
    size: int | None = None
    modified_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "size": self.size, "modified_at": self.modified_at}


@dataclass(frozen=True)
class ProviderHealth:
    """Outcome of a single `health()` call."""

    healthy: bool
    provider: str
    detail: str | None = None
    checked_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "healthy": self.healthy,
            "provider": self.provider,
            "detail": self.detail,
            "checked_at": self.checked_at,
        }


class ModelProvider(ABC):
    """Base class every model provider implements.

    Deliberately narrow and chat-agnostic: `generate`, `health`,
    `list_models`. Future planners and chat interfaces are expected to
    build on top of this, never call a concrete provider (e.g.
    `OllamaProvider`) directly — they go through `ProviderManager`.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable identifier this provider is registered under (e.g. 'ollama')."""

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """Return a single completion for `request`. Raises `ProviderError` on failure."""

    @abstractmethod
    async def health(self) -> ProviderHealth:
        """Check whether this provider is reachable and usable right now. Never raises."""

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """Return the models this provider currently has available. Raises `ProviderError` on failure."""
