#!/usr/bin/env bash
# Auto-format Python and TypeScript code.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

(cd apps/api && ruff check --fix src tests && black src tests)
npm run format --workspace=@orbit/web
