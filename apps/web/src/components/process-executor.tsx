"use client";

import { useRef, useState } from "react";
import type { ProcessResultResponse, ProcessStatusResponse } from "@orbit/shared";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const POLL_INTERVAL_MS = 800;

async function postJson<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail ?? `HTTP ${res.status}`);
  return (await res.json()) as T;
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return (await res.json()) as T;
}

export function ProcessExecutor() {
  const [commandLine, setCommandLine] = useState("echo hello, orbit");
  const [cwd, setCwd] = useState(".");
  const [run, setRun] = useState<ProcessResultResponse | ProcessStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = () => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = null;
  };

  const poll = (executionId: string) => {
    stopPolling();
    pollRef.current = setInterval(async () => {
      try {
        const status = await getJson<ProcessStatusResponse>(`/api/v1/process/${executionId}/status`);
        if (status.status === "running") {
          setRun(status);
          return;
        }
        stopPolling();
        const result = await getJson<ProcessResultResponse>(`/api/v1/process/${executionId}/result`);
        setRun(result);
      } catch {
        stopPolling();
        setError("Lost connection while polling execution status.");
      }
    }, POLL_INTERVAL_MS);
  };

  const execute = async () => {
    const command = commandLine.trim().split(/\s+/).filter(Boolean);
    if (command.length === 0) return;
    setError(null);
    try {
      const status = await postJson<ProcessStatusResponse>("/api/v1/process/execute", {
        command,
        cwd,
      });
      setRun(status);
      poll(status.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start execution.");
    }
  };

  const cancel = async () => {
    if (!run) return;
    try {
      const status = await postJson<ProcessStatusResponse>(`/api/v1/process/${run.id}/cancel`);
      setRun(status);
      stopPolling();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to cancel execution.");
    }
  };

  const result = run && "stdout" in run ? (run as ProcessResultResponse) : null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Process Execution</CardTitle>
        <CardDescription>
          Runs a command (no shell — arguments are split on whitespace) inside the sandboxed
          workspace. This is Orbit&apos;s execution foundation for future tools like Git and
          package managers.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {error && <p className="text-sm text-destructive">{error}</p>}

        <div className="flex flex-col gap-2 sm:flex-row">
          <input
            className="w-full rounded-md border bg-transparent px-3 py-1.5 font-mono text-sm"
            value={commandLine}
            onChange={(e) => setCommandLine(e.target.value)}
            placeholder="echo hello, orbit"
          />
          <input
            className="w-full shrink-0 rounded-md border bg-transparent px-3 py-1.5 font-mono text-sm sm:w-32"
            value={cwd}
            onChange={(e) => setCwd(e.target.value)}
            placeholder="cwd"
          />
        </div>

        <div className="flex gap-2">
          <Button size="sm" disabled={run?.status === "running"} onClick={execute}>
            {run?.status === "running" ? "Running…" : "Run"}
          </Button>
          {run?.status === "running" && (
            <Button size="sm" variant="outline" onClick={cancel}>
              Cancel
            </Button>
          )}
        </div>

        {run && (
          <div className="space-y-2 rounded-md border p-2 text-sm">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="truncate font-mono text-xs text-muted-foreground">
                {run.command.join(" ")}
              </span>
              <span
                className={
                  run.status === "completed"
                    ? "font-medium text-primary"
                    : run.status === "running"
                      ? "font-medium text-muted-foreground"
                      : "font-medium text-destructive"
                }
              >
                {run.status}
              </span>
            </div>
            <div className="flex flex-wrap gap-x-4 text-xs text-muted-foreground">
              {result && <span>exit code: {result.exit_code ?? "—"}</span>}
              <span>duration: {run.duration !== null ? `${run.duration.toFixed(2)}s` : "—"}</span>
              {run.pid !== null && <span>pid: {run.pid}</span>}
            </div>
            {result && (
              <>
                <div>
                  <p className="mb-1 text-xs font-medium text-muted-foreground">stdout</p>
                  <pre className="max-h-48 overflow-auto whitespace-pre-wrap break-all rounded bg-secondary p-2 font-mono text-xs">
                    {result.stdout || "(empty)"}
                  </pre>
                </div>
                <div>
                  <p className="mb-1 text-xs font-medium text-muted-foreground">stderr</p>
                  <pre className="max-h-48 overflow-auto whitespace-pre-wrap break-all rounded bg-secondary p-2 font-mono text-xs">
                    {result.stderr || "(empty)"}
                  </pre>
                </div>
              </>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
