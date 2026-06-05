"use client";

import { useCallback, useEffect, useState } from "react";
import type { TaskResponse, TaskStatus } from "@orbit/shared";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const POLL_INTERVAL_MS = 2000;

const GROUPS: { status: TaskStatus; label: string }[] = [
  { status: "queued", label: "Queued" },
  { status: "running", label: "Running" },
  { status: "completed", label: "Completed" },
  { status: "failed", label: "Failed" },
];

export default function TasksPage() {
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/tasks`, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setTasks((await res.json()) as TaskResponse[]);
      setError(null);
    } catch {
      setError("Couldn't reach the API — is it running?");
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [refresh]);

  const cancelTask = async (id: string) => {
    await fetch(`${API_BASE_URL}/api/v1/tasks/${id}/cancel`, { method: "POST" });
    refresh();
  };

  return (
    <main className="container flex min-h-screen flex-col gap-6 py-16">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Tasks</h1>
        <p className="text-muted-foreground">
          A placeholder view over the runtime&apos;s task queue. Submitted tasks fail with
          &quot;no handler registered&quot; until a future subsystem registers one.
        </p>
      </div>

      {error && <p className="font-mono text-sm text-destructive">{error}</p>}

      <div className="grid gap-4 sm:grid-cols-2">
        {GROUPS.map((group) => {
          const groupTasks = tasks.filter((t) => t.status === group.status);
          return (
            <Card key={group.status}>
              <CardHeader>
                <CardTitle>{group.label}</CardTitle>
                <CardDescription>{groupTasks.length} task(s)</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {groupTasks.length === 0 && (
                  <span className="font-mono text-sm text-muted-foreground">none</span>
                )}
                {groupTasks.map((task) => (
                  <div
                    key={task.id}
                    className="flex items-center justify-between gap-2 rounded-md border p-2 text-sm"
                  >
                    <div className="min-w-0">
                      <div className="truncate font-mono">{task.name}</div>
                      <div className="truncate text-xs text-muted-foreground">{task.id}</div>
                      {task.error && (
                        <div className="truncate text-xs text-destructive">{task.error}</div>
                      )}
                    </div>
                    {(task.status === "queued" || task.status === "running") && (
                      <Button variant="outline" size="sm" onClick={() => cancelTask(task.id)}>
                        Cancel
                      </Button>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </main>
  );
}
