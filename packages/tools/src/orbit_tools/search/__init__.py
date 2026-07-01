"""Search tool: Orbit's first code-intelligence capability.

Exposes `SearchTool` plus `WorkspaceIndex`, the non-semantic file-discovery
cache it's built on. Filename, full-text, and regex search only — no
embeddings or vector search belong here; that's a future release's layer
on top of this one.
"""

from orbit_tools.search.engine import SearchMatch
from orbit_tools.search.index import IndexedFile, WorkspaceIndex
from orbit_tools.search.tool import SearchTool

__all__ = ["SearchTool", "WorkspaceIndex", "IndexedFile", "SearchMatch"]
