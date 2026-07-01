import pytest

from orbit_tools import SearchTool, ToolContext, WorkspaceIndex


@pytest.fixture
def workspace(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def hello():\n    return 'hello world'\n")
    (tmp_path / "src" / "util.py").write_text("CONST = 42\n")
    (tmp_path / "README.md").write_text("# hello project\n")
    ignored = tmp_path / "node_modules"
    ignored.mkdir()
    (ignored / "lib.js").write_text("module.exports = {}\n")
    return tmp_path


@pytest.fixture
def tool(workspace):
    return SearchTool(workspace_root=workspace)


async def _run(tool, **arguments):
    return await tool.run(arguments, ToolContext())


def test_index_ignores_configured_directories(workspace):
    index = WorkspaceIndex(workspace)
    paths = {f.path for f in index.files}
    assert "node_modules/lib.js" not in paths
    assert "src/main.py" in paths


def test_index_refresh_picks_up_new_files(workspace):
    index = WorkspaceIndex(workspace)
    assert len(index.files) == 3
    (workspace / "new_file.txt").write_text("data")
    index.refresh()
    assert len(index.files) == 4


async def test_filename_search_matches_substring(tool):
    result = await _run(tool, query="main", mode="filename")
    assert result.success
    assert result.output["match_count"] == 1
    assert result.output["matches"][0]["path"] == "src/main.py"


async def test_text_search_returns_line_and_column(tool):
    result = await _run(tool, query="hello world")
    assert result.success
    matches = result.output["matches"]
    assert len(matches) == 1
    assert matches[0]["path"] == "src/main.py"
    assert matches[0]["line"] == 2
    assert matches[0]["column"] == 12


async def test_text_search_is_case_insensitive_by_default(tool):
    result = await _run(tool, query="HELLO")
    assert result.success
    assert result.output["match_count"] >= 1


async def test_regex_search_matches_pattern(tool):
    result = await _run(tool, query=r"CONST\s*=\s*\d+", mode="regex")
    assert result.success
    assert result.output["matches"][0]["path"] == "src/util.py"


async def test_regex_search_rejects_invalid_pattern(tool):
    result = await _run(tool, query="(unclosed", mode="regex")
    assert not result.success
    assert "Invalid regular expression" in result.error


async def test_extension_filter_narrows_results(tool):
    result = await _run(tool, query="hello", extensions=[".md"])
    assert result.success
    assert all(m["path"].endswith(".md") for m in result.output["matches"])


async def test_directory_filter_narrows_results(tool):
    result = await _run(tool, query="hello", directory="src")
    assert result.success
    assert all(m["path"].startswith("src/") for m in result.output["matches"])


async def test_index_status_and_refresh_operations(tool, workspace):
    status = tool.index_status()
    assert status["file_count"] == 3
    (workspace / "extra.py").write_text("x = 1\n")
    refreshed = tool.refresh_index()
    assert refreshed["file_count"] == 4
