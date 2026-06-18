"""Filesystem tool: Orbit's first real (non-demonstration) capability tool.

Exposes `FilesystemTool` plus the `WorkspaceGuard` sandboxing primitive it's
built on. `WorkspaceGuard` is intentionally reusable — it's the security
model future filesystem-touching tools (shell, git, ...) are expected to
build on too.
"""

from orbit_tools.filesystem.tool import FilesystemTool
from orbit_tools.filesystem.workspace import WorkspaceError, WorkspaceGuard

__all__ = ["FilesystemTool", "WorkspaceError", "WorkspaceGuard"]
