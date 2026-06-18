import pytest

from orbit_tools import FilesystemTool, ToolContext, WorkspaceError, WorkspaceGuard


@pytest.fixture
def tool(tmp_path):
    return FilesystemTool(workspace_root=tmp_path)


async def _run(tool, **arguments):
    return await tool.run(arguments, ToolContext())


def test_workspace_guard_rejects_traversal(tmp_path):
    guard = WorkspaceGuard(tmp_path)
    with pytest.raises(WorkspaceError):
        guard.resolve("../outside.txt")


def test_workspace_guard_treats_absolute_paths_as_relative(tmp_path):
    guard = WorkspaceGuard(tmp_path)
    resolved = guard.resolve("/etc/passwd")
    assert resolved == (tmp_path / "etc" / "passwd").resolve()


async def test_create_then_read_round_trips(tool):
    result = await _run(tool, operation="create", path="notes.txt", content="hello")
    assert result.success
    result = await _run(tool, operation="read", path="notes.txt")
    assert result.success
    assert result.output["content"] == "hello"


async def test_create_rejects_existing_file_without_overwrite(tool):
    await _run(tool, operation="create", path="notes.txt", content="a")
    result = await _run(tool, operation="create", path="notes.txt", content="b")
    assert not result.success
    assert "already exists" in result.error


async def test_write_overwrite_flag_is_enforced(tool):
    await _run(tool, operation="create", path="notes.txt", content="a")
    denied = await _run(tool, operation="write", path="notes.txt", content="b")
    assert not denied.success
    allowed = await _run(tool, operation="write", path="notes.txt", content="b", overwrite=True)
    assert allowed.success
    read_back = await _run(tool, operation="read", path="notes.txt")
    assert read_back.output["content"] == "b"


async def test_delete_removes_file(tool):
    await _run(tool, operation="create", path="notes.txt")
    result = await _run(tool, operation="delete", path="notes.txt")
    assert result.success
    exists = await _run(tool, operation="exists", path="notes.txt")
    assert exists.output["exists"] is False


async def test_list_directory_reports_entries(tool):
    await _run(tool, operation="create", path="a.txt")
    await _run(tool, operation="create_directory", path="sub")
    result = await _run(tool, operation="list_directory", path=".")
    assert result.success
    names = {entry["name"] for entry in result.output["entries"]}
    assert names == {"a.txt", "sub"}


async def test_delete_directory_requires_recursive_when_not_empty(tool):
    await _run(tool, operation="create_directory", path="sub")
    await _run(tool, operation="create", path="sub/a.txt")
    denied = await _run(tool, operation="delete_directory", path="sub")
    assert not denied.success
    allowed = await _run(tool, operation="delete_directory", path="sub", recursive=True)
    assert allowed.success


async def test_delete_directory_refuses_workspace_root(tool):
    result = await _run(tool, operation="delete_directory", path=".", recursive=True)
    assert not result.success
    assert "workspace root" in result.error


async def test_copy_and_move(tool):
    await _run(tool, operation="create", path="a.txt", content="x")
    copied = await _run(tool, operation="copy", source="a.txt", destination="b.txt")
    assert copied.success
    moved = await _run(tool, operation="move", source="b.txt", destination="c.txt")
    assert moved.success
    assert (await _run(tool, operation="exists", path="b.txt")).output["exists"] is False
    assert (await _run(tool, operation="exists", path="c.txt")).output["exists"] is True


async def test_path_traversal_is_rejected_through_the_tool(tool):
    result = await _run(tool, operation="read", path="../outside.txt")
    assert not result.success
    assert "workspace" in result.error


async def test_unknown_operation_fails_validation(tool):
    result = await _run(tool, operation="fly")
    assert not result.success
