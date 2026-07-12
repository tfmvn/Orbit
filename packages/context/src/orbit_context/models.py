"""Reusable, JSON-serializable context models produced by `ContextEngine`.

Deliberately plain dataclasses with a `to_dict()` each — mirroring
`orbit_tools.ToolResult.to_dict()` — so the API layer can serialize them
directly. No behavior beyond that; these are the shapes future planners
and model providers are expected to consume, not decide anything
themselves.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class WorkspaceInfo:
    """Identity of the workspace a context bundle was built from."""

    root: str
    file_count: int
    indexed_at: float | None

    def to_dict(self) -> dict[str, Any]:
        return {"root": self.root, "file_count": self.file_count, "indexed_at": self.indexed_at}


@dataclass(frozen=True)
class ExtensionBreakdown:
    """File count and total size for one file extension (`""` = none)."""

    extension: str
    file_count: int
    total_size: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "extension": self.extension,
            "file_count": self.file_count,
            "total_size": self.total_size,
        }


@dataclass(frozen=True)
class ProjectStats:
    """Workspace-wide statistics derived from the search tool's index."""

    total_files: int
    total_size: int
    by_extension: list[ExtensionBreakdown] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_files": self.total_files,
            "total_size": self.total_size,
            "by_extension": [e.to_dict() for e in self.by_extension],
        }


@dataclass(frozen=True)
class SearchMatchInfo:
    """One search match, as returned by the search tool."""

    path: str
    line: int | None
    column: int | None
    text: str

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "line": self.line, "column": self.column, "text": self.text}


@dataclass(frozen=True)
class SelectedFile:
    """One file's content gathered into a context bundle.

    `content` is `None` if the file couldn't be read (missing, not valid
    UTF-8 text, ...); `truncated` marks content clipped by
    `ContextBuilder`'s `max_file_size`.
    """

    path: str
    size: int
    content: str | None
    truncated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "size": self.size,
            "content": self.content,
            "truncated": self.truncated,
        }


@dataclass(frozen=True)
class GitInfo:
    """Optional Git snapshot included in a context bundle, if a repository is present.

    Deliberately minimal — the fields a future planner needs for
    situational awareness (branch, cleanliness, what's changed, what
    happened recently), not a full status/log dump. Sourced from the `git`
    tool's `metadata`, `status`, and `log` operations; no summarization
    happens here.
    """

    branch: str | None
    clean: bool
    modified_files: list[str]
    recent_commits: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "branch": self.branch,
            "clean": self.clean,
            "modified_files": self.modified_files,
            "recent_commits": self.recent_commits,
        }


@dataclass(frozen=True)
class ContextBundle:
    """Structured workspace context assembled by `ContextEngine`.

    The final, consumer-facing object: everything a future planner or
    model provider needs, gathered but not reasoned about or summarized.
    `git` is `None` when the workspace isn't a Git repository.
    """

    workspace: WorkspaceInfo
    stats: ProjectStats
    files: list[SelectedFile]
    matches: list[SearchMatchInfo]
    query: str | None
    generated_at: float
    truncated: bool
    git: GitInfo | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspace": self.workspace.to_dict(),
            "stats": self.stats.to_dict(),
            "files": [f.to_dict() for f in self.files],
            "matches": [m.to_dict() for m in self.matches],
            "query": self.query,
            "generated_at": self.generated_at,
            "truncated": self.truncated,
            "git": self.git.to_dict() if self.git else None,
        }


@dataclass(frozen=True)
class ProjectSummary:
    """Lightweight workspace overview: identity and statistics, no files.

    `git` is `None` when the workspace isn't a Git repository.
    """

    workspace: WorkspaceInfo
    stats: ProjectStats
    git: GitInfo | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspace": self.workspace.to_dict(),
            "stats": self.stats.to_dict(),
            "git": self.git.to_dict() if self.git else None,
        }
