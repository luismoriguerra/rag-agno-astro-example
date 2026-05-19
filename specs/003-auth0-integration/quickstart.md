# Quickstart: Auth0 Integration

## Prerequisites

- Python 3.12, Node.js 22, Make, Docker (for local Postgres)
- Auth0 tenant with admin access
- Terraform >= 1.6 and Auth0 M2M credentials for Terraform provider
- Google Cloud OAuth client (for Google social login) OR existing Auth0 Google connection
- Allowlisted Google account: `luismoridev@gmail.com`

## 1. Provision Auth0 (Terraform)

```bash
cd infra/auth0-terraform
cp terraform.tfvars.example terraform.tfvars
# Edit: auth0_domain, M2M credentials, api_identifier, callback/logout/web_origins, allowed_emails
make init
make plan
make apply
```

Note outputs: `issuer`, `api_audience`, `spa_client_id`, `auth0_domain`.

Register production URLs when Railway domains exist (re-run `terraform apply` after updating `callback_urls`, `logout_urls`, `web_origins`).

## 2. Backend environment

`apps/backend/.env`:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/agentos_chat
AUTH0_DOMAIN=your-tenant.us.auth0.com
AUTH0_ISSUER=https://your-tenant.us.auth0.com/
AUTH0_API_AUDIENCE=https://your-api-identifier
CORS_ORIGINS=http://localhost:4321
OPENROUTER_API_KEY=...
# Remove MOCK_AUTH_SUBJECT — no longer used
```

## 3. Frontend environment

`apps/frontend/.env`:

```bash
PUBLIC_AUTH0_DOMAIN=your-tenant.us.auth0.com
PUBLIC_AUTH0_CLIENT_ID=<spa_client_id from terraform>
PUBLIC_AUTH0_AUDIENCE=https://your-api-identifier
PUBLIC_AGENTOS_API_BASE_URL=http://localhost:8000
AUTH0_SECRET=<random 32+ char string for session cookies>
# Remove PUBLIC_MOCK_IDENTITY
```

## 4. Local run

```bash
make install
make db-up
make migrate
make dev
```

## 5. Manual verification (P1)

1. Open `http://localhost:4321/chat` in a private window → redirect to Auth0 Google login.
2. Sign in with `luismoridev@gmail.com` → land on `/chat`.
3. Submit a chat message → succeeds with Bearer token (check Network tab: no `X-Mock-Identity`).
4. Reload page → history restores for same user.
5. Sign out → federated logout; `/chat` requires login again.
6. Attempt sign-in with non-allowlisted Google account → denied at Auth0.

## 6. Backend security checks

```bash
# Should 401
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/chat/sessions

# Should 200
curl -s http://localhost:8000/health
```

With a valid access token (from browser devtools):

```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/chat/sessions
```

## 7. Smoke test (deployment)

```bash
make smoke-local
# Backend /health → 2xx
# Frontend / → 302/307 redirect acceptable
```

After Railway deploy:

```bash
make railway-smoke
```

## 8. Token inspection (scope claim)

Decode access token at [jwt.io](https://jwt.io) (local only; do not paste production tokens on public tools):

- `aud` matches `AUTH0_API_AUDIENCE`
- `scope` contains `access:api`
- `sub` is stable Auth0 subject

If scope missing, verify SPA requests token with `audience` + Auth0 client grant in Terraform.

## 9. Troubleshooting

| Symptom | Check |
|---------|-------|
| Redirect loop | Callback URL in Terraform matches `/api/auth/callback` |
| 401 on all API calls | Audience mismatch; token not API access token |
| 403 on API calls | Missing `access:api` scope; check `scopes_claim` in middleware |
| Login denied | Email not in Terraform allowlist Action |
| Frontend smoke fails | Expect 302/307 not 200 for `/` when unauthenticated |

## 10. Railway env sync

Set `BACKEND_ENV_SYNC_KEYS` and `FRONTEND_ENV_SYNC_KEYS` in `infra/railway/project.env` per `contracts/terraform-env-mapping.md`, then redeploy.
