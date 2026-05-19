#!/usr/bin/env bash
# Railway project cleanup: wire DB variable, sync URLs, clear dashboard drift,
# warn on duplicate Postgres services, then smoke-test.
set -euo pipefail

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
load_project_env

require_cmd railway
require_cmd jq

cd "$ROOT_DIR"

if ! railway status >/dev/null 2>&1; then
  echo "Link project first: railway link" >&2
  exit 1
fi

echo "==> Link backend DATABASE_URL to Postgres"
railway variable set "DATABASE_URL=$DATABASE_URL_REF" --service "$BACKEND_SERVICE" >/dev/null

echo "==> Sync CORS and frontend API URL"
eval "$(bash "$ROOT_DIR/infra/railway/configure_urls.sh" \
  | sed -nE 's/^(BACKEND_URL|FRONTEND_URL)=/export \1=/p')"

echo "==> Clear stale dashboard start/build overrides (Dockerfile is source of truth)"
backend_id="$(railway_service_id "$BACKEND_SERVICE")"
frontend_id="$(railway_service_id "$FRONTEND_SERVICE")"

if [[ -z "$backend_id" || -z "$frontend_id" ]]; then
  echo "Could not resolve service IDs (backend='$backend_id' frontend='$frontend_id')." >&2
  echo "Check BACKEND_SERVICE/FRONTEND_SERVICE in infra/railway/project.env." >&2
  exit 1
fi

railway environment edit --json <<JSON
{
  "services": {
    "${backend_id}": {
      "deploy": { "startCommand": null },
      "build":  { "buildCommand": null }
    },
    "${frontend_id}": {
      "deploy": { "startCommand": null },
      "build":  { "buildCommand": null }
    }
  }
}
JSON

pg_services=()
while IFS= read -r name; do
  [[ -n "$name" ]] && pg_services+=("$name")
done < <(railway_postgres_service_names)

if ((${#pg_services[@]} > 1)); then
  echo "WARNING: Multiple Postgres services: ${pg_services[*]}"
  echo "Keep ${POSTGRES_SERVICE}; delete extras in Railway UI (Settings -> Danger)."
elif ((${#pg_services[@]} == 0)); then
  echo "WARNING: No Postgres service found. Run: make railway-up"
else
  echo "Postgres: ${pg_services[0]} -- OK"
fi

echo ""
echo "==> Services"
railway status --json \
  | jq -r '.environments.edges[0].node.serviceInstances.edges[].node.serviceName' \
  | sort -u

echo ""
echo "==> Smoke"
if [[ -n "${BACKEND_URL:-}" && -n "${FRONTEND_URL:-}" ]]; then
  BACKEND_URL="$BACKEND_URL" FRONTEND_URL="$FRONTEND_URL" \
    python "$ROOT_DIR/infra/railway/smoke_test.py"
else
  echo "Skipped (domains missing)"
fi
