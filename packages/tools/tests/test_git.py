import subprocess

import pytest

from orbit_tools import GitTool, ToolContext


def _git(*args: str, cwd) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    """A tiny initialized repo with one committed file and one dirty change."""
    _git("init", "-q", cwd=tmp_path)
    _git("config", "user.email", "orbit@example.com", cwd=tmp_path)
    _git("config", "user.name", "Orbit", cwd=tmp_path)
    (tmp_path / "committed.txt").write_text("hello\n")
    _git("add", "committed.txt", cwd=tmp_path)
    _git("commit", "-q", "-m", "initial commit", cwd=tmp_path)
    (tmp_path / "committed.txt").write_text("hello again\n")
    (tmp_path / "untracked.txt").write_text("new\n")
    return tmp_path


@pytest.fixture
def tool(tmp_path):
    return GitTool(workspace_root=tmp_path)


async def _run(tool, **arguments):
    return await tool.run(arguments, ToolContext())


async def test_detect_false_outside_repository(tool):
    result = await _run(tool, operation="detect", path=".")
    assert result.success
    assert result.output["is_repository"] is False


async def test_detect_true_inside_repository(repo):
    tool = GitTool(workspace_root=repo)
    result = await _run(tool, operation="detect", path=".")
    assert result.success
    assert result.output["is_repository"] is True


async def test_status_reports_modified_and_untracked(repo):
    tool = GitTool(workspace_root=repo)
    result = await _run(tool, operation="status", path=".")
    assert result.success
    assert result.output["modified"] == ["committed.txt"]
    assert result.output["untracked"] == ["untracked.txt"]
    assert result.output["clean"] is False


async def test_branch_reports_head(repo):
    tool = GitTool(workspace_root=repo)
    result = await _run(tool, operation="branch", path=".")
    assert result.success
    assert result.output["head_commit"] is not None


async def test_log_returns_recent_commits(repo):
    tool = GitTool(workspace_root=repo)
    result = await _run(tool, operation="log", path=".", limit=5)
    assert result.success
    assert result.output["count"] == 1
    assert result.output["commits"][0]["subject"] == "initial commit"


async def test_diff_summary_reports_line_counts(repo):
    tool = GitTool(workspace_root=repo)
    result = await _run(tool, operation="diff", path=".")
    assert result.success
    assert result.output["files_changed"] == 1
    assert result.output["files"][0]["path"] == "committed.txt"


async def test_operations_fail_outside_a_repository(tool):
    result = await _run(tool, operation="status", path=".")
    assert not result.success
    assert "not a Git repository" in result.error


async def test_unknown_operation_is_rejected(tool):
    result = await _run(tool, operation="commit", path=".")
    assert not result.success
    assert "Unknown operation" in result.error


async def test_path_traversal_is_rejected(tool):
    result = await _run(tool, operation="detect", path="../outside")
    assert not result.success
