from orbit_context import ContextBundle, ExtensionBreakdown, ProjectStats, WorkspaceInfo
from orbit_providers.provider import GenerationParameters, GenerationRequest


def _bundle() -> ContextBundle:
    return ContextBundle(
        workspace=WorkspaceInfo(root="/workspace", file_count=1, indexed_at=1.0),
        stats=ProjectStats(total_files=1, total_size=10, by_extension=[ExtensionBreakdown(".py", 1, 10)]),
        files=[],
        matches=[],
        query=None,
        generated_at=1.0,
        truncated=False,
    )


def test_combined_prompt_without_context_is_unchanged() -> None:
    request = GenerationRequest(prompt="hello")
    assert request.combined_prompt() == "hello"


def test_combined_prompt_folds_in_context() -> None:
    request = GenerationRequest(prompt="hello", context=_bundle())
    combined = request.combined_prompt()
    assert "/workspace" in combined
    assert combined.endswith("hello")


def test_generation_parameters_to_dict_omits_nothing() -> None:
    params = GenerationParameters(temperature=0.5)
    assert params.to_dict() == {"temperature": 0.5, "top_p": None, "max_tokens": None, "stop": None}
