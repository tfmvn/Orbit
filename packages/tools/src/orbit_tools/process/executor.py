"""Runs a single subprocess to completion and updates its `ExecutionRecord`.

Kept separate from `ProcessExecutionTool` so the subprocess lifecycle
(spawn, capture, timeout, cancellation) is testable independent of the
`Tool` interface glue around it.
"""

from __future__ import annotations

import asyncio
import time

from orbit_tools.process.store import ExecutionRecord

# Upper bound on captured stdout/stderr, so a runaway/verbose command can't
# exhaust memory. Streaming (future work) removes the need for this.
_MAX_OUTPUT_BYTES = 1_000_000


def _truncate(data: bytes) -> str:
    text = data[:_MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
    if len(data) > _MAX_OUTPUT_BYTES:
        text += "\n...[output truncated]"
    return text


async def run_execution(
    record: ExecutionRecord,
    *,
    executable_command: list[str],
    resolved_cwd: str,
    env: dict[str, str],
    timeout: float,
) -> None:
    """Spawn `executable_command`, capture output, and mutate `record` in place.

    Intended to run as a background `asyncio.Task`; `record` is the shared
    state a caller polls (via `ExecutionStore`) while this coroutine runs.
    Cancelling the task (see `ProcessExecutionTool.cancel`) kills the
    underlying process and marks the record `cancelled`.
    """
    try:
        process = await asyncio.create_subprocess_exec(
            *executable_command,
            cwd=resolved_cwd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except (FileNotFoundError, PermissionError, OSError) as exc:
        record.status = "failed"
        record.stderr = str(exc)
        record.finished_at = time.time()
        return

    record.pid = process.pid
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        record.stdout = _truncate(stdout)
        record.stderr = _truncate(stderr)
        record.exit_code = process.returncode
        record.status = "completed"
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        record.status = "timeout"
        record.stderr = record.stderr or f"Execution exceeded timeout of {timeout}s"
    except asyncio.CancelledError:
        process.kill()
        await process.wait()
        record.status = "cancelled"
        raise
    finally:
        if record.finished_at is None:
            record.finished_at = time.time()
