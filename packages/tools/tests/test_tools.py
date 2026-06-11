import pytest

from orbit_tools import EchoTool, SystemInfoTool, TimeTool, ToolContext


@pytest.mark.asyncio
async def test_echo_tool_returns_message():
    result = await EchoTool().run({"message": "hi"}, ToolContext())
    assert result.success
    assert result.output == {"echo": "hi"}
    assert result.execution_time >= 0


@pytest.mark.asyncio
async def test_echo_tool_missing_argument_fails_gracefully():
    result = await EchoTool().run({}, ToolContext())
    assert not result.success
    assert result.error is not None


@pytest.mark.asyncio
async def test_time_tool_returns_utc_timestamp():
    result = await TimeTool().run({}, ToolContext())
    assert result.success
    assert "utc" in result.output


@pytest.mark.asyncio
async def test_system_info_tool_returns_platform_fields():
    result = await SystemInfoTool().run({}, ToolContext())
    assert result.success
    assert {"system", "release", "machine", "python_version"} <= result.output.keys()
