"""`ContextEngine`: gathers and structures workspace context.

Coordinates the existing `search` and `filesystem` tools through
`orbit_tools.ToolRegistry` — never by importing or instantiating those
tool classes directly — and assembles the results into the models in
`orbit_context.models`. Purely a gathering/shaping layer: no reasoning,
ranking, or summarization happens here. Future planners and model
providers are expected to call this instead of tools directly.
"""

from __future__ import annotations

import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from orbit_tools import SearchTool, ToolContext, ToolRegistry

from orbit_context.builder import ContextBuilder
from orbit_context.models import (
    ContextBundle,
    ExtensionBreakdown,
    ProjectStats,
    ProjectSummary,
    SearchMatchInfo,
    SelectedFile,
    WorkspaceInfo,
)


class ContextEngineError(Exception):
    """Raised when a required tool is missing or a tool invocation fails."""


class ContextEngine:
    """Builds structured context from Orbit's existing tool capabilities.

    Requires a `ToolRegistry` with `search` (a `SearchTool`) and
    `filesystem` (any `FilesystemTool`-shaped tool exposing `read`,
    `metadata` operations) already registered — this class never
    registers tools itself.
    """

    def __init__(self, registry: ToolRegistry, builder: ContextBuilder | None = None) -> None:
        self._registry = registry
        self.builder = builder or ContextBuilder()

    # -- tool access, isolated so the rest of this class never touches
    #    ToolRegistry/ToolResult mechanics directly ------------------------

    def _search_tool(self) -> SearchTool:
        tool = self._registry.get("search")
        if not isinstance(tool, SearchTool):
            raise ContextEngineError("'search' tool is not registered")
        return tool

    async def _invoke(self, name: str, **arguments: Any) -> Any:
        result = await self._registry.invoke(name, arguments, ToolContext())
        if not result.success:
            raise ContextEngineError(f"'{name}' failed: {result.error}")
        return result.output

    # -- workspace info & statistics --------------------------------------

    async def workspace_info(self) -> WorkspaceInfo:
        """Identity of the workspace: root, indexed file count, index age."""
        status = self._search_tool().index_status()
        return WorkspaceInfo(
            root=status["root"],
            file_count=status["file_count"],
            indexed_at=status["built_at"],
        )

    async def project_stats(self) -> ProjectStats:
        """Aggregate file count/size, broken down by extension."""
        files = self._search_tool().index.files
        totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])  # ext -> [count, size]
        for indexed_file in files:
            ext = Path(indexed_file.path).suffix
            bucket = totals[ext]
            bucket[0] += 1
            bucket[1] += indexed_file.size
        by_extension = [
            ExtensionBreakdown(extension=ext, file_count=count, total_size=size)
            for ext, (count, size) in sorted(totals.items())
        ]
        return ProjectStats(
            total_files=len(files),
            total_size=sum(f.size for f in files),
            by_extension=by_extension,
        )

    async def project_summary(self) -> ProjectSummary:
        """Lightweight overview: workspace identity plus statistics."""
        return ProjectSummary(workspace=await self.workspace_info(), stats=await self.project_stats())

    # -- search & file loading ---------------------------------------------

    async def search_matches(
        self,
        query: str,
        *,
        mode: str = "text",
        case_sensitive: bool = False,
        extensions: list[str] | None = None,
        directory: str | None = None,
        max_results: int = 100,
    ) -> list[SearchMatchInfo]:
        """Run a search via the `search` tool and return typed matches."""
        arguments: dict[str, Any] = {
            "query": query,
            "mode": mode,
            "case_sensitive": case_sensitive,
            "max_results": max_results,
        }
        if extensions:
            arguments["extensions"] = extensions
        if directory:
            arguments["directory"] = directory
        output = await self._invoke("search", **arguments)
        return [SearchMatchInfo(**match) for match in output["matches"]]

    async def load_files(self, paths: list[str]) -> list[SelectedFile]:
        """Read each path via the `filesystem` tool, clipping oversized content.

        Paths are deduplicated and sorted first, so output order never
        depends on input order. Unreadable paths are skipped rather than
        raising, so one bad path doesn't fail the whole bundle.
        """
        selected: list[SelectedFile] = []
        for path in sorted(set(paths)):
            try:
                read = await self._invoke("filesystem", operation="read", path=path)
            except ContextEngineError:
                continue
            content, truncated = self.builder.clip_content(read["content"])
            selected.append(
                SelectedFile(path=path, size=read["size"], content=content, truncated=truncated)
            )
        return selected

    # -- full context assembly ----------------------------------------------

    async def build_context(
        self,
        *,
        query: str | None = None,
        paths: list[str] | None = None,
        mode: str = "text",
        case_sensitive: bool = False,
        extensions: list[str] | None = None,
        directory: str | None = None,
        max_results: int = 100,
    ) -> ContextBundle:
        """Assemble a full `ContextBundle` from a search query and/or explicit paths.

        Candidate files (from `paths` and/or search matches) are bounded and
        ordered deterministically by `self.builder` before any file is read,
        so `max_files` limits reads, not just the final output.
        """
        matches: list[SearchMatchInfo] = []
        candidate_paths: set[str] = set(paths or [])
        if query:
            matches = await self.search_matches(
                query,
                mode=mode,
                case_sensitive=case_sensitive,
                extensions=extensions,
                directory=directory,
                max_results=max_results,
            )
            candidate_paths |= {m.path for m in matches}

        index_sizes = {f.path: f.size for f in self._search_tool().index.files}
        candidates = [(path, index_sizes.get(path, 0)) for path in candidate_paths]
        selected_candidates, truncated = self.builder.select_files(candidates)

        files = await self.load_files([path for path, _ in selected_candidates])
        workspace = await self.workspace_info()
        stats = await self.project_stats()

        return ContextBundle(
            workspace=workspace,
            stats=stats,
            files=files,
            matches=matches,
            query=query,
            generated_at=time.time(),
            truncated=truncated,
        )
