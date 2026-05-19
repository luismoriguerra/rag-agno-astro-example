#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ -n "${SKIP_MIGRATIONS:-}" ]]; then
  echo "Skipping migrations (SKIP_MIGRATIONS is set)"
else
  python -m alembic upgrade head
fi

exec python -m uvicorn agentos_chat.main:app --host 0.0.0.0 --port "${PORT:?PORT not set}"
