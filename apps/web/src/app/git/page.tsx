import { GitPanel } from "@/components/git-panel";

export default function GitPage() {
  return (
    <main className="container flex min-h-screen flex-col gap-6 py-16">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Git Workspace</h1>
        <p className="text-muted-foreground">
          Repository status, branch, staged/modified files, and recent commit history for the
          workspace root — read-only, sandboxed the same way the filesystem tool is.
        </p>
      </div>

      <GitPanel />
    </main>
  );
}
