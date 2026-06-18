"use client";

import { useCallback, useEffect, useState } from "react";
import type { FilesystemEntry, ToolResultResponse, WorkspaceInfoResponse } from "@orbit/shared";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type Selected = { path: string; content: string; meta?: FilesystemEntry };

async function runFilesystem(
  operation: string,
  args: Record<string, unknown>,
): Promise<ToolResultResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/tools/filesystem/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ arguments: { operation, ...args } }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return (await res.json()) as ToolResultResponse;
}

export function FileExplorer() {
  const [workspace, setWorkspace] = useState<WorkspaceInfoResponse | null>(null);
  const [path, setPath] = useState(".");
  const [entries, setEntries] = useState<FilesystemEntry[]>([]);
  const [selected, setSelected] = useState<Selected | null>(null);
  const [newFileName, setNewFileName] = useState("");
  const [error, setError] = useState<string | null>(null);

  const loadWorkspace = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/workspace`, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setWorkspace((await res.json()) as WorkspaceInfoResponse);
    } catch {
      setError("Couldn't reach the API — is it running?");
    }
  }, []);

  const loadDirectory = useCallback(async (targetPath: string) => {
    try {
      const result = await runFilesystem("list_directory", { path: targetPath });
      if (!result.success) throw new Error(result.error ?? "Failed to list directory");
      setEntries((result.output as { entries: FilesystemEntry[] }).entries);
      setPath(targetPath);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to list directory");
    }
  }, []);

  useEffect(() => {
    loadWorkspace();
    loadDirectory(".");
  }, [loadWorkspace, loadDirectory]);

  const openEntry = async (entry: FilesystemEntry) => {
    if (entry.is_dir) {
      setSelected(null);
      await loadDirectory(entry.path);
      return;
    }
    try {
      const [readResult, metaResult] = await Promise.all([
        runFilesystem("read", { path: entry.path }),
        runFilesystem("metadata", { path: entry.path }),
      ]);
      if (!readResult.success) throw new Error(readResult.error ?? "Failed to read file");
      setSelected({
        path: entry.path,
        content: (readResult.output as { content: string }).content,
        meta: metaResult.success ? (metaResult.output as FilesystemEntry) : undefined,
      });
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to read file");
    }
  };

  const goUp = () => {
    if (path === ".") return;
    const parent = path.split("/").slice(0, -1).join("/");
    setSelected(null);
    loadDirectory(parent || ".");
  };

  const createFile = async () => {
    const name = newFileName.trim();
    if (!name) return;
    const target = path === "." ? name : `${path}/${name}`;
    try {
      const result = await runFilesystem("create", { path: target, content: "" });
      if (!result.success) throw new Error(result.error ?? "Failed to create file");
      setNewFileName("");
      await loadDirectory(path);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create file");
    }
  };

  const deleteEntry = async (entry: FilesystemEntry) => {
    try {
      const result = await runFilesystem("delete", { path: entry.path });
      if (!result.success) throw new Error(result.error ?? "Failed to delete file");
      if (selected?.path === entry.path) setSelected(null);
      await loadDirectory(path);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete file");
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>File Explorer</CardTitle>
        <CardDescription>
          {workspace ? `Sandboxed workspace at ${workspace.root}.` : "Loading workspace…"} No
          access outside this root is possible.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <p className="text-sm text-destructive">{error}</p>}

        <div className="flex items-center gap-2">
          <Button size="sm" variant="outline" onClick={goUp} disabled={path === "."}>
            Up
          </Button>
          <span className="truncate font-mono text-sm text-muted-foreground">
            /{path === "." ? "" : path}
          </span>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1 rounded-md border p-2">
            {entries.length === 0 && (
              <p className="p-2 text-sm text-muted-foreground">Empty directory.</p>
            )}
            {entries.map((entry) => (
              <div
                key={entry.path}
                className="flex items-center justify-between gap-2 rounded px-2 py-1 text-sm hover:bg-secondary"
              >
                <button
                  className="flex-1 truncate text-left font-mono"
                  onClick={() => openEntry(entry)}
                >
                  {entry.is_dir ? "📁" : "📄"} {entry.name}
                </button>
                <span className="shrink-0 text-xs text-muted-foreground">
                  {entry.is_dir ? "" : `${entry.size}B`}
                </span>
                {!entry.is_dir && (
                  <Button size="sm" variant="ghost" onClick={() => deleteEntry(entry)}>
                    Delete
                  </Button>
                )}
              </div>
            ))}
          </div>

          <div className="space-y-2 rounded-md border p-2">
            {selected ? (
              <>
                <p className="truncate font-mono text-xs text-muted-foreground">
                  {selected.path}
                  {selected.meta &&
                    ` · ${selected.meta.size}B · ${selected.meta.mode} · ${new Date(
                      selected.meta.modified * 1000,
                    ).toLocaleString()}`}
                </p>
                <pre className="max-h-64 overflow-auto whitespace-pre-wrap break-all font-mono text-xs">
                  {selected.content}
                </pre>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">Select a file to view its contents.</p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <input
            className="w-full rounded-md border bg-transparent px-3 py-1.5 text-sm"
            value={newFileName}
            onChange={(e) => setNewFileName(e.target.value)}
            placeholder="new-file.txt"
          />
          <Button size="sm" onClick={createFile}>
            Create
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
