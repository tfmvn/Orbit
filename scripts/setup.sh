#!/usr/bin/env bash
# Install all backend and frontend dependencies for local development.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Installing runtime engine (Python) dependencies"
cd "$repo_root/packages/runtime"
python3 -m pip install -e ".[dev]"

echo "==> Installing tool framework (Python) dependencies"
cd "$repo_root/packages/tools"
python3 -m pip install -e ".[dev]"

echo "==> Installing API (Python) dependencies"
cd "$repo_root/apps/api"
python3 -m pip install -e ".[dev]"

echo "==> Installing Node dependencies (web + shared)"
cd "$repo_root"
npm install --workspaces --if-present

echo "==> Done. Copy .env.example -> .env in apps/api and apps/web if you haven't already."
