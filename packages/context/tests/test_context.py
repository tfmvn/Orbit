import pytest

from orbit_context import ContextBuilder, ContextBuilderConfig, ContextEngine, ContextEngineError
from orbit_tools import FilesystemTool, SearchTool, ToolRegistry


@pytest.fixture
def workspace(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def hello():\n    return 'hello world'\n")
    (tmp_path / "src" / "util.py").write_text("CONST = 42\n")
    (tmp_path / "README.md").write_text("# hello project\n")
    return tmp_path


@pytest.fixture
def registry(workspace):
    reg = ToolRegistry()
    reg.register(SearchTool(workspace_root=workspace))
    reg.register(FilesystemTool(workspace_root=workspace))
    return reg


@pytest.fixture
def engine(registry):
    return ContextEngine(registry)


def test_builder_select_files_is_deterministic_and_capped():
    builder = ContextBuilder(ContextBuilderConfig(max_files=2))
    candidates = [("b.py", 10), ("a.py", 5), ("c.py", 20)]
    selected, truncated = builder.select_files(candidates)
    assert selected == [("a.py", 5), ("b.py", 10)]
    assert truncated is True


def test_builder_select_files_respects_ignore_paths():
    builder = ContextBuilder(ContextBuilderConfig(ignore_paths=("node_modules",)))
    candidates = [("node_modules/lib.js", 1), ("src/main.py", 2)]
    selected, truncated = builder.select_files(candidates)
    assert selected == [("src/main.py", 2)]
    assert truncated is False


def test_builder_clip_content_marks_truncation():
    builder = ContextBuilder(ContextBuilderConfig(max_file_size=5))
    content, truncated = builder.clip_content("hello world")
    assert truncated is True
    assert len(content.encode("utf-8")) <= 5


async def test_project_summary_reports_workspace_and_stats(engine, workspace):
    summary = await engine.project_summary()
    assert summary.workspace.root == str(workspace)
    assert summary.stats.total_files == 3
    extensions = {e.extension for e in summary.stats.by_extension}
    assert extensions == {".py", ".md"}


async def test_search_matches_returns_typed_results(engine):
    matches = await engine.search_matches("hello")
    assert any(m.path == "src/main.py" for m in matches)


async def test_load_files_reads_and_sorts_deterministically(engine):
    files = await engine.load_files(["src/util.py", "src/main.py"])
    assert [f.path for f in files] == ["src/main.py", "src/util.py"]
    assert files[0].content is not None


async def test_load_files_skips_missing_paths(engine):
    files = await engine.load_files(["does/not/exist.py"])
    assert files == []


async def test_build_context_from_query_assembles_bundle(engine):
    bundle = await engine.build_context(query="hello")
    assert bundle.query == "hello"
    assert bundle.matches
    assert any(f.path == "src/main.py" for f in bundle.files)
    assert bundle.stats.total_files == 3


async def test_build_context_from_explicit_paths(engine):
    bundle = await engine.build_context(paths=["src/util.py"])
    assert bundle.query is None
    assert [f.path for f in bundle.files] == ["src/util.py"]


async def test_build_context_requires_no_registered_search_raises(workspace):
    empty_registry = ToolRegistry()
    empty_registry.register(FilesystemTool(workspace_root=workspace))
    engine = ContextEngine(empty_registry)
    with pytest.raises(ContextEngineError):
        await engine.workspace_info()


async def test_build_context_respects_max_files_limit(registry):
    engine = ContextEngine(registry, builder=ContextBuilder(ContextBuilderConfig(max_files=1)))
    bundle = await engine.build_context(query="hello")
    assert len(bundle.files) <= 1
    assert bundle.truncated is True
