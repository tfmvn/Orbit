"""Process-wide workspace root, shared by the filesystem tool and the API.

Kept as its own provider (rather than inlined in `core/tools.py`) so
`/api/v1/workspace` can report the exact root the registered
`FilesystemTool` is sandboxed to, without either depending on the other's
wiring.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from orbit_api.config import get_settings


@lru_cache
def get_workspace_root() -> Path:
    """Return the cached, resolved workspace root directory."""
    return Path(get_settings().workspace_root).expanduser().resolve()
