#!/usr/bin/env bash
# Provision/link Railway services and sync env vars from local .env files.
set -euo pipefail

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
load_project_env

require_cmd railway
require_cmd jq

if ! railway whoami >/dev/null 2>&1; then
  echo "Run: railway login" >&2
  exit 1
fi

cd "$ROOT_DIR"

if ! railway status >/dev/null 2>&1; then
  echo "Linking Railway project: $RAILWAY_PROJECT_NAME"
  railway init --name "$RAILWAY_PROJECT_NAME"
fi

if ! railway status --json 2>/dev/null | jq -e --arg svc "$POSTGRES_SERVICE" '
  .environments.edges[0].node.serviceInstances.edges[]
  | select(.node.serviceName == $svc or (.node.serviceName | test("postgres"; "i")))
' >/dev/null; then
  echo "Adding PostgreSQL..."
  railway add --database postgres 2>/dev/null || true
fi

set_service_var() {
  railway variable set "${2}=${3}" --service "$1" >/dev/null
}

# Push selected keys from a local .env file into a Railway service.
sync_env_file() {
  local env_file="$1"
  local service="$2"
  local keys="$3"

  [[ -f "$env_file" ]] || return 0
  [[ -n "$keys" ]] || return 0

  echo "Syncing $(basename "$(dirname "$env_file")")/.env into $service..."
  local line key value
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    key="${line%%=*}"
    value="${line#*=}"
    [[ -z "$value" ]] && continue
    if [[ " $keys " == *" $key "* ]]; then
      set_service_var "$service" "$key" "$value"
    fi
  done < "$env_file"
}

sync_env_file "$ROOT_DIR/$BACKEND_DIR/.env" "$BACKEND_SERVICE" "$BACKEND_ENV_SYNC_KEYS"
sync_env_file "$ROOT_DIR/$FRONTEND_DIR/.env" "$FRONTEND_SERVICE" "$FRONTEND_ENV_SYNC_KEYS"

if [[ -n "${BACKEND_DEFAULT_VARS:-}" ]]; then
  for pair in $BACKEND_DEFAULT_VARS; do
    set_service_var "$BACKEND_SERVICE" "${pair%%=*}" "${pair#*=}"
  done
fi

set_service_var "$BACKEND_SERVICE" "DATABASE_URL" "$DATABASE_URL_REF"

if [[ -n "$(railway_domain_base "$BACKEND_SERVICE")" && -n "$(railway_domain_base "$FRONTEND_SERVICE")" ]]; then
  echo "Syncing production URLs from Railway domains..."
  bash "$ROOT_DIR/infra/railway/configure_urls.sh" >/dev/null || true
fi

echo ""
echo "Project ready. Next:"
echo "  make railway-deploy"
echo "  make railway-cleanup   # recommended once: clear dashboard drift + smoke"
echo "  make railway-smoke"
