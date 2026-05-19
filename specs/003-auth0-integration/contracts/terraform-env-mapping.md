# Contract: Terraform Outputs → Application Environment

## Purpose

Maps `infra/auth0-terraform` outputs and variables to backend/frontend/Railway environment variables after `terraform apply`.

## Terraform Outputs (to implement)

| Output | Example | Consumer |
|--------|---------|----------|
| `issuer` | `https://dev-xxx.us.auth0.com/` | Backend `AUTH0_ISSUER` |
| `api_audience` | `https://web0personal-vector-api.local` | Backend + frontend audience |
| `spa_client_id` | `abc123...` | Frontend `PUBLIC_AUTH0_CLIENT_ID` |
| `auth0_domain` | `dev-xxx.us.auth0.com` | Backend `AUTH0_DOMAIN`, frontend `PUBLIC_AUTH0_DOMAIN` |

## Backend (`apps/backend/.env`)

| Variable | Source | Required |
|----------|--------|----------|
| `AUTH0_DOMAIN` | Terraform `auth0_domain` variable / output | Yes |
| `AUTH0_ISSUER` | Terraform output `issuer` | Yes |
| `AUTH0_API_AUDIENCE` | Terraform output `api_audience` | Yes |
| `DATABASE_URL` | Postgres (unchanged) | Yes |
| `CORS_ORIGINS` | Frontend origin(s) | Yes |

**Removed**: `MOCK_AUTH_SUBJECT`

## Frontend (`apps/frontend/.env`)

| Variable | Source | Required |
|----------|--------|----------|
| `PUBLIC_AUTH0_DOMAIN` | Terraform `auth0_domain` | Yes |
| `PUBLIC_AUTH0_CLIENT_ID` | Terraform output `spa_client_id` | Yes |
| `PUBLIC_AUTH0_AUDIENCE` | Terraform output `api_audience` | Yes |
| `PUBLIC_AGENTOS_API_BASE_URL` | Backend public URL | Yes |
| `AUTH0_SECRET` | Random 32+ char secret (session cookie encryption) | Yes (server-only, not `PUBLIC_`) |

**Removed**: `PUBLIC_MOCK_IDENTITY`

## Terraform secrets (`infra/auth0-terraform/terraform.tfvars` — gitignored)

| Variable | Purpose |
|----------|---------|
| `auth0_domain` | Tenant |
| `auth0_terraform_client_id` | M2M client for provider |
| `auth0_terraform_client_secret` | M2M secret |
| `api_identifier` | API audience string |
| `callback_urls` | `http://localhost:4321/api/auth/callback`, Railway frontend callback |
| `logout_urls` | `http://localhost:4321`, Railway frontend URL |
| `web_origins` | `http://localhost:4321`, Railway frontend URL |
| `allowed_emails` | `["luismoridev@gmail.com"]` |
| `manage_google_connection` | Default `false` — use existing Google connection; enable SPA in Auth0 dashboard after apply |
| `google_client_id` / `google_client_secret` | Only when `manage_google_connection = true` (greenfield tenants) |

## Railway (`infra/railway/project.env`)

Suggested sync keys after implementation:

```bash
BACKEND_ENV_SYNC_KEYS="AUTH0_DOMAIN AUTH0_ISSUER AUTH0_API_AUDIENCE CORS_ORIGINS OPENROUTER_API_KEY"
FRONTEND_ENV_SYNC_KEYS="PUBLIC_AUTH0_DOMAIN PUBLIC_AUTH0_CLIENT_ID PUBLIC_AUTH0_AUDIENCE PUBLIC_AGENTOS_API_BASE_URL AUTH0_SECRET"
```

## Callback URL convention

Local: `http://localhost:4321/api/auth/callback`  
Production: `https://{railway-frontend-domain}/api/auth/callback`

Must match Terraform `callback_urls` and Google OAuth authorized redirect (via Auth0).
