"use client";

import { useCallback, useEffect, useState } from "react";
import type { ToolMetadataResponse, ToolResultResponse } from "@orbit/shared";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type RunState = {
  status: "idle" | "running" | "done";
  result?: ToolResultResponse;
  error?: string;
};

export default function ToolsPage() {
  const [tools, setTools] = useState<ToolMetadataResponse[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [echoMessage, setEchoMessage] = useState("hello, orbit");
  const [runs, setRuns] = useState<Record<string, RunState>>({});

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/tools`, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setTools((await res.json()) as ToolMetadataResponse[]);
      setLoadError(null);
    } catch {
      setLoadError("Couldn't reach the API — is it running?");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const runTool = async (name: string, args: Record<string, unknown>) => {
    setRuns((prev) => ({ ...prev, [name]: { status: "running" } }));
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/tools/${name}/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ arguments: args }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const result = (await res.json()) as ToolResultResponse;
      setRuns((prev) => ({ ...prev, [name]: { status: "done", result } }));
    } catch {
      setRuns((prev) => ({
        ...prev,
        [name]: { status: "done", error: "Execution request failed." },
      }));
    }
  };

  return (
    <main className="container flex min-h-screen flex-col gap-6 py-16">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Tools</h1>
        <p className="text-muted-foreground">
          Tools registered with the tool registry. These are lightweight demonstration tools
          proving the tool framework works — no AI, agent, or planner logic yet.
        </p>
      </div>

      {loadError && <p className="font-mono text-sm text-destructive">{loadError}</p>}

      <div className="grid gap-4 sm:grid-cols-2">
        {tools.map((tool) => {
          const run = runs[tool.name];
          return (
            <Card key={tool.name}>
              <CardHeader>
                <CardTitle className="font-mono">{tool.name}</CardTitle>
                <CardDescription>{tool.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {tool.name === "echo" && (
                  <input
                    className="w-full rounded-md border bg-transparent px-3 py-1.5 text-sm"
                    value={echoMessage}
                    onChange={(e) => setEchoMessage(e.target.value)}
                    placeholder="message to echo"
                  />
                )}

                <Button
                  size="sm"
                  disabled={run?.status === "running"}
                  onClick={() =>
                    runTool(tool.name, tool.name === "echo" ? { message: echoMessage } : {})
                  }
                >
                  {run?.status === "running" ? "Running…" : "Run"}
                </Button>

                {run?.error && <p className="text-sm text-destructive">{run.error}</p>}

                {run?.result && (
                  <div className="rounded-md border p-2 text-sm">
                    <div className="mb-1 flex items-center justify-between">
                      <span
                        className={
                          run.result.success ? "font-medium text-primary" : "font-medium text-destructive"
                        }
                      >
                        {run.result.success ? "success" : "failed"}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {run.result.execution_time.toFixed(4)}s
                      </span>
                    </div>
                    <pre className="overflow-x-auto whitespace-pre-wrap break-all font-mono text-xs">
                      {JSON.stringify(run.result.output ?? run.result.error, null, 2)}
                    </pre>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </main>
  );
}
