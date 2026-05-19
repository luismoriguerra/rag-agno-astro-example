#!/usr/bin/env bash
# Wire cross-service URL variables (CORS + frontend API URL) from public domains.
set -euo pipefail

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
load_project_env

require_cmd railway
require_cmd jq

backend_host="$(railway_domain_base "$BACKEND_SERVICE")"
frontend_host="$(railway_domain_base "$FRONTEND_SERVICE")"

if [[ -z "$backend_host" || -z "$frontend_host" ]]; then
  echo "Generate public domains first: railway domain --service <name>" >&2
  exit 1
fi

backend_base="https://${backend_host}"
frontend_base="https://${frontend_host}"

railway variable set "${BACKEND_CORS_VAR}=${frontend_base}" --service "$BACKEND_SERVICE" >/dev/null
railway variable set "${FRONTEND_API_VAR}=${backend_base}" --service "$FRONTEND_SERVICE" >/dev/null

echo "BACKEND_URL=${backend_base}${SMOKE_BACKEND_PATH}"
echo "FRONTEND_URL=${frontend_base}${SMOKE_FRONTEND_PATH}"
echo "Redeploy after PUBLIC_* changes: make railway-deploy" >&2
