#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

export VIEW_TOKEN="${VIEW_TOKEN:-dev}"
export ADMIN_TOKEN="${ADMIN_TOKEN:-dev}"
export DB_PATH="${DB_PATH:-career.db}"

if [ ! -d frontend/node_modules ]; then
  echo "frontend/node_modules missing — run: npm install --prefix frontend" >&2
  exit 1
fi

cleanup() {
  jobs -p | xargs -r kill 2>/dev/null
}
trap cleanup EXIT INT TERM

echo "Backend:  http://127.0.0.1:8000/api/dashboard?v=$VIEW_TOKEN"
echo "Frontend: http://127.0.0.1:5173"

python3 -m uvicorn api.main:app --reload --port 8000 &
(cd frontend && exec ./node_modules/.bin/vite) &

wait
