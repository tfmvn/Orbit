"""`ContextBuilder`: pure, I/O-free rules for shaping a `ContextBundle`.

Everything here is deterministic and side-effect-free — no filesystem or
network access. `ContextEngine` does all the actual tool calls and hands
this builder plain data to filter, cap, and clip.
"""

from __future__ import annotations

from dataclasses import dataclass, field

_DEFAULT_MAX_FILES = 20
_DEFAULT_MAX_FILE_SIZE = 200_000  # bytes


@dataclass(frozen=True)
class ContextBuilderConfig:
    """Configurable limits a `ContextBuilder` enforces."""

    max_files: int = _DEFAULT_MAX_FILES
    max_file_size: int = _DEFAULT_MAX_FILE_SIZE
    ignore_paths: tuple[str, ...] = field(default_factory=tuple)


class ContextBuilder:
    """Selects and bounds files deterministically for a `ContextBundle`.

    File count and file-size limits are enforced here so `ContextEngine`
    never has to duplicate that logic; ordering is always by path, so the
    same inputs always produce the same output.
    """

    def __init__(self, config: ContextBuilderConfig | None = None) -> None:
        self.config = config or ContextBuilderConfig()

    def _is_ignored(self, path: str) -> bool:
        normalized = path.replace("\\", "/")
        return any(
            normalized == ignored or normalized.startswith(f"{ignored}/")
            for ignored in self.config.ignore_paths
        )

    def select_files(self, candidates: list[tuple[str, int]]) -> tuple[list[tuple[str, int]], bool]:
        """Filter, sort, and cap `(path, size)` candidates.

        Returns `(selected, truncated)` where `truncated` is `True` if
        `max_files` cut off otherwise-eligible candidates.
        """
        eligible = sorted(
            (path, size) for path, size in candidates if not self._is_ignored(path)
        )
        truncated = len(eligible) > self.config.max_files
        return eligible[: self.config.max_files], truncated

    def clip_content(self, content: str) -> tuple[str, bool]:
        """Clip `content` to `max_file_size` bytes (UTF-8), if needed."""
        encoded = content.encode("utf-8")
        if len(encoded) <= self.config.max_file_size:
            return content, False
        clipped = encoded[: self.config.max_file_size].decode("utf-8", errors="ignore")
        return clipped, True
