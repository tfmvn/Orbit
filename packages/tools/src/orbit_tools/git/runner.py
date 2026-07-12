"""Runs read-only `git` subcommands and captures their output.

Kept separate from `GitTool` so the subprocess mechanics are testable on
their own, mirroring `orbit_tools.process.executor`. Unlike
`ProcessExecutionTool`, this runner is not a general command executor: it
only ever invokes `git`, and only with the read-only subcommands `GitTool`
passes in — callers outside this package never supply arbitrary argv.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

_TIMEOUT = 15.0
_MAX_OUTPUT_BYTES = 1_000_000


class GitNotAvailableError(Exception):
    """Raised when the `git` executable cannot be found or invoked."""


@dataclass(frozen=True)
class GitCommandResult:
    """Outcome of a single `git` invocation."""

    args: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def _truncate(data: bytes) -> str:
    text = data[:_MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
    if len(data) > _MAX_OUTPUT_BYTES:
        text += "\n...[output truncated]"
    return text


async def run_git(args: list[str], *, cwd: str, timeout: float = _TIMEOUT) -> GitCommandResult:
    """Run `git *args` in `cwd`, always non-interactively and read-only.

    Raises `GitNotAvailableError` if the `git` executable is missing; any
    other failure (non-zero exit, e.g. "not a git repository") is returned
    as a `GitCommandResult` with `ok = False` rather than raised, so callers
    can turn it into a `ToolError` with the real git message.
    """
    try:
        process = await asyncio.create_subprocess_exec(
            "git",
            "-c",
            "core.pager=cat",
            *args,
            cwd=cwd,
            env={"GIT_TERMINAL_PROMPT": "0"},
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise GitNotAvailableError("The 'git' executable was not found on this system") from exc

    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        return GitCommandResult(args=args, returncode=-1, stdout="", stderr=f"'git {' '.join(args)}' timed out")

    return GitCommandResult(
        args=args,
        returncode=process.returncode if process.returncode is not None else -1,
        stdout=_truncate(stdout),
        stderr=_truncate(stderr),
    )
