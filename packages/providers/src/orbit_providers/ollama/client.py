"""Thin async HTTP client for a local Ollama server.

Kept separate from `OllamaProvider` so the HTTP mechanics are testable on
their own, mirroring `orbit_tools.git.runner`. Only ever calls the two
endpoints `OllamaProvider` needs (`/api/tags`, `/api/generate`) plus a root
ping for health — not a general-purpose Ollama client.
"""

from __future__ import annotations

from typing import Any

import httpx

_DEFAULT_TIMEOUT = 60.0


class OllamaConnectionError(Exception):
    """Raised when the Ollama server can't be reached at all (DNS, refused, timeout, ...)."""


class OllamaClient:
    """Talks to a single Ollama server over HTTP. Raw request/response only — no retries."""

    def __init__(self, base_url: str = "http://localhost:11434", *, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self.base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def list_models(self) -> list[dict[str, Any]]:
        """`GET /api/tags` — installed local models."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(f"{self.base_url}/api/tags")
            except httpx.RequestError as exc:
                raise OllamaConnectionError(str(exc)) from exc
        response.raise_for_status()
        return response.json().get("models", [])

    async def generate(self, *, model: str, prompt: str, options: dict[str, Any]) -> dict[str, Any]:
        """`POST /api/generate` with `stream: false` — a single, non-streaming completion."""
        payload = {"model": model, "prompt": prompt, "stream": False, "options": options}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
            except httpx.RequestError as exc:
                raise OllamaConnectionError(str(exc)) from exc
        response.raise_for_status()
        return response.json()

    async def ping(self) -> bool:
        """`GET /` — Ollama's root endpoint, used as a lightweight health check."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(f"{self.base_url}/")
            except httpx.RequestError:
                return False
        return response.status_code == 200
