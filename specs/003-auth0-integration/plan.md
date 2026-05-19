# Implementation Plan: Auth0 Integration

**Branch**: `003-auth0-integration` | **Date**: 2026-05-18 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/003-auth0-integration/spec.md`

## Summary

Replace mock identity with end-to-end Auth0 authentication: Terraform-provisioned tenant resources
(SPA, API, Google connection, email-allowlist Action), Agno `JWTMiddleware` on FastAPI with dynamic
JWKS and `access:api` RBAC, and hybrid Astro auth (server middleware + Auth0 SPA SDK with Bearer
tokens on all chat API calls). Remove mock headers/env vars. Update smoke tests for auth-gated frontend.

## Technical Context

**Language/Version**: Python 3.12 (backend); Node.js 22 + TypeScript 5.x (frontend)  
**Primary Dependencies**: FastAPI, Agno (`JWTMiddleware`), Auth0 Terraform provider (`auth0/auth0`),
`@auth0/auth0-spa-js`, `@astrojs/node`, `@astrojs/react`  
**Storage**: PostgreSQL unchanged; Auth0 tenant for identity; no mock→Auth0 data migration  
**Testing**: pytest (backend JWT + identity); vitest (frontend auth helpers); manual Google login flow;
updated `smoke_test.py`  
**Target Platform**: Local dev + Railway (frontend SSR Node, backend FastAPI, Postgres)  
**Project Type**: Full-stack auth integration on existing RAG chat monorepo  
**Performance Goals**: SC-001–SC-015 (sign-in redirect <2s; history restore <2s; silent refresh on expiry)  
**Constraints**: Google-only login; single tenant; allowlist `luismoridev@gmail.com` via Terraform Action;
no mock auth; federated logout; frontend must migrate static → server output for middleware  
**Scale/Scope**: Single-user allowlist; ~15 backend files, ~10 frontend files, new `infra/auth0-terraform/`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Grounded RAG and Agent Behavior**: PASS (N/A for grounding). Agent/search unchanged; auth gates agent
  invocation; LangWatch traces continue using `auth_subject` from JWT `sub`.
- **Auth0-Centered Security Boundaries**: PASS. Real Auth0 JWT at FastAPI boundary; `access:api` scope
  RBAC; owner-filtered chat data; allowlist at Auth0 Action; secrets in env/terraform.tfvars only.
- **Typed API and UI Contracts**: PASS WITH UPDATES. OpenAPI security scheme changes MockIdentity →
  Bearer JWT; frontend handles 401/403 and re-auth states; contracts in `contracts/auth-api-security.md`.
- **PostgreSQL and pgvector Integrity**: PASS (N/A migrations). Lazy `UserIdentity` provisioning;
  mock rows orphaned; owner filters unchanged.
- **Railway-Ready Delivery and Observability**: PASS. Auth env vars documented; smoke test accepts
  frontend redirect; structured auth failure logs; Terraform + quickstart for provisioning.

**Post-Design Recheck**: PASS. Research resolves Astro SSR migration, JWKS, scope claim, and Terraform
Action pattern. No justified violations.

## Project Structure

### Documentation (this feature)

```text
specs/003-auth0-integration/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── auth-api-security.md
│   └── terraform-env-mapping.md
└── tasks.md             # Phase 2 — /speckit.tasks
```

### Source Code (repository root)

```text
infra/auth0-terraform/              # NEW — Terraform (reference: jobs-analyzer/auth0)
├── main.tf, versions.tf, variables.tf, outputs.tf
├── api.tf, client.tf, scopes.tf
├── connection_google.tf            # Google OAuth connection
├── action_allowlist.tf             # post-login email allowlist
├── trigger_actions.tf              # bind Action to login flow
├── Makefile, terraform.tfvars.example, README.md

apps/backend/
├── pyproject.toml                    # agno JWT deps if not already present
├── .env.example                      # AUTH0_* ; remove MOCK_AUTH_SUBJECT
└── src/agentos_chat/
    ├── main.py                       # JWTMiddleware + excluded /health
    ├── settings.py                   # auth0_domain, issuer, audience
    ├── auth/
    │   ├── dependencies.py           # JWT sub → CurrentIdentity ; remove mock
    │   └── jwt_middleware.py         # JWKS fetch, scope_mappings helper
    └── tests/
        ├── unit/test_auth_jwt.py
        └── integration/test_auth_api.py

apps/frontend/
├── package.json                      # @auth0/auth0-spa-js, @astrojs/node
├── astro.config.ts                   # output: server, node adapter
├── Dockerfile                        # Node SSR entry (not serve static)
├── .env.example                      # PUBLIC_AUTH0_* ; remove PUBLIC_MOCK_IDENTITY
└── src/
    ├── middleware.ts                 # Auth gate on protected routes
    ├── pages/api/auth/
    │   ├── login.ts
    │   ├── callback.ts
    │   └── logout.ts
    ├── lib/auth0.ts                  # SPA client + token helpers
    └── services/chatApi.ts           # Bearer token + silent refresh retry

infra/railway/
├── smoke_test.py                     # Accept 302/307 frontend
└── project.env.example               # Auth0 env sync keys
```

**Structure Decision**: Extend existing `apps/backend` + `apps/frontend` monorepo; add sibling
`infra/auth0-terraform` per user requirement. Frontend requires SSR migration (currently static).

## Implementation Phases (for /speckit.tasks)

### Phase A — Terraform foundation (P2, blocking for real login)

1. Scaffold `infra/auth0-terraform/` from jobs-analyzer reference with project naming.
2. Add Google connection, allowlist Action, trigger binding, `allowed_emails` variable.
3. Document `terraform.tfvars.example` with localhost + placeholder production URLs.
4. Add README with output → env mapping.

### Phase B — Backend JWT (P1)

5. Add Auth0 settings to `settings.py`; remove `mock_auth_subject`.
6. Implement JWKS client + Agno `JWTMiddleware` in `main.py` with `access:api` scope mappings for all `/api/chat/*` routes.
7. Rewrite `get_current_identity` to use JWT `sub` + `get_or_create_identity`.
8. Add auth failure structured logging (no token content).
9. Unit/integration tests for 401/403/unauthorized.

### Phase C — Frontend auth (P1)

10. Add `@astrojs/node`; change `output: "server"`; update Dockerfile for SSR.
11. Implement `/api/auth/login|callback|logout` and `middleware.ts` public route allowlist.
12. Integrate `@auth0/auth0-spa-js`; update `chatApi.ts` with Bearer + silent refresh retry.
13. Add sign-out control to chat UI; handle auth error states (FR-016).

### Phase D — Deployment & cleanup (P2)

14. Update `.env.example` files, Railway env sync, quickstart cross-links.
15. Update `smoke_test.py` for redirect acceptance.
16. Remove all mock identity references (frontend, backend, docs, OpenAPI).
17. Manual verification per quickstart with allowlisted Gmail.

## Complexity Tracking

> No constitution violations requiring justification.

| Item | Notes |
|------|-------|
| Astro static → SSR | Required for server middleware (spec FR-029); Dockerfile must change |
| Agno JWTMiddleware on custom routes | Custom `scope_mappings` for `/api/chat/*` endpoints |
| Terraform Action code | Inline JS in `auth0_action` resource with email list variable |

## Phase 0 & Phase 1 Artifacts

| Artifact | Status |
|----------|--------|
| [research.md](./research.md) | Complete |
| [data-model.md](./data-model.md) | Complete |
| [quickstart.md](./quickstart.md) | Complete |
| [contracts/auth-api-security.md](./contracts/auth-api-security.md) | Complete |
| [contracts/terraform-env-mapping.md](./contracts/terraform-env-mapping.md) | Complete |

**Next command**: `/speckit.implement` to execute dependency-ordered tasks in [tasks.md](./tasks.md).
