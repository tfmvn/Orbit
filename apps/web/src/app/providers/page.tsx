"use client";

import { useCallback, useEffect, useState } from "react";
import type {
  GenerateResponse,
  ModelInfoResponse,
  ProviderHealthResponse,
  ProviderSummaryResponse,
} from "@orbit/shared";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function ProvidersPage() {
  const [providers, setProviders] = useState<ProviderSummaryResponse[]>([]);
  const [health, setHealth] = useState<ProviderHealthResponse | null>(null);
  const [models, setModels] = useState<ModelInfoResponse[]>([]);
  const [prompt, setPrompt] = useState("Say hello in one sentence.");
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const [providersRes, healthRes, modelsRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/v1/providers`, { cache: "no-store" }),
        fetch(`${API_BASE_URL}/api/v1/providers/health`, { cache: "no-store" }),
        fetch(`${API_BASE_URL}/api/v1/providers/models`, { cache: "no-store" }),
      ]);
      if (providersRes.ok) setProviders((await providersRes.json()) as ProviderSummaryResponse[]);
      if (healthRes.ok) setHealth((await healthRes.json()) as ProviderHealthResponse);
      if (modelsRes.ok) setModels((await modelsRes.json()) as ModelInfoResponse[]);
      setError(null);
    } catch {
      setError("Couldn't reach the API — is it running?");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const activeProvider = providers.find((p) => p.active)?.name ?? null;

  const runGenerate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/providers/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? `HTTP ${res.status}`);
      }
      setResult((await res.json()) as GenerateResponse);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container flex min-h-screen flex-col gap-6 py-16">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Model Provider</h1>
        <p className="text-muted-foreground">
          Validates the Model Provider integration — active provider, health, installed models,
          and a single test prompt. Not a chat interface.
        </p>
      </div>

      {error && <p className="font-mono text-sm text-destructive">{error}</p>}

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Providers</CardTitle>
            <CardDescription>active: {activeProvider ?? "none"}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-1 font-mono text-sm">
            {providers.map((p) => (
              <div key={p.name}>
                {p.name} {p.active ? "(active)" : ""}
              </div>
            ))}
            {providers.length === 0 && (
              <span className="text-muted-foreground">No providers registered.</span>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Health</CardTitle>
            <CardDescription>{API_BASE_URL}/api/v1/providers/health</CardDescription>
          </CardHeader>
          <CardContent className="font-mono text-sm">
            {health ? (
              <span className={health.healthy ? "text-primary" : "text-destructive"}>
                {health.healthy ? "healthy" : `unhealthy — ${health.detail ?? "unknown"}`}
              </span>
            ) : (
              <span className="text-muted-foreground">Loading…</span>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Installed models</CardTitle>
          <CardDescription>{API_BASE_URL}/api/v1/providers/models</CardDescription>
        </CardHeader>
        <CardContent className="space-y-1 font-mono text-xs">
          {models.map((m) => (
            <div key={m.name}>
              {m.name} {m.size ? `(${m.size}B)` : ""}
            </div>
          ))}
          {models.length === 0 && <span className="text-muted-foreground">No models available.</span>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Test prompt</CardTitle>
          <CardDescription>
            Runs against the active provider — for validating the integration, not for chat.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <textarea
            className="w-full rounded-md border bg-transparent px-3 py-1.5 text-sm"
            rows={3}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
          <Button size="sm" disabled={loading} onClick={runGenerate}>
            {loading ? "Generating…" : "Generate"}
          </Button>
          {result && (
            <pre className="max-h-64 overflow-auto whitespace-pre-wrap break-words rounded-md border p-2 font-mono text-xs">
              {result.text}
            </pre>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
