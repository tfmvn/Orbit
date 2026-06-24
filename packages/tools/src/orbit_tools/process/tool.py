"""`ProcessExecutionTool`: asynchronous execution of external commands.

The execution foundation future tools (git, python, package managers,
Docker, build systems, ...) will build on. Unlike other tools, a single
invocation doesn't block until the command finishes — `execute` starts the
process in the background and returns immediately with an execution id;
callers poll `get_status`/`get_result` (exposed over HTTP at
`/api/v1/process`) the same way a shell UI would.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from orbit_tools.context import ToolContext
from orbit_tools.filesystem.workspace import WorkspaceError, WorkspaceGuard
from orbit_tools.process.executor import run_execution
from orbit_tools.process.store import ExecutionRecord, ExecutionStore
from orbit_tools.tool import Tool, ToolError, ToolMetadata

_DEFAULT_TIMEOUT = 30.0
_MAX_TIMEOUT = 300.0


class ProcessExecutionTool(Tool):
    """Runs external commands, sandboxed to a workspace root.

    `command` is an argv list (no shell interpretation, so `&&`, pipes, and
    globbing are not expanded — this avoids shell-injection entirely).
    `cwd` is resolved the same way `FilesystemTool` resolves paths: relative
    to, and confined within, the workspace root.
    """

    def __init__(self, workspace_root: str | Path) -> None:
        self._workspace = WorkspaceGuard(workspace_root)
        self.store = ExecutionStore()
        self._tasks: dict[str, asyncio.Task[None]] = {}

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="process_execute",
            description=(
                "Execute an external command asynchronously, sandboxed to Orbit's "
                "workspace. Returns immediately with an execution id; poll "
                "/api/v1/process/{id}/status and /result for progress and output."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Argv, e.g. ['git', 'status']. No shell interpretation.",
                    },
                    "cwd": {"type": "string", "default": ".", "description": "Relative to the workspace root."},
                    "env": {"type": "object", "description": "Extra environment variables."},
                    "timeout": {
                        "type": "number",
                        "default": _DEFAULT_TIMEOUT,
                        "description": f"Seconds before the process is killed (max {_MAX_TIMEOUT}).",
                    },
                },
                "required": ["command"],
            },
        )

    def validate(self, arguments: dict[str, Any]) -> None:
        super().validate(arguments)
        command = arguments.get("command")
        if not isinstance(command, list) or not command:
            raise ToolError("'command' must be a non-empty list of strings")
        if not all(isinstance(part, str) and part for part in command):
            raise ToolError("'command' must contain only non-empty strings")

        cwd = arguments.get("cwd", ".")
        if not isinstance(cwd, str):
            raise ToolError("'cwd' must be a string")
        try:
            self._workspace.resolve(cwd)
        except WorkspaceError as exc:
            raise ToolError(str(exc)) from exc

        env = arguments.get("env", {})
        if env and (not isinstance(env, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in env.items())):
            raise ToolError("'env' must be an object of string keys to string values")

        timeout = arguments.get("timeout", _DEFAULT_TIMEOUT)
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
            raise ToolError("'timeout' must be a positive number")
        if timeout > _MAX_TIMEOUT:
            raise ToolError(f"'timeout' must not exceed {_MAX_TIMEOUT} seconds")

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> Any:
        command: list[str] = arguments["command"]
        cwd = arguments.get("cwd", ".")
        resolved_cwd = self._workspace.resolve(cwd)
        env = {**os.environ, **arguments.get("env", {})}
        timeout = float(arguments.get("timeout", _DEFAULT_TIMEOUT))

        record = self.store.create(command=command, cwd=cwd)
        task = asyncio.create_task(
            run_execution(
                record,
                executable_command=command,
                resolved_cwd=str(resolved_cwd),
                env=env,
                timeout=timeout,
            )
        )
        self._tasks[record.id] = task
        task.add_done_callback(lambda _: self._tasks.pop(record.id, None))
        return {"execution_id": record.id, "status": record.status, "command": command, "cwd": cwd}

    # -- status/result/cancel, used directly by the /process API router --

    def get_status(self, execution_id: str) -> ExecutionRecord | None:
        return self.store.get(execution_id)

    def get_result(self, execution_id: str) -> ExecutionRecord | None:
        return self.store.get(execution_id)

    def cancel(self, execution_id: str) -> bool:
        """Request cancellation of a running execution.

        Returns `False` if the id is unknown or already finished.
        """
        task = self._tasks.get(execution_id)
        if task is None or task.done():
            return False
        task.cancel()
        return True
