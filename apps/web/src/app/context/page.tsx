"use client";

import { useCallback, useEffect, useState } from "react";
import type {
  ContextBundleResponse,
  FilesystemEntry,
  ProjectSummaryResponse,
  ToolResultResponse,
} from "@orbit/shared";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function ContextPage() {
  const [summary, setSummary] = useState<ProjectSummaryResponse | null>(null);
  const [files, setFiles] = useState<FilesystemEntry[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [query, setQuery] = useState("");
  const [bundle, setBundle] = useState<ContextBundleResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const loadSummary = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/context/summary`, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setSummary((await res.json()) as ProjectSummaryResponse);
    } catch {
      setError("Couldn't reach the API — is it running?");
    }
  }, []);

  const loadIndexedFiles = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/tools/filesystem/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          arguments: { operation: "list_directory", path: ".", recursive: true },
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const result = (await res.json()) as ToolResultResponse;
      if (!result.success) throw new Error(result.error ?? "Failed to list files");
      const entries = (result.output as { entries: FilesystemEntry[] }).entries;
      setFiles(entries.filter((entry) => entry.is_file));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to list indexed files");
    }
  }, []);

  useEffect(() => {
    loadSummary();
    loadIndexedFiles();
  }, [loadSummary, loadIndexedFiles]);

  const toggleSelected = (path: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  };

  const generateContext = async () => {
    if (selected.size === 0 && !query.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/context/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query.trim() || undefined,
          paths: selected.size > 0 ? Array.from(selected) : undefined,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? `HTTP ${res.status}`);
      }
      setBundle((await res.json()) as ContextBundleResponse);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate context.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container flex min-h-screen flex-col gap-6 py-16">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Context</h1>
        <p className="text-muted-foreground">
          The Context Engine gathers and structures workspace context from the search and
          filesystem tools — no reasoning or summarization happens here.
        </p>
      </div>

      {error && <p className="font-mono text-sm text-destructive">{error}</p>}

      <Card>
        <CardHeader>
          <CardTitle>Workspace statistics</CardTitle>
          <CardDescription>
            {summary ? `${summary.workspace.root}` : "Loading…"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {summary && (
            <div className="space-y-2 text-sm">
              <div className="flex gap-6 font-mono">
                <span>files: {summary.stats.total_files}</span>
                <span>size: {summary.stats.total_size}B</span>
                <span>indexed_at: {summary.workspace.indexed_at?.toFixed(0) ?? "—"}</span>
              </div>
              <div className="space-y-1">
                {summary.stats.by_extension.map((e) => (
                  <div key={e.extension || "(none)"} className="flex justify-between font-mono text-xs">
                    <span>{e.extension || "(no extension)"}</span>
                    <span>
                      {e.file_count} files, {e.total_size}B
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Indexed files</CardTitle>
            <CardDescription>Click to add/remove from the selected files below.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="max-h-80 space-y-1 overflow-y-auto">
              {files.map((entry) => (
                <button
                  key={entry.path}
                  onClick={() => toggleSelected(entry.path)}
                  className={`block w-full truncate rounded px-2 py-1 text-left font-mono text-xs ${
                    selected.has(entry.path) ? "bg-primary/10 text-primary" : "hover:bg-secondary"
                  }`}
                >
                  {entry.path}
                </button>
              ))}
              {files.length === 0 && (
                <p className="p-2 text-sm text-muted-foreground">No files indexed yet.</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Selected files ({selected.size})</CardTitle>
            <CardDescription>Passed as `paths` to `/api/v1/context/generate`.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="max-h-48 space-y-1 overflow-y-auto">
              {Array.from(selected).map((path) => (
                <div key={path} className="flex items-center justify-between font-mono text-xs">
                  <span className="truncate">{path}</span>
                  <Button size="sm" variant="ghost" onClick={() => toggleSelected(path)}>
                    Remove
                  </Button>
                </div>
              ))}
              {selected.size === 0 && (
                <p className="text-sm text-muted-foreground">No files selected.</p>
              )}
            </div>

            <input
              className="w-full rounded-md border bg-transparent px-3 py-1.5 text-sm"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="optional search query to include as context"
            />
            <Button size="sm" disabled={loading} onClick={generateContext}>
              {loading ? "Generating…" : "Generate context"}
            </Button>
          </CardContent>
        </Card>
      </div>

      {bundle && (
        <Card>
          <CardHeader>
            <CardTitle>Generated context preview</CardTitle>
            <CardDescription>
              {bundle.files.length} file{bundle.files.length === 1 ? "" : "s"}, {bundle.matches.length}{" "}
              match{bundle.matches.length === 1 ? "" : "es"}
              {bundle.truncated ? " (truncated by builder limits)" : ""}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <pre className="max-h-96 overflow-auto whitespace-pre-wrap break-all rounded-md border p-2 font-mono text-xs">
              {JSON.stringify(bundle, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </main>
  );
}
