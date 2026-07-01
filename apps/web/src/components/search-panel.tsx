"use client";

import { useCallback, useEffect, useState } from "react";
import type { IndexStatusResponse, SearchResponse } from "@orbit/shared";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type Mode = "filename" | "text" | "regex";

export function SearchPanel() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<Mode>("text");
  const [caseSensitive, setCaseSensitive] = useState(false);
  const [extensions, setExtensions] = useState("");
  const [directory, setDirectory] = useState("");
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [status, setStatus] = useState<IndexStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const loadStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/search/index`, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setStatus((await res.json()) as IndexStatusResponse);
    } catch {
      setError("Couldn't reach the API — is it running?");
    }
  }, []);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  const refreshIndex = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/search/index/refresh`, { method: "POST" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setStatus((await res.json()) as IndexStatusResponse);
      setError(null);
    } catch {
      setError("Failed to refresh the index.");
    }
  };

  const runSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          mode,
          case_sensitive: caseSensitive,
          extensions: extensions.trim()
            ? extensions.split(",").map((e) => e.trim()).filter(Boolean)
            : undefined,
          directory: directory.trim() || undefined,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? `HTTP ${res.status}`);
      }
      setResult((await res.json()) as SearchResponse);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Search</CardTitle>
        <CardDescription>
          {status
            ? `Index: ${status.file_count} files at ${status.root}.`
            : "Loading workspace index…"}{" "}
          Filename, full-text, and regex search — no AI model involved.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <p className="text-sm text-destructive">{error}</p>}

        <div className="flex flex-wrap items-center gap-2">
          <input
            className="min-w-[12rem] flex-1 rounded-md border bg-transparent px-3 py-1.5 text-sm"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && runSearch()}
            placeholder="search query"
          />
          <select
            className="rounded-md border bg-transparent px-2 py-1.5 text-sm"
            value={mode}
            onChange={(e) => setMode(e.target.value as Mode)}
          >
            <option value="filename">filename</option>
            <option value="text">text</option>
            <option value="regex">regex</option>
          </select>
          <Button size="sm" disabled={loading} onClick={runSearch}>
            {loading ? "Searching…" : "Search"}
          </Button>
          <Button size="sm" variant="outline" onClick={refreshIndex}>
            Refresh index
          </Button>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
          <label className="flex items-center gap-1">
            <input
              type="checkbox"
              checked={caseSensitive}
              onChange={(e) => setCaseSensitive(e.target.checked)}
            />
            case-sensitive
          </label>
          <input
            className="w-40 rounded-md border bg-transparent px-2 py-1 text-sm"
            value={extensions}
            onChange={(e) => setExtensions(e.target.value)}
            placeholder="extensions, e.g. .py,.ts"
          />
          <input
            className="w-40 rounded-md border bg-transparent px-2 py-1 text-sm"
            value={directory}
            onChange={(e) => setDirectory(e.target.value)}
            placeholder="directory filter"
          />
        </div>

        {result && (
          <div className="space-y-2 rounded-md border p-2 text-sm">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>
                {result.match_count} match{result.match_count === 1 ? "" : "es"} across{" "}
                {result.files_searched} files
              </span>
              <span>{result.search_duration.toFixed(4)}s</span>
            </div>
            <div className="max-h-80 space-y-1 overflow-y-auto">
              {result.matches.map((m, i) => (
                <div key={`${m.path}-${m.line}-${i}`} className="rounded px-2 py-1 hover:bg-secondary">
                  <div className="font-mono text-xs text-muted-foreground">
                    {m.path}
                    {m.line !== null ? `:${m.line}${m.column !== null ? `:${m.column}` : ""}` : ""}
                  </div>
                  {m.line !== null && (
                    <div className="truncate font-mono text-xs">{m.text}</div>
                  )}
                </div>
              ))}
              {result.matches.length === 0 && (
                <p className="p-2 text-sm text-muted-foreground">No matches.</p>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
