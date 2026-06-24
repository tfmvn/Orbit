import asyncio

import pytest

from orbit_tools import ProcessExecutionTool, ToolContext


@pytest.fixture
def tool(tmp_path):
    return ProcessExecutionTool(workspace_root=tmp_path)


async def _run(tool, **arguments):
    return await tool.run(arguments, ToolContext())


async def _await_completion(tool, execution_id, timeout=2.0):
    async def _poll():
        while tool.get_status(execution_id).status == "running":
            await asyncio.sleep(0.01)

    await asyncio.wait_for(_poll(), timeout=timeout)
    return tool.get_result(execution_id)


async def test_execute_returns_running_execution_id(tool):
    result = await _run(tool, command=["echo", "hello"])
    assert result.success
    assert result.output["status"] == "running"
    record = await _await_completion(tool, result.output["execution_id"])
    assert record.status == "completed"
    assert record.exit_code == 0
    assert record.stdout.strip() == "hello"


async def test_nonzero_exit_code_is_still_completed(tool):
    result = await _run(tool, command=["python3", "-c", "import sys; sys.exit(3)"])
    record = await _await_completion(tool, result.output["execution_id"])
    assert record.status == "completed"
    assert record.exit_code == 3


async def test_timeout_kills_the_process(tool):
    result = await _run(tool, command=["sleep", "5"], timeout=0.1)
    record = await _await_completion(tool, result.output["execution_id"])
    assert record.status == "timeout"


async def test_cwd_is_confined_to_workspace(tool):
    result = await _run(tool, command=["echo", "hi"], cwd="../outside")
    assert not result.success
    assert "outside the workspace" in result.error


async def test_rejects_empty_command(tool):
    result = await _run(tool, command=[])
    assert not result.success


async def test_rejects_timeout_over_max(tool):
    result = await _run(tool, command=["echo", "hi"], timeout=10_000)
    assert not result.success


async def test_cancel_running_execution(tool):
    result = await _run(tool, command=["sleep", "5"])
    execution_id = result.output["execution_id"]
    assert tool.cancel(execution_id) is True
    record = await _await_completion(tool, execution_id)
    assert record.status == "cancelled"
    assert tool.cancel(execution_id) is False
