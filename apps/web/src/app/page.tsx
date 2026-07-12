import Link from "next/link";
import type { HealthResponse, VersionResponse } from "@orbit/shared";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function getHealth(): Promise<HealthResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/health`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as HealthResponse;
  } catch {
    return null;
  }
}

async function getVersion(): Promise<VersionResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/version`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as VersionResponse;
  } catch {
    return null;
  }
}

export default async function DashboardPage() {
  const [health, version] = await Promise.all([getHealth(), getVersion()]);

  return (
    <main className="container flex min-h-screen flex-col gap-6 py-16">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Orbit</h1>
        <p className="text-muted-foreground">
          A local-first autonomous AI runtime. This dashboard is a placeholder — agent, planner,
          memory, and tool UI will be built on top of this foundation.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>API health</CardTitle>
            <CardDescription>{API_BASE_URL}/api/v1/health</CardDescription>
          </CardHeader>
          <CardContent>
            {health ? (
              <span className="font-mono text-sm text-primary">{health.status}</span>
            ) : (
              <span className="font-mono text-sm text-muted-foreground">
                unreachable — is the API running?
              </span>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>API version</CardTitle>
            <CardDescription>{API_BASE_URL}/api/v1/version</CardDescription>
          </CardHeader>
          <CardContent>
            {version ? (
              <dl className="grid grid-cols-2 gap-x-4 gap-y-1 font-mono text-sm">
                <dt className="text-muted-foreground">name</dt>
                <dd>{version.name}</dd>
                <dt className="text-muted-foreground">version</dt>
                <dd>{version.version}</dd>
                <dt className="text-muted-foreground">environment</dt>
                <dd>{version.environment}</dd>
              </dl>
            ) : (
              <span className="font-mono text-sm text-muted-foreground">
                unreachable — is the API running?
              </span>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="flex gap-4">
        <Link href="/tasks" className="text-sm font-medium text-primary underline underline-offset-4">
          View tasks →
        </Link>
        <Link href="/tools" className="text-sm font-medium text-primary underline underline-offset-4">
          View tools →
        </Link>
        <Link
          href="/context"
          className="text-sm font-medium text-primary underline underline-offset-4"
        >
          View context →
        </Link>
        <Link href="/git" className="text-sm font-medium text-primary underline underline-offset-4">
          View git →
        </Link>
      </div>
    </main>
  );
}
