"""`FilesystemTool`: sandboxed, asynchronous file and directory operations.

Every path argument is resolved through a `WorkspaceGuard` before any I/O
happens, so callers can never read, write, or delete outside the configured
workspace root. Blocking filesystem calls run in a worker thread via
`asyncio.to_thread` so the tool never blocks the event loop.
"""

from __future__ import annotations

import asyncio
import shutil
import stat as stat_module
from pathlib import Path
from typing import Any

from orbit_tools.context import ToolContext
from orbit_tools.filesystem.workspace import WorkspaceError, WorkspaceGuard
from orbit_tools.tool import Tool, ToolError, ToolMetadata

_OPERATIONS = {
    "read",
    "write",
    "create",
    "delete",
    "create_directory",
    "delete_directory",
    "list_directory",
    "copy",
    "move",
    "metadata",
    "exists",
}
_PAIR_OPERATIONS = {"copy", "move"}


class FilesystemTool(Tool):
    """File and directory operations scoped to a workspace root.

    A single `operation` argument selects the action; see `metadata` for
    the full argument shape. All paths are relative to the workspace root
    this tool was constructed with.
    """

    def __init__(self, workspace_root: str | Path) -> None:
        self._workspace = WorkspaceGuard(workspace_root)

    @property
    def workspace_root(self) -> Path:
        return self._workspace.root

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="filesystem",
            description=(
                "Read, write, and manage files and directories inside Orbit's "
                "sandboxed workspace. All paths are relative to the workspace root; "
                "access outside it is always rejected."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": sorted(_OPERATIONS)},
                    "path": {"type": "string", "description": "Relative to the workspace root."},
                    "source": {"type": "string", "description": "Used by copy/move."},
                    "destination": {"type": "string", "description": "Used by copy/move."},
                    "content": {"type": "string", "description": "Used by write/create."},
                    "encoding": {"type": "string", "default": "utf-8"},
                    "overwrite": {"type": "boolean", "default": False},
                    "recursive": {"type": "boolean", "default": False},
                    "create_parents": {"type": "boolean", "default": True},
                },
                "required": ["operation"],
            },
        )

    def validate(self, arguments: dict[str, Any]) -> None:
        super().validate(arguments)
        operation = arguments.get("operation")
        if operation not in _OPERATIONS:
            raise ToolError(f"Unknown operation '{operation}'")
        if operation in _PAIR_OPERATIONS:
            missing = [key for key in ("source", "destination") if not arguments.get(key)]
            if missing:
                raise ToolError(f"Missing required argument(s): {', '.join(missing)}")
            return
        if not arguments.get("path"):
            if operation == "list_directory":
                arguments["path"] = "."
            else:
                raise ToolError("Missing required argument: path")

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> Any:
        handler = getattr(self, f"_op_{arguments['operation']}")
        return await asyncio.to_thread(handler, arguments)

    # -- path resolution -----------------------------------------------

    def _resolve(self, raw: str) -> Path:
        try:
            return self._workspace.resolve(raw)
        except WorkspaceError as exc:
            raise ToolError(str(exc)) from exc

    def _describe(self, path: Path) -> dict[str, Any]:
        info = path.stat()
        return {
            "name": path.name,
            "path": str(path.relative_to(self._workspace.root)),
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "size": info.st_size,
            "modified": info.st_mtime,
            "mode": stat_module.filemode(info.st_mode),
        }

    # -- operations (each runs in a worker thread) ----------------------

    def _op_read(self, args: dict[str, Any]) -> dict[str, Any]:
        path = self._resolve(args["path"])
        if not path.exists():
            raise ToolError(f"No such file: '{args['path']}'")
        if not path.is_file():
            raise ToolError(f"'{args['path']}' is not a file")
        encoding = args.get("encoding", "utf-8")
        try:
            content = path.read_text(encoding=encoding)
        except UnicodeDecodeError as exc:
            raise ToolError(f"'{args['path']}' is not valid {encoding} text: {exc}") from exc
        return {"path": args["path"], "content": content, "size": path.stat().st_size}

    def _op_write(self, args: dict[str, Any]) -> dict[str, Any]:
        path = self._resolve(args["path"])
        if path.is_dir():
            raise ToolError(f"'{args['path']}' is a directory")
        if path.exists() and not args.get("overwrite", False):
            raise ToolError(f"'{args['path']}' already exists (set overwrite=true to replace it)")
        if args.get("create_parents", True):
            path.parent.mkdir(parents=True, exist_ok=True)
        elif not path.parent.exists():
            raise ToolError(f"Parent directory does not exist for '{args['path']}'")
        path.write_text(args.get("content", ""), encoding=args.get("encoding", "utf-8"))
        return {"path": args["path"], "bytes_written": path.stat().st_size}

    def _op_create(self, args: dict[str, Any]) -> dict[str, Any]:
        path = self._resolve(args["path"])
        if path.exists() and not args.get("overwrite", False):
            raise ToolError(f"'{args['path']}' already exists")
        if args.get("create_parents", True):
            path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(args.get("content", ""), encoding=args.get("encoding", "utf-8"))
        return {"path": args["path"], "created": True}

    def _op_delete(self, args: dict[str, Any]) -> dict[str, Any]:
        path = self._resolve(args["path"])
        if not path.exists():
            raise ToolError(f"No such file: '{args['path']}'")
        if path.is_dir():
            raise ToolError(f"'{args['path']}' is a directory; use delete_directory")
        path.unlink()
        return {"path": args["path"], "deleted": True}

    def _op_create_directory(self, args: dict[str, Any]) -> dict[str, Any]:
        path = self._resolve(args["path"])
        try:
            path.mkdir(
                parents=args.get("create_parents", True),
                exist_ok=args.get("overwrite", False),
            )
        except FileExistsError as exc:
            raise ToolError(f"'{args['path']}' already exists") from exc
        return {"path": args["path"], "created": True}

    def _op_delete_directory(self, args: dict[str, Any]) -> dict[str, Any]:
        path = self._resolve(args["path"])
        if path == self._workspace.root:
            raise ToolError("Refusing to delete the workspace root")
        if not path.exists():
            raise ToolError(f"No such directory: '{args['path']}'")
        if not path.is_dir():
            raise ToolError(f"'{args['path']}' is not a directory")
        if any(path.iterdir()) and not args.get("recursive", False):
            raise ToolError(f"'{args['path']}' is not empty (set recursive=true to remove it)")
        if args.get("recursive", False):
            shutil.rmtree(path)
        else:
            path.rmdir()
        return {"path": args["path"], "deleted": True}

    def _op_list_directory(self, args: dict[str, Any]) -> dict[str, Any]:
        path = self._resolve(args["path"])
        if not path.exists():
            raise ToolError(f"No such directory: '{args['path']}'")
        if not path.is_dir():
            raise ToolError(f"'{args['path']}' is not a directory")
        pattern = "**/*" if args.get("recursive", False) else "*"
        entries = [self._describe(entry) for entry in sorted(path.glob(pattern))]
        return {"path": args["path"], "entries": entries}

    def _op_copy(self, args: dict[str, Any]) -> dict[str, Any]:
        source = self._resolve(args["source"])
        destination = self._resolve(args["destination"])
        if not source.exists():
            raise ToolError(f"No such file or directory: '{args['source']}'")
        if destination.exists() and not args.get("overwrite", False):
            raise ToolError(f"'{args['destination']}' already exists")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)
        return {"source": args["source"], "destination": args["destination"]}

    def _op_move(self, args: dict[str, Any]) -> dict[str, Any]:
        source = self._resolve(args["source"])
        destination = self._resolve(args["destination"])
        if not source.exists():
            raise ToolError(f"No such file or directory: '{args['source']}'")
        if destination.exists():
            if not args.get("overwrite", False):
                raise ToolError(f"'{args['destination']}' already exists")
            if destination.is_dir():
                shutil.rmtree(destination)
            else:
                destination.unlink()
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        return {"source": args["source"], "destination": args["destination"]}

    def _op_metadata(self, args: dict[str, Any]) -> dict[str, Any]:
        path = self._resolve(args["path"])
        if not path.exists():
            raise ToolError(f"No such file or directory: '{args['path']}'")
        return self._describe(path)

    def _op_exists(self, args: dict[str, Any]) -> dict[str, Any]:
        path = self._resolve(args["path"])
        return {"path": args["path"], "exists": path.exists()}
