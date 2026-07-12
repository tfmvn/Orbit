"use client";

import { useCallback, useEffect, useState } from "react";
import type {
  GitBranchResponse,
  GitLogResponse,
  GitStatusResponse,
} from "@orbit/shared";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function FileList({ title, files }: { title: string; files: string[] }) {
  return (
    <div className="space-y-1">
      <p className="text-xs font-medium text-muted-foreground">
        {title} ({files.length})
      </p>
      <div className="max-h-32 space-y-0.5 overflow-y-auto">
        {files.map((path) => (
          <div key={path} className="truncate font-mono text-xs">
            {path}
          </div>
        ))}
        {files.length === 0 && <p className="font-mono text-xs text-muted-foreground">—</p>}
      </div>
    </div>
  );
}

export function GitPanel() {
  const [branch, setBranch] = useState<GitBranchResponse | null>(null);
  const [status, setStatus] = useState<GitStatusResponse | null>(null);
  const [log, setLog] = useState<GitLogResponse | null>(null);
  const [notRepo, setNotRepo] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setNotRepo(false);
    setError(null);
    try {
      const [branchRes, statusRes, logRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/v1/git/branch`, { cache: "no-store" }),
        fetch(`${API_BASE_URL}/api/v1/git/status`, { cache: "no-store" }),
        fetch(`${API_BASE_URL}/api/v1/git/log?limit=10`, { cache: "no-store" }),
      ]);
      if (branchRes.status === 400 || statusRes.status === 400 || logRes.status === 400) {
        setNotRepo(true);
        setBranch(null);
        setStatus(null);
        setLog(null);
        return;
      }
      if (!branchRes.ok || !statusRes.ok || !logRes.ok) {
        throw new Error("HTTP error fetching Git info");
      }
      setBranch((await branchRes.json()) as GitBranchResponse);
      setStatus((await statusRes.json()) as GitStatusResponse);
      setLog((await logRes.json()) as GitLogResponse);
    } catch {
      setError("Couldn't reach the API — is it running?");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Git</CardTitle>
            <CardDescription>
              Read-only repository inspection for the workspace root — no operation modifies
              the repository.
            </CardDescription>
          </div>
          <Button size="sm" variant="outline" disabled={loading} onClick={load}>
            {loading ? "Loading…" : "Refresh"}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <p className="text-sm text-destructive">{error}</p>}
        {notRepo && !error && (
          <p className="text-sm text-muted-foreground">
            The workspace root isn&apos;t a Git repository.
          </p>
        )}

        {branch && status && (
          <div className="flex flex-wrap items-center gap-4 font-mono text-sm">
            <span>
              branch: <span className="text-primary">{branch.branch ?? "(detached)"}</span>
            </span>
            <span className={status.clean ? "text-primary" : "text-destructive"}>
              {status.clean ? "clean" : "dirty"}
            </span>
          </div>
        )}

        {status && (
          <div className="grid gap-4 sm:grid-cols-3">
            <FileList title="Staged" files={status.staged} />
            <FileList title="Modified" files={status.modified} />
            <FileList title="Untracked" files={status.untracked} />
          </div>
        )}

        {log && (
          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground">
              Recent commits ({log.count})
            </p>
            <div className="max-h-48 space-y-1 overflow-y-auto">
              {log.commits.map((commit) => (
                <div key={commit.commit} className="flex gap-2 font-mono text-xs">
                  <span className="text-muted-foreground">{commit.short_commit}</span>
                  <span className="truncate">{commit.subject}</span>
                </div>
              ))}
              {log.commits.length === 0 && (
                <p className="font-mono text-xs text-muted-foreground">No commits yet.</p>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
