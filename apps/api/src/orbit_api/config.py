"""Application configuration.

Settings are loaded once from environment variables (and `.env` in local
development) and exposed through the cached `get_settings()` dependency so
they can be injected wherever needed instead of imported as a global.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Orbit API service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ORBIT_",
        case_sensitive=False,
        extra="ignore",
    )

    # Identity
    app_name: str = "orbit-api"
    environment: Literal["local", "test", "staging", "production"] = "local"

    # Networking
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS — kept permissive for local dev only; tighten per-environment.
    cors_allow_origins: list[str] = ["http://localhost:3000"]

    # Filesystem tool — all file operations are sandboxed to this root.
    workspace_root: str = "./workspace"

    # Model Provider system — Ollama provider connection/generation defaults.
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "llama3"
    ollama_timeout: float = 60.0

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_json: bool = False

    @property
    def is_local(self) -> bool:
        return self.environment == "local"


@lru_cache
def get_settings() -> Settings:
    """Return a cached, process-wide Settings instance.

    Cached so repeated `Depends(get_settings)` calls don't re-parse the
    environment on every request, while still being overridable in tests via
    `get_settings.cache_clear()` + monkeypatched env vars.
    """
    return Settings()
