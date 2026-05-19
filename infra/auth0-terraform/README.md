# Auth0 Terraform — web0personal-vector

Provisions Auth0 **API**, **SPA client**, and **email-allowlist Action** for this application. **Google social login is excluded by default** — use your existing tenant connection (see below).

See also: [specs/003-auth0-integration/contracts/terraform-env-mapping.md](../../specs/003-auth0-integration/contracts/terraform-env-mapping.md)

## Prerequisites

- Terraform >= 1.6
- Auth0 tenant with a **machine-to-machine** client authorized for the Auth0 Terraform provider
- **Google social connection** already enabled in the tenant (default), *or* set `manage_google_connection = true` with Google OAuth credentials to create it via Terraform

## Setup

1. Copy `terraform.tfvars.example` to `terraform.tfvars` (gitignored) and fill values.
2. Or export `TF_VAR_*` variables for secrets.

## Commands

```bash
make init
make plan
make apply
```

Re-run `terraform apply` against an unchanged configuration to confirm idempotency (SC-007).

## Outputs → environment

| Output / variable | Backend `.env`           | Frontend `.env`              |
|-------------------|--------------------------|------------------------------|
| `auth0_domain`    | `AUTH0_DOMAIN`           | `PUBLIC_AUTH0_DOMAIN`        |
| `issuer`          | `AUTH0_ISSUER`           | (same domain as issuer host) |
| `api_audience`    | `AUTH0_API_AUDIENCE`     | `PUBLIC_AUTH0_AUDIENCE`      |
| `spa_client_id`   | —                        | `PUBLIC_AUTH0_CLIENT_ID`     |

Generate `AUTH0_SECRET` locally (32+ random chars) for frontend session cookies — not a Terraform output.

Callback URL convention: `{frontend_origin}/api/auth/callback`

## Existing Google connection (default)

When `manage_google_connection = false` (default), Terraform does **not** create or modify Google.

After `terraform apply`, enable the new SPA on your existing Google connection:

1. Auth0 Dashboard → **Authentication** → **Social** → **Google**
2. **Applications** tab → enable **web0personal-vector Web** (or your `spa_name`)
3. Ensure Google is the only connection enabled for that SPA (Universal Login)

To let Terraform create Google instead (greenfield tenants only):

```hcl
manage_google_connection = true
google_client_id         = "..."
google_client_secret     = "..."
```

## Railway env sync

After apply, sync keys documented in `infra/railway/project.env.example`.
