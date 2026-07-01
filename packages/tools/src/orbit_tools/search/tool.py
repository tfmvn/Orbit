"""`SearchTool`: asynchronous, non-semantic code and file search.

Locates files and text within a workspace without any AI model — filename
matching, full-text matching, and regular-expression matching, all backed
by `WorkspaceIndex`. This is the retrieval foundation future planners and
LLM providers are expected to call for context instead of re-implementing
their own file walking or grepping.
"""

from __future__ import annotations

import asyncio
import re
import time
from pathlib import Path
from typing import Any

from orbit_tools.context import ToolContext
from orbit_tools.search.engine import filter_files, search_contents, search_filenames
from orbit_tools.search.index import WorkspaceIndex
from orbit_tools.tool import Tool, ToolError, ToolMetadata

_MODES = {"filename", "text", "regex"}
_DEFAULT_MAX_RESULTS = 100
_HARD_MAX_RESULTS = 1000


class SearchTool(Tool):
    """Searches a workspace's files by name or content.

    Backed by a `WorkspaceIndex` built lazily on first use; call the
    `refresh_index`/`index_status` operations (also exposed directly for
    the backend API, see `orbit_api.api.v1.search`) to rebuild or inspect
    the cache.
    """

    def __init__(
        self,
        workspace_root: str | Path,
        *,
        ignore_dirs: frozenset[str] | None = None,
    ) -> None:
        self.index = WorkspaceIndex(workspace_root, ignore_dirs=ignore_dirs)

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="search",
            description=(
                "Search the workspace for files or text without any AI model: filename "
                "matching, full-text matching, or regular expressions, with extension and "
                "directory filters. Returns matching files/lines with line, column, and "
                "search duration."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Text, substring, or regex to search for."},
                    "mode": {
                        "type": "string",
                        "enum": sorted(_MODES),
                        "default": "text",
                        "description": "'filename' matches file paths; 'text' matches literal content; 'regex' matches a pattern.",
                    },
                    "case_sensitive": {"type": "boolean", "default": False},
                    "extensions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Restrict to these extensions, e.g. ['.py', '.ts'].",
                    },
                    "directory": {
                        "type": "string",
                        "description": "Restrict to this directory, relative to the workspace root.",
                    },
                    "max_results": {"type": "integer", "default": _DEFAULT_MAX_RESULTS},
                },
                "required": ["query"],
            },
        )

    def validate(self, arguments: dict[str, Any]) -> None:
        super().validate(arguments)
        query = arguments.get("query")
        if not isinstance(query, str) or not query:
            raise ToolError("'query' must be a non-empty string")

        mode = arguments.get("mode", "text")
        if mode not in _MODES:
            raise ToolError(f"Unknown mode '{mode}'; expected one of {sorted(_MODES)}")

        max_results = arguments.get("max_results", _DEFAULT_MAX_RESULTS)
        if not isinstance(max_results, int) or isinstance(max_results, bool) or max_results <= 0:
            raise ToolError("'max_results' must be a positive integer")
        if max_results > _HARD_MAX_RESULTS:
            raise ToolError(f"'max_results' must not exceed {_HARD_MAX_RESULTS}")

        extensions = arguments.get("extensions")
        if extensions is not None and (
            not isinstance(extensions, list) or not all(isinstance(e, str) for e in extensions)
        ):
            raise ToolError("'extensions' must be a list of strings")

        directory = arguments.get("directory")
        if directory is not None and not isinstance(directory, str):
            raise ToolError("'directory' must be a string")

        if mode == "regex":
            try:
                re.compile(query)
            except re.error as exc:
                raise ToolError(f"Invalid regular expression: {exc}") from exc

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> Any:
        return await asyncio.to_thread(self._search, arguments)

    def _search(self, args: dict[str, Any]) -> dict[str, Any]:
        query = args["query"]
        mode = args.get("mode", "text")
        case_sensitive = bool(args.get("case_sensitive", False))
        max_results = int(args.get("max_results", _DEFAULT_MAX_RESULTS))

        candidates = filter_files(
            self.index.files,
            extensions=args.get("extensions"),
            directory=args.get("directory"),
        )

        started = time.perf_counter()
        if mode == "filename":
            matches = search_filenames(
                candidates, query, case_sensitive=case_sensitive, max_results=max_results
            )
        else:
            matches = search_contents(
                candidates,
                self.index.root,
                query,
                regex=(mode == "regex"),
                case_sensitive=case_sensitive,
                max_results=max_results,
            )
        duration = time.perf_counter() - started

        return {
            "query": query,
            "mode": mode,
            "matches": [m.to_dict() for m in matches],
            "match_count": len(matches),
            "files_searched": len(candidates),
            "search_duration": duration,
        }

    # -- index operations, used directly by the /search API router --------

    def index_status(self) -> dict[str, Any]:
        return self.index.status()

    def refresh_index(self) -> dict[str, Any]:
        self.index.refresh()
        return self.index.status()
