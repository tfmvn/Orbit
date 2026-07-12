"""Git Workspace: read-only Git repository inspection.

Exposes `GitTool`, sandboxed to a workspace root the same way
`FilesystemTool` and `ProcessExecutionTool` are (see `WorkspaceGuard` in
`orbit_tools.filesystem`). This release only implements inspection
(`detect`, `root`, `branch`, `status`, `log`, `diff`, `metadata`) — no
operation here ever mutates a repository. Mutating Git operations (commit,
add, push, pull, merge, rebase, ...) are a future release's concern and are
not implemented anywhere in this module.
"""

from orbit_tools.git.runner import GitCommandResult, GitNotAvailableError
from orbit_tools.git.tool import GitTool

__all__ = ["GitTool", "GitNotAvailableError", "GitCommandResult"]
