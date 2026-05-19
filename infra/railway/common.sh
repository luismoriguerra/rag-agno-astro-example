#!/usr/bin/env bash
# Shared helpers for Railway scripts.

require_cmd() {
  command -v "$1" >/dev/null || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

# Resolve the repository root (two levels up from this file) and load
# infra/railway/project.env. Required variables raise an error.
load_project_env() {
  if [[ -z "${ROOT_DIR:-}" ]]; then
    ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    export ROOT_DIR
  fi

  local config="$ROOT_DIR/infra/railway/project.env"
  if [[ ! -f "$config" ]]; then
    echo "Missing $config. Copy project.env.example and edit." >&2
    exit 1
  fi

  # shellcheck disable=SC1090
  set -a
  source "$config"
  set +a

  require_project_env \
    RAILWAY_PROJECT_NAME BACKEND_SERVICE FRONTEND_SERVICE POSTGRES_SERVICE \
    BACKEND_DIR FRONTEND_DIR DATABASE_URL_REF \
    BACKEND_CORS_VAR FRONTEND_API_VAR \
    SMOKE_BACKEND_PATH SMOKE_FRONTEND_PATH
}

require_project_env() {
  local missing=()
  local name
  for name in "$@"; do
    if [[ -z "${!name:-}" ]]; then
      missing+=("$name")
    fi
  done
  if ((${#missing[@]} > 0)); then
    echo "project.env is missing: ${missing[*]}" >&2
    exit 1
  fi
}

railway_domain_base() {
  local service="$1"
  railway domain --service "$service" --json 2>/dev/null | jq -r '
    if .domains then (.domains[0] | sub("^https://"; ""))
    elif type == "array" then .[0].domain
    elif .domain then .domain
    else empty end
  '
}

railway_service_id() {
  local name="$1"
  railway status --json | jq -r --arg n "$name" '
    .services.edges[] | select(.node.name == $n) | .node.id
  '
}

railway_postgres_service_names() {
  railway status --json | jq -r '
    .environments.edges[0].node.serviceInstances.edges[]
    | select(.node.serviceName | test("postgres"; "i"))
    | .node.serviceName
  '
}
