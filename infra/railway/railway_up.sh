#!/usr/bin/env bash
set -euo pipefail

# Adapted from Agno PAL Railway setup: preflight, services, database, variables.
# Requires Railway CLI authenticated.

echo "Creating Railway services with minimum resource settings..."
railway service create agentos-chat-backend || true
railway service create agentos-chat-frontend || true

echo "Link Postgres (pgvector) plugin if not present..."
railway add --database postgres || true

echo "Document any minimum CPU/memory exceptions in infra/railway/README.md"
echo "Done. Configure variables and run: make railway-deploy"
