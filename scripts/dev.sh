#!/usr/bin/env bash
# Run the API and web app concurrently for local development.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

cleanup() {
  jobs -p | xargs -r kill
}
trap cleanup EXIT

(cd apps/api && uvicorn orbit_api.main:app --reload --port 8000) &
(npm run dev --workspace=@orbit/web) &

wait
