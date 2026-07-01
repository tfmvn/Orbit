"""Search engine functions used by `SearchTool`.

Pure functions operating over a `WorkspaceIndex` snapshot plus the
workspace root for reading file content. No ranking or AI logic beyond
straightforward ordered matches — this is the retrieval foundation future
planners and model providers are expected to build on.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from orbit_tools.search.index import IndexedFile


@dataclass(frozen=True)
class SearchMatch:
    """One match: a whole file (filename search) or a line within one."""

    path: str
    line: int | None
    column: int | None
    text: str

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "line": self.line, "column": self.column, "text": self.text}


def filter_files(
    files: list[IndexedFile],
    *,
    extensions: list[str] | None = None,
    directory: str | None = None,
) -> list[IndexedFile]:
    """Narrow `files` by extension (e.g. `.py`) and/or directory prefix."""
    result = files
    if extensions:
        normalized = {ext if ext.startswith(".") else f".{ext}" for ext in extensions}
        result = [f for f in result if Path(f.path).suffix in normalized]
    if directory:
        prefix = directory.strip("/\\").replace("\\", "/")
        if prefix and prefix != ".":
            result = [
                f
                for f in result
                if f.path.replace("\\", "/") == prefix
                or f.path.replace("\\", "/").startswith(f"{prefix}/")
            ]
    return result


def search_filenames(
    files: list[IndexedFile], query: str, *, case_sensitive: bool, max_results: int
) -> list[SearchMatch]:
    """Substring match against each file's workspace-relative path."""
    needle = query if case_sensitive else query.lower()
    matches: list[SearchMatch] = []
    for f in files:
        haystack = f.path if case_sensitive else f.path.lower()
        if needle in haystack:
            matches.append(SearchMatch(path=f.path, line=None, column=None, text=f.path))
            if len(matches) >= max_results:
                break
    return matches


def search_contents(
    files: list[IndexedFile],
    root: Path,
    query: str,
    *,
    regex: bool,
    case_sensitive: bool,
    max_results: int,
) -> list[SearchMatch]:
    """Line-by-line full-text or regular-expression search across file contents.

    Binary or non-UTF-8 files are skipped rather than raising. Stops as
    soon as `max_results` matches are found.
    """
    flags = 0 if case_sensitive else re.IGNORECASE
    pattern = re.compile(query if regex else re.escape(query), flags)
    matches: list[SearchMatch] = []
    for f in files:
        full_path = root / f.path
        try:
            with full_path.open("r", encoding="utf-8", errors="strict") as handle:
                for line_number, line in enumerate(handle, start=1):
                    found = pattern.search(line)
                    if found:
                        matches.append(
                            SearchMatch(
                                path=f.path,
                                line=line_number,
                                column=found.start() + 1,
                                text=line.rstrip("\n"),
                            )
                        )
                        if len(matches) >= max_results:
                            return matches
        except (OSError, UnicodeDecodeError, ValueError):
            continue
    return matches
