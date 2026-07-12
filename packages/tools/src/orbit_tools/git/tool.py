"""`GitTool`: read-only, asynchronous Git repository inspection.

Every `path` argument is resolved through the same `WorkspaceGuard` used by
`FilesystemTool` and `ProcessExecutionTool`, so a repository outside the
configured workspace can never be inspected. This release is intentionally
read-only: every operation below maps to a non-mutating `git` plumbing/
porcelain command (`status`, `log`, `diff`, `rev-parse`, `remote -v`, ...).
Mutating operations (`commit`, `add`, `push`, `pull`, `merge`, `rebase`,
...) are out of scope and are not implemented anywhere in this package —
adding them later means adding new `_op_*` methods here, not changing the
security model.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from orbit_tools.context import ToolContext
from orbit_tools.filesystem.workspace import WorkspaceError, WorkspaceGuard
from orbit_tools.git import repository
from orbit_tools.git.runner import GitNotAvailableError
from orbit_tools.tool import Tool, ToolError, ToolMetadata

_OPERATIONS = {
    "detect",
    "root",
    "branch",
    "status",
    "log",
    "diff",
    "metadata",
}
_DEFAULT_LOG_LIMIT = 20
_MAX_LOG_LIMIT = 200


class GitTool(Tool):
    """Read-only Git repository inspection scoped to a workspace root.

    A single `operation` argument selects the action; `path` (relative to
    the workspace root, default `.`) selects which directory inside the
    workspace to inspect. Every operation ultimately shells out to the
    `git` executable (see `orbit_tools.git.runner.run_git`) rather than
    parsing `.git` internals by hand.
    """

    def __init__(self, workspace_root: str | Path) -> None:
        self._workspace = WorkspaceGuard(workspace_root)

    @property
    def workspace_root(self) -> Path:
        return self._workspace.root

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="git",
            description=(
                "Inspect Git repositories inside Orbit's sandboxed workspace: detect a "
                "repository, current branch, repository root, working-tree status "
                "(staged/modified/untracked/ignored files), recent commit history, and a "
                "diff summary. Read-only — no operation modifies the repository."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": sorted(_OPERATIONS)},
                    "path": {
                        "type": "string",
                        "default": ".",
                        "description": "Repository directory, relative to the workspace root.",
                    },
                    "limit": {
                        "type": "integer",
                        "default": _DEFAULT_LOG_LIMIT,
                        "description": "Used by 'log': max commits to return.",
                    },
                    "staged": {
                        "type": "boolean",
                        "default": False,
                        "description": "Used by 'diff': summarize staged changes instead of the working tree.",
                    },
                },
                "required": ["operation"],
            },
        )

    def validate(self, arguments: dict[str, Any]) -> None:
        super().validate(arguments)
        operation = arguments.get("operation")
        if operation not in _OPERATIONS:
            raise ToolError(f"Unknown operation '{operation}'")

        limit = arguments.get("limit", _DEFAULT_LOG_LIMIT)
        if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
            raise ToolError("'limit' must be a positive integer")
        if limit > _MAX_LOG_LIMIT:
            raise ToolError(f"'limit' must not exceed {_MAX_LOG_LIMIT}")

        staged = arguments.get("staged", False)
        if not isinstance(staged, bool):
            raise ToolError("'staged' must be a boolean")

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> Any:
        raw_path = arguments.get("path", ".")
        cwd = self._resolve(raw_path)
        operation = arguments["operation"]

        try:
            found = await repository.is_repository(str(cwd))
            in_bounds = found and await self._root_within_workspace(str(cwd))
        except GitNotAvailableError as exc:
            raise ToolError(str(exc)) from exc

        if operation == "detect":
            return {"path": raw_path, "is_repository": in_bounds}

        if not found:
            raise ToolError(f"'{raw_path}' is not a Git repository")
        if not in_bounds:
            # `git` searches parent directories for a `.git`; if the one it
            # found lives above the workspace root, the repository itself is
            # outside the sandbox even though `cwd` is inside it.
            raise ToolError(f"'{raw_path}' resolves to a repository outside the configured workspace")

        try:
            if operation == "root":
                root = await repository.repository_root(str(cwd))
                return {"root": self._relative_to_workspace(root)}
            if operation == "branch":
                return await repository.current_branch(str(cwd))
            if operation == "status":
                return await repository.status(str(cwd))
            if operation == "log":
                limit = int(arguments.get("limit", _DEFAULT_LOG_LIMIT))
                commits = await repository.log(str(cwd), limit=limit)
                return {"commits": commits, "count": len(commits)}
            if operation == "diff":
                staged = bool(arguments.get("staged", False))
                return await repository.diff_summary(str(cwd), staged=staged)
            if operation == "metadata":
                data = await repository.metadata(str(cwd))
                data["root"] = self._relative_to_workspace(data["root"])
                return data
        except GitNotAvailableError as exc:
            raise ToolError(str(exc)) from exc
        except RuntimeError as exc:
            raise ToolError(str(exc)) from exc

        raise ToolError(f"Unhandled operation '{operation}'")  # pragma: no cover - guarded by validate()

    async def _root_within_workspace(self, cwd: str) -> bool:
        """Whether the repository reachable from `cwd` is rooted inside the workspace."""
        try:
            root = await repository.repository_root(cwd)
        except RuntimeError:
            return False
        return Path(root).resolve().is_relative_to(self._workspace.root)

    # -- path resolution, mirroring FilesystemTool -----------------------

    def _resolve(self, raw: str) -> Path:
        try:
            return self._workspace.resolve(raw)
        except WorkspaceError as exc:
            raise ToolError(str(exc)) from exc

    def _relative_to_workspace(self, absolute: str) -> str:
        """Best-effort relative path for display; falls back to the absolute path.

        `git rev-parse --show-toplevel` may resolve symlinks and legitimately
        land outside the workspace root's exact string form even though the
        directory it was invoked from is inside it (e.g. a symlinked
        workspace root itself) — display the absolute path in that case
        rather than raising, since no path outside the workspace can be
        reached through `_resolve` in the first place.
        """
        try:
            return str(Path(absolute).relative_to(self._workspace.root))
        except ValueError:
            return absolute
