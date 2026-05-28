#!/usr/bin/env bash
# Run all linters/formatters in check mode. Used by `make lint` and CI.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

echo "==> ruff"
(cd apps/api && ruff check src tests)

echo "==> black --check"
(cd apps/api && black --check src tests)

echo "==> eslint"
npm run lint --workspace=@orbit/web

echo "==> prettier --check"
npm run format:check --workspace=@orbit/web
