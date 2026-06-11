import pytest

from orbit_tools import (
    EchoTool,
    TimeTool,
    ToolAlreadyRegisteredError,
    ToolNotFoundError,
    ToolRegistry,
)


def test_register_and_list():
    registry = ToolRegistry()
    registry.register(EchoTool())
    registry.register(TimeTool())
    names = {meta.name for meta in registry.list()}
    assert names == {"echo", "time"}


def test_duplicate_registration_rejected_unless_replace():
    registry = ToolRegistry()
    registry.register(EchoTool())
    with pytest.raises(ToolAlreadyRegisteredError):
        registry.register(EchoTool())
    registry.register(EchoTool(), replace=True)  # should not raise


def test_unregister_removes_tool():
    registry = ToolRegistry()
    registry.register(EchoTool())
    registry.unregister("echo")
    assert registry.get("echo") is None


@pytest.mark.asyncio
async def test_invoke_unknown_tool_raises():
    registry = ToolRegistry()
    with pytest.raises(ToolNotFoundError):
        await registry.invoke("nope")


@pytest.mark.asyncio
async def test_invoke_known_tool_returns_result():
    registry = ToolRegistry()
    registry.register(EchoTool())
    result = await registry.invoke("echo", {"message": "hi"})
    assert result.success
    assert result.output == {"echo": "hi"}
