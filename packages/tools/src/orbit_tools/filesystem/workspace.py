"""`WorkspaceGuard`: normalizes and validates paths against a fixed root.

Every tool that touches the filesystem should resolve caller-supplied paths
through this before doing any I/O. It is the security model this release
establishes as the foundation future tools (shell, git, browser, ...) are
expected to reuse for their own sandboxing.
"""

from __future__ import annotations

from pathlib import Path


class WorkspaceError(Exception):
    """Raised when a path cannot be safely resolved inside the workspace."""


class WorkspaceGuard:
    """Resolves caller-supplied paths relative to a fixed workspace root.

    Guarantees the returned path is normalized and lies inside `root` —
    `..` traversal and symlinks that escape the root are both rejected.
    Absolute-looking input (e.g. `/etc/passwd`, `C:\\Windows`) is treated as
    relative to the workspace, never as a pointer into the host filesystem.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve(self, relative_path: str | None) -> Path:
        """Return the absolute, validated path for `relative_path`.

        Raises `WorkspaceError` if the normalized path would fall outside
        `root`.
        """
        raw = relative_path if relative_path not in (None, "") else "."
        candidate_parts = Path(raw)
        if candidate_parts.is_absolute():
            # Drop the OS-level anchor so absolute-looking input stays
            # relative to the workspace instead of the host filesystem.
            candidate_parts = Path(*candidate_parts.parts[1:])
        candidate = (self.root / candidate_parts).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise WorkspaceError(
                f"Path '{relative_path}' resolves outside the workspace root"
            ) from exc
        return candidate
