# Research: Auth0 Integration

## 1. Terraform layout (jobs-analyzer reference)

**Decision**: Add `infra/auth0-terraform/` modeled on `railway-projects/jobs-analyzer/auth0` with project-specific naming and URLs; extend with Google connection, allowlist Action, and production callback URLs.

**Rationale**: Spec requires reproducible provisioning (FR-011) and M2M credentials via `terraform.tfvars` (user input). Reference module already validates SPA + API + scope + client grant pattern.

**Alternatives considered**:
- Manual Auth0 dashboard only — rejected; fails FR-011/FR-026.
- Separate dev/prod tenants — rejected in clarifications (single tenant).

**Files** (from reference):
- `main.tf`, `versions.tf`, `variables.tf`, `outputs.tf`, `api.tf`, `client.tf`, `scopes.tf`, `Makefile`, `terraform.tfvars.example`
- **New**: `connection_google.tf`, `action_allowlist.tf`, `trigger_actions.tf`

---

## 2. Auth0 Action email allowlist in Terraform

**Decision**: Use `auth0_action` (post-login trigger, `deploy = true`) + `auth0_trigger_actions` to bind the allowlist Action to the login flow. Allowlist emails passed via Terraform variable `allowed_emails = ["luismoridev@gmail.com"]` embedded in Action JavaScript.

**Rationale**: Clarification requires full Terraform management (FR-026). Provider supports `auth0_action` and `auth0_trigger_actions` ([Terraform Registry](https://registry.terraform.io/providers/auth0/auth0/latest/docs/resources/trigger_actions)).

**Alternatives considered**:
- Manual dashboard Action — rejected.
- `auth0_trigger_action` per action — rejected; use `auth0_trigger_actions` when managing one flow to avoid binding conflicts.

**Action behavior**: On `post-login`, read `event.user.email`; if not in allowlist, `api.access.deny('Access denied')`.

---

## 3. Google-only Universal Login

**Decision**: Enable Google social connection via `auth0_connection` (strategy `google-oauth2`) and enable it on the SPA client; disable Username-Password database connection for this application.

**Rationale**: Clarification B — Google only with allowlisted Gmail.

**Alternatives considered**:
- Database + Google — rejected.
- Google credentials stored in Terraform variables (`google_client_id`, `google_client_secret`) or existing tenant connection referenced by ID.

**Note**: Google OAuth app must be configured in Google Cloud Console with authorized redirect URI `https://{auth0_domain}/login/callback`.

---

## 4. Backend JWT validation (Agno JWTMiddleware)

**Decision**: Add Agno `JWTMiddleware` to the FastAPI app in `main.py` with:
- `algorithm="RS256"`
- Dynamic JWKS from Auth0 issuer (`https://{domain}/.well-known/jwks.json`) — fetch at startup and refresh on `kid` miss, or use PyJWT/PyJWKClient helper if middleware accepts JWKS URL
- `verify_audience=True`, `audience=settings.auth0_api_audience`
- `authorization=True`, `scopes_claim="scope"` (Auth0 API access tokens from client grant use space-delimited `scope` claim)
- Custom `scope_mappings` for all `/api/chat/*` routes requiring `access:api`
- `excluded_route_paths=["/health"]`
- `token_source=TokenSource.HEADER` (default)

**Rationale**: User requirement + spec FR-006/FR-031; Agno docs at [JWT Middleware](https://docs.agno.com/agent-os/middleware/jwt). Custom FastAPI routes (not AgentOS built-ins) need explicit scope mappings.

**Alternatives considered**:
- Custom PyJWT dependency only — rejected; user asked for Agno middleware.
- `authorization=False` — rejected; clarification requires `access:api` enforcement.

**Bridge to existing code**: Replace `get_current_identity` mock header dependency with JWT `sub` extraction from request state populated by middleware (or shared JWT decode). Call existing `get_or_create_identity(db, auth_subject=sub)` for lazy provisioning (FR-007).

---

## 5. Remove mock identity

**Decision**: Delete mock header path (`X-Mock-Identity`, `MOCK_AUTH_SUBJECT`, `PUBLIC_MOCK_IDENTITY`); all environments require Auth0.

**Rationale**: Clarifications — Auth0 required everywhere (FR-010).

**Migration**: Mock-owned chat rows remain in DB but are invisible to Auth0 `sub` queries (clean break).

---

## 6. Frontend hybrid auth (Astro middleware + Auth0 SPA SDK)

**Decision**:
1. Migrate Astro from `output: "static"` to `output: "server"` with `@astrojs/node` (standalone) for Railway.
2. Add `src/middleware.ts` — redirect unauthenticated requests on protected routes to `/api/auth/login`; allow public routes per FR-014/FR-027.
3. Add Auth0 API routes: `/api/auth/login`, `/api/auth/callback`, `/api/auth/logout` (Astro endpoints).
4. Use `@auth0/auth0-spa-js` in client code for silent token refresh and `Authorization: Bearer` on API calls (FR-015, FR-029).
5. Server session cookie (httpOnly) set after callback so middleware can gate SSR without exposing tokens to middleware parsing on every route.

**Rationale**: Current `astro.config.ts` is static-only; Astro middleware does not run on pure static output. Spec requires server middleware gate + client SDK token lifecycle.

**Alternatives considered**:
- Client-only guard (no middleware) — rejected in clarification C.
- `@auth0/nextjs-auth0` — wrong framework.

**Dockerfile change**: Replace `serve dist` with Node adapter server entry (`node ./dist/server/entry.mjs` or documented Astro standalone command).

---

## 7. Auth0 SPA token audience

**Decision**: Frontend requests access tokens with `audience: PUBLIC_AUTH0_AUDIENCE` (API identifier) and `scope: "access:api"` so backend RBAC passes.

**Rationale**: Backend requires `access:api` scope (FR-006); Auth0 SPA must request API access token, not ID token only.

---

## 8. Federated logout

**Decision**: Logout route clears local session cookie and redirects to Auth0 `/v2/logout?client_id=...&returnTo=...` (FR-003).

**Rationale**: Clarification A — federated logout.

---

## 9. Smoke test updates

**Decision**: Update `infra/railway/smoke_test.py` `check()` to accept 2xx OR 302/307 for frontend URL; backend remains 2xx only on `/health`.

**Rationale**: FR-030 / SC-015.

---

## 10. Environment variable mapping

**Decision**: See `contracts/terraform-env-mapping.md`. Backend: `AUTH0_DOMAIN`, `AUTH0_ISSUER`, `AUTH0_API_AUDIENCE`. Frontend: `PUBLIC_AUTH0_DOMAIN`, `PUBLIC_AUTH0_CLIENT_ID`, `PUBLIC_AUTH0_AUDIENCE`, `PUBLIC_AGENTOS_API_BASE_URL`. Terraform M2M vars stay in `terraform.tfvars` only.

**Rationale**: FR-012/FR-018; jobs-analyzer README pattern.

---

## 11. Railway env sync

**Decision**: Extend `infra/railway/project.env.example` with `BACKEND_ENV_SYNC_KEYS` and `FRONTEND_ENV_SYNC_KEYS` for Auth0 variables; document in quickstart.

**Rationale**: Constitution V — deployment repeatability.

---

## 12. Auth0 token permissions vs scope claim

**Decision**: Use Auth0 Resource Server scopes (not RBAC permissions API) so access tokens include `scope: "access:api"`. Configure Agno `scopes_claim="scope"`.

**Rationale**: Terraform reference uses `auth0_resource_server_scope` + client grant; avoids Auth0 RBAC authorization feature flag complexity.

**Verification**: Decode a test access token during quickstart manual step; adjust `scopes_claim` to `permissions` only if tenant uses RBAC permissions instead.
