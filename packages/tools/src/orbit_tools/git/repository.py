"""Pure parsing of `git` plumbing output into plain dicts.

`GitTool` (see `tool.py`) resolves and sandboxes the path, then delegates to
the functions here to turn `git`'s output into the shapes the tool/API
return. Nothing here touches the filesystem directly or knows about
`WorkspaceGuard` — it only interprets text already produced by `run_git`.
"""

from __future__ import annotations

from typing import Any

from orbit_tools.git.runner import run_git

_LOG_FORMAT = "%H%x1f%h%x1f%an%x1f%ae%x1f%ad%x1f%s%x1e"
_LOG_DATE_FORMAT = "iso-strict"


async def is_repository(cwd: str) -> bool:
    """Whether `cwd` is inside a git working tree."""
    result = await run_git(["rev-parse", "--is-inside-work-tree"], cwd=cwd)
    return result.ok and result.stdout.strip() == "true"


async def repository_root(cwd: str) -> str:
    """Absolute path to the repository's top-level working directory."""
    result = await run_git(["rev-parse", "--show-toplevel"], cwd=cwd)
    if not result.ok:
        raise RuntimeError(result.stderr.strip() or "Not a git repository")
    return result.stdout.strip()


async def current_branch(cwd: str) -> dict[str, Any]:
    """Current branch name (or `None` if HEAD is detached) and HEAD commit."""
    branch_result = await run_git(["symbolic-ref", "--short", "-q", "HEAD"], cwd=cwd)
    head_result = await run_git(["rev-parse", "--short", "HEAD"], cwd=cwd)
    branch = branch_result.stdout.strip() if branch_result.ok else None
    head = head_result.stdout.strip() if head_result.ok else None
    return {"branch": branch or None, "detached": branch_result.returncode != 0, "head_commit": head}


def _parse_porcelain_v2(output: str) -> dict[str, list[str]]:
    """Parse `git status --porcelain=v2 --ignored` into path buckets."""
    staged: list[str] = []
    modified: list[str] = []
    untracked: list[str] = []
    ignored: list[str] = []

    for line in output.splitlines():
        if not line:
            continue
        tag = line[0]
        if tag == "?":
            untracked.append(line[2:])
        elif tag == "!":
            ignored.append(line[2:])
        elif tag in ("1", "2"):
            # "1 <XY> ... <path>" (renames use record type "2" with an
            # extra trailing "\t<orig path>", which we ignore here).
            parts = line.split(" ", 8)
            xy = parts[1]
            path = parts[-1].split("\t")[0]
            index_status, worktree_status = xy[0], xy[1]
            if index_status != ".":
                staged.append(path)
            if worktree_status != ".":
                modified.append(path)

    return {
        "staged": sorted(set(staged)),
        "modified": sorted(set(modified)),
        "untracked": sorted(set(untracked)),
        "ignored": sorted(set(ignored)),
    }


async def status(cwd: str) -> dict[str, Any]:
    """Structured working-tree status: staged, modified, untracked, ignored."""
    result = await run_git(
        ["status", "--porcelain=v2", "--ignored", "--untracked-files=all"], cwd=cwd
    )
    if not result.ok:
        raise RuntimeError(result.stderr.strip() or "Unable to read repository status")
    buckets = _parse_porcelain_v2(result.stdout)
    is_clean = not any(buckets[key] for key in ("staged", "modified", "untracked"))
    return {**buckets, "clean": is_clean}


def _parse_log(output: str) -> list[dict[str, Any]]:
    commits: list[dict[str, Any]] = []
    for record in output.split("\x1e"):
        record = record.strip("\n")
        if not record:
            continue
        fields = record.split("\x1f")
        if len(fields) != 6:
            continue
        commit_hash, short_hash, author_name, author_email, date, subject = fields
        commits.append(
            {
                "commit": commit_hash,
                "short_commit": short_hash,
                "author_name": author_name,
                "author_email": author_email,
                "date": date,
                "subject": subject,
            }
        )
    return commits


async def log(cwd: str, *, limit: int = 20) -> list[dict[str, Any]]:
    """Recent commit history, most recent first."""
    result = await run_git(
        [
            "log",
            f"--max-count={limit}",
            f"--date={_LOG_DATE_FORMAT}",
            f"--pretty=format:{_LOG_FORMAT}",
        ],
        cwd=cwd,
    )
    if not result.ok:
        # An empty repository (no commits yet) exits non-zero; treat as no history.
        if "does not have any commits" in result.stderr or "unknown revision" in result.stderr:
            return []
        raise RuntimeError(result.stderr.strip() or "Unable to read commit history")
    return _parse_log(result.stdout)


def _parse_numstat(output: str) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for line in output.splitlines():
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added_raw, removed_raw, path = parts
        added = None if added_raw == "-" else int(added_raw)
        removed = None if removed_raw == "-" else int(removed_raw)
        files.append({"path": path, "added": added, "removed": removed, "binary": added is None})
    return files


async def diff_summary(cwd: str, *, staged: bool = False) -> dict[str, Any]:
    """Per-file added/removed line counts for the working tree or index."""
    args = ["diff", "--numstat"]
    if staged:
        args.insert(1, "--staged")
    result = await run_git(args, cwd=cwd)
    if not result.ok:
        raise RuntimeError(result.stderr.strip() or "Unable to compute diff summary")
    files = _parse_numstat(result.stdout)
    totals_added = sum(f["added"] or 0 for f in files)
    totals_removed = sum(f["removed"] or 0 for f in files)
    return {
        "staged": staged,
        "files": files,
        "files_changed": len(files),
        "total_added": totals_added,
        "total_removed": totals_removed,
    }


async def metadata(cwd: str) -> dict[str, Any]:
    """Repository-wide overview: root, branch, remotes, and cleanliness."""
    root = await repository_root(cwd)
    branch_info = await current_branch(cwd)
    status_info = await status(cwd)
    remotes_result = await run_git(["remote", "-v"], cwd=cwd)
    remotes: dict[str, str] = {}
    if remotes_result.ok:
        for line in remotes_result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                remotes.setdefault(parts[0], parts[1])
    return {
        "root": root,
        "branch": branch_info["branch"],
        "detached": branch_info["detached"],
        "head_commit": branch_info["head_commit"],
        "clean": status_info["clean"],
        "remotes": remotes,
    }
