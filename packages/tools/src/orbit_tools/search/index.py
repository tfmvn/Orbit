"""`WorkspaceIndex`: lightweight, non-semantic catalog of workspace files.

Recursively discovers files under a workspace root, skipping configurable
ignored directories and filename patterns, and caches the result until
`refresh()` is called again. No file content is stored here — `SearchTool`
reads files on demand at search time. This is the discovery layer future
search, planner, or provider code is expected to query instead of
re-walking the filesystem itself. Purely structural (paths, sizes,
timestamps) — no embeddings or semantic indexing belong here.
"""

from __future__ import annotations

import fnmatch
import os
import time
from dataclasses import dataclass
from pathlib import Path

DEFAULT_IGNORE_DIRS = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        "dist",
        "build",
        ".mypy_cache",
        ".pytest_cache",
        ".next",
        ".turbo",
    }
)

DEFAULT_IGNORE_PATTERNS: tuple[str, ...] = ("*.pyc", "*.pyo", "*.so", "*.o", "*.class")


@dataclass(frozen=True)
class IndexedFile:
    """One discovered file, path relative to the workspace root."""

    path: str
    size: int
    modified: float


class WorkspaceIndex:
    """Recursively discovers and caches a workspace's files.

    `files` and `status()` read from the last built snapshot without
    touching the filesystem; call `refresh()` to (re)build it. Cheap
    enough to rebuild fully on every refresh — no incremental diffing.
    """

    def __init__(
        self,
        root: str | Path,
        *,
        ignore_dirs: frozenset[str] | None = None,
        ignore_patterns: tuple[str, ...] | None = None,
    ) -> None:
        self.root = Path(root).expanduser().resolve()
        self.ignore_dirs = ignore_dirs if ignore_dirs is not None else DEFAULT_IGNORE_DIRS
        self.ignore_patterns = ignore_patterns if ignore_patterns is not None else DEFAULT_IGNORE_PATTERNS
        self._files: list[IndexedFile] = []
        self._built_at: float | None = None

    @property
    def files(self) -> list[IndexedFile]:
        """Cached files, building the index on first access."""
        if self._built_at is None:
            self.refresh()
        return self._files

    def _ignored_dir(self, name: str) -> bool:
        return name in self.ignore_dirs

    def _ignored_file(self, name: str) -> bool:
        return any(fnmatch.fnmatch(name, pattern) for pattern in self.ignore_patterns)

    def refresh(self) -> list[IndexedFile]:
        """Re-walk the workspace root and rebuild the cached file list."""
        discovered: list[IndexedFile] = []
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = sorted(d for d in dirnames if not self._ignored_dir(d))
            for filename in filenames:
                if self._ignored_file(filename):
                    continue
                full = Path(dirpath) / filename
                try:
                    info = full.stat()
                except OSError:
                    continue
                discovered.append(
                    IndexedFile(
                        path=str(full.relative_to(self.root)),
                        size=info.st_size,
                        modified=info.st_mtime,
                    )
                )
        discovered.sort(key=lambda f: f.path)
        self._files = discovered
        self._built_at = time.time()
        return self._files

    def status(self) -> dict[str, object]:
        """Summary of the current cache: root, file count, last build time."""
        if self._built_at is None:
            self.refresh()
        return {
            "root": str(self.root),
            "file_count": len(self._files),
            "built_at": self._built_at,
            "ignore_dirs": sorted(self.ignore_dirs),
        }
