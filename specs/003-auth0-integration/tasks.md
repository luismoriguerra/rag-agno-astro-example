# Tasks: Auth0 Integration

**Input**: Design documents from `/specs/003-auth0-integration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Backend unit/integration auth tests and smoke-test updates are included because this
feature changes security boundaries, API contracts, and deployment verification.

**Organization**: Tasks grouped by user story (US1 sign-in, US2 secure API access, US3 Terraform provisioning).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2, or US3
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Scaffold Terraform directory, add dependencies, and secure secret handling.

- [x] T001 Scaffold `infra/auth0-terraform/` from jobs-analyzer reference (`main.tf`, `versions.tf`, `variables.tf`, `outputs.tf`, `api.tf`, `client.tf`, `scopes.tf`, `Makefile`) adapted to web0personal-vector naming
- [x] T002 [P] Add `terraform.tfvars.example` and `README.md` in `infra/auth0-terraform/` with M2M credential and URL placeholders per `specs/003-auth0-integration/contracts/terraform-env-mapping.md`
- [x] T003 [P] Ensure `infra/auth0-terraform/terraform.tfvars` and `.terraform/` are gitignored in `.gitignore`
- [x] T004 [P] Add `@auth0/auth0-spa-js` and `@astrojs/node` to `apps/frontend/package.json` and run install
- [x] T005 [P] Verify Agno JWT middleware dependencies are available in `apps/backend/pyproject.toml` (add if missing)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared Auth0 configuration, SSR migration base, and removal of mock-auth assumptions.

**CRITICAL**: No user story E2E testing with real Auth0 until this phase completes. **Apply US3 Terraform (Phase 5, T031–T038) before manual US1/US2 E2E validation** — phase numbers reflect user-story priority (P1 before P2), not implementation order.

- [x] T006 Add `auth0_domain`, `auth0_issuer`, and `auth0_api_audience` settings to `apps/backend/src/agentos_chat/settings.py`; remove `mock_auth_subject`
- [x] T007 [P] Update `apps/backend/.env.example` with `AUTH0_*` variables and remove `MOCK_AUTH_SUBJECT` per `contracts/terraform-env-mapping.md`
- [x] T008 [P] Update `apps/frontend/.env.example` with `PUBLIC_AUTH0_*`, `AUTH0_SECRET`, and remove `PUBLIC_MOCK_IDENTITY`
- [x] T009 Migrate `apps/frontend/astro.config.ts` from `output: "static"` to `output: "server"` with `@astrojs/node` adapter
- [x] T010 Update `apps/frontend/Dockerfile` to run Astro SSR Node entry instead of `serve dist`
- [x] T011 [P] Create JWKS fetch helper and chat API `scope_mappings` builder in `apps/backend/src/agentos_chat/auth/jwt_middleware.py`
- [x] T012 [P] Refactor `apps/backend/tests/conftest.py` to remove `mock_headers` fixture and add JWT test token helpers for use by T046

**Checkpoint**: Auth settings, SSR base, and Terraform scaffold ready. Proceed to user stories.

---

## Phase 3: User Story 1 - Sign In to Use the Application (Priority: P1) MVP

> **CRITICAL — execution order**: Manual E2E for this phase requires **Phase 5 (US3) Terraform apply (T031–T038)** completed first. Implement code here in parallel with US2/US3, but do not validate real Google login until tenant credentials exist.

**Goal**: Visitors are redirected to Google Universal Login before protected pages render; federated logout works; only Google connection shown.

**Independent Test**: Open `/chat` in a private window → Auth0 Google login → return to app signed in → sign out → cannot access `/chat` without re-login. Non-allowlisted email blocked at Auth0 (requires US3 Terraform apply).

### Implementation for User Story 1

- [x] T013 [P] [US1] Create Auth0 SPA client wrapper with login/logout/getAccessToken helpers in `apps/frontend/src/lib/auth0.ts`
- [x] T014 [P] [US1] Implement `/api/auth/login` endpoint redirecting to Auth0 authorize URL in `apps/frontend/src/pages/api/auth/login.ts`
- [x] T015 [P] [US1] Implement `/api/auth/callback` OAuth code exchange and session cookie in `apps/frontend/src/pages/api/auth/callback.ts`
- [x] T016 [P] [US1] Implement `/api/auth/logout` federated logout via Auth0 `/v2/logout` in `apps/frontend/src/pages/api/auth/logout.ts`
- [x] T017 [US1] Implement Astro auth gate with public route allowlist in `apps/frontend/src/middleware.ts` (auth handlers, static assets exempt per FR-014/FR-027)
- [x] T018 [US1] Add sign-out control and signed-in state indicator to `apps/frontend/src/components/ChatBox.tsx`
- [x] T019 [US1] Handle session-expiry and auth error UI states per FR-016 (session expired, IdP unavailable, API auth failed; no secrets) in `apps/frontend/src/components/ChatBox.tsx`
- [x] T020 [P] [US1] Add frontend auth helper unit tests for token/header builder in `apps/frontend/tests/auth-helpers.test.ts`

**Checkpoint**: Frontend auth gate and login/logout flow work; API calls may still use mock until US2.

---

## Phase 4: User Story 2 - Secure Chat and Data Access (Priority: P1)

**Goal**: All chat API calls use Bearer tokens; backend validates JWT via Agno middleware with `access:api` scope; lazy UserIdentity provisioning; mock identity removed.

**Independent Test**: Sign in, send chat message with Bearer token, reload history; `curl` without token returns 401; token without scope returns 403; first request creates UserIdentity for Auth0 `sub`.

### Tests for User Story 2

- [x] T021 [P] [US2] Add unit tests for JWKS helper and scope mappings in `apps/backend/tests/unit/test_auth_jwt.py`
- [x] T022 [P] [US2] Add integration tests for 401/403, owner-scoped sessions, and clean-break history (Auth0 `sub` excludes mock-owned rows per FR-019/SC-011) in `apps/backend/tests/integration/test_auth_api.py`
- [x] T046 [P] [US2] Migrate existing contract and integration tests from `mock_headers` to JWT fixtures in `apps/backend/tests/contract/test_chat_sessions_contract.py`, `test_chat_stream_contract.py`, `test_stop_run_contract.py`, and `apps/backend/tests/integration/test_chat_history_context.py`

### Implementation for User Story 2

- [x] T023 [US2] Register Agno `JWTMiddleware` in `apps/backend/src/agentos_chat/main.py` with RS256, dynamic JWKS from issuer, `verify_audience=True`, `authorization=True`, `scopes_claim="scope"`, and `excluded_route_paths=["/health"]`
- [x] T024 [US2] Configure custom `scope_mappings` for all `/api/chat/*` routes requiring `access:api` in `apps/backend/src/agentos_chat/auth/jwt_middleware.py`
- [x] T025 [US2] Replace mock `get_current_identity` with JWT `sub` extraction and `get_or_create_identity` lazy provisioning in `apps/backend/src/agentos_chat/auth/dependencies.py`
- [x] T026 [US2] Add structured auth failure logging (issuer/audience/scope/expiry codes, no token body) in `apps/backend/src/agentos_chat/services/logging.py`
- [x] T027 [US2] Update `apps/frontend/src/services/chatApi.ts` to attach `Authorization: Bearer` on all fetch/SSE calls; remove `X-Mock-Identity`
- [x] T028 [US2] Implement silent token refresh and single retry on 401 before re-auth prompt in `apps/frontend/src/services/chatApi.ts`
- [x] T029 [US2] Update OpenAPI security scheme from MockIdentity to Auth0Bearer in `specs/001-agentos-chat-search/contracts/openapi.yaml` per `specs/003-auth0-integration/contracts/auth-api-security.md`
- [x] T030 [US2] Remove mock identity references from backend API route docstrings and error messages in `apps/backend/src/agentos_chat/api/sessions.py`, `messages.py`, `stream.py`, and `runs.py`

**Checkpoint**: End-to-end authenticated chat works with real Auth0 tokens (requires tenant config from US3).

---

## Phase 5: User Story 3 - Provision and Deploy Authentication Configuration (Priority: P2)

> **CRITICAL — execution order**: Complete Terraform apply (T038) **before** manual E2E validation of US1/US2, even though this phase is numbered after US1/US2.

**Goal**: Maintainers provision Auth0 API, SPA, Google connection, and email-allowlist Action via Terraform; env mapping documented for local and Railway.

**Independent Test**: Run `make apply` in `infra/auth0-terraform/`; verify outputs map to `.env` files; sign-in works locally with allowlisted Gmail; re-apply is idempotent.

### Implementation for User Story 3

- [x] T031 [P] [US3] Add `connection_google.tf` enabling Google OAuth2 for SPA client only in `infra/auth0-terraform/connection_google.tf`
- [x] T032 [P] [US3] Add `action_allowlist.tf` with post-login email allowlist Action (`allowed_emails` variable, initial `luismoridev@gmail.com`) in `infra/auth0-terraform/action_allowlist.tf`
- [x] T033 [US3] Add `trigger_actions.tf` binding allowlist Action to post-login flow in `infra/auth0-terraform/trigger_actions.tf`
- [x] T034 [US3] Extend `variables.tf` and `outputs.tf` with `allowed_emails`, `auth0_domain`, callback/logout/web_origin lists for localhost and Railway placeholders in `infra/auth0-terraform/`
- [x] T035 [US3] Update `client.tf` callback URLs to include `/api/auth/callback` pattern in `infra/auth0-terraform/client.tf`
- [x] T036 [US3] Document Terraform workflow and output→env mapping in `infra/auth0-terraform/README.md`
- [x] T037 [US3] Update `infra/railway/project.env.example` with `BACKEND_ENV_SYNC_KEYS` and `FRONTEND_ENV_SYNC_KEYS` for Auth0 variables per `contracts/terraform-env-mapping.md`
- [ ] T038 [US3] Manual verification: `terraform apply`, populate `apps/backend/.env` and `apps/frontend/.env`, confirm Google login and allowlist deny per `specs/003-auth0-integration/quickstart.md`

**Checkpoint**: Auth0 tenant fully provisioned as code; local and Railway env documented.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Deployment smoke tests, mock cleanup, docs, and full quickstart validation.

- [x] T039 Update `infra/railway/smoke_test.py` to accept frontend 302/307 redirect and require backend `/health` 2xx per FR-030
- [x] T040 [P] Remove remaining `MOCK_AUTH_SUBJECT` / `PUBLIC_MOCK_IDENTITY` / `X-Mock-Identity` references across repo via grep (backend, frontend, Makefile, specs cross-links)
- [x] T041 [P] Update `infra/railway/README.md` with Auth0 env sync and smoke-test expectations
- [x] T042 [P] Update root `readme.md` auth section to reference Auth0 quickstart instead of mock identity
- [x] T043 Run `make check` and `make test` after auth changes; fix regressions
- [ ] T044 Run full manual verification checklist in `specs/003-auth0-integration/quickstart.md` (sign-in, chat, logout, 401/403, smoke)
- [x] T045 [P] Update `specs/003-auth0-integration/checklists/requirements.md` notes if implementation diverges from spec

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS** user story E2E validation
- **US1 (Phase 3)**: Depends on Foundational (SSR base, env examples)
- **US2 (Phase 4)**: Depends on Foundational; integrates with US1 for full E2E (Bearer tokens from frontend)
- **US3 (Phase 5)**: Can start after Setup (Terraform files); **required before real Auth0 E2E** for US1/US2
- **Polish (Phase 6)**: Depends on US1 + US2 + US3

### User Story Dependencies

- **US1 (P1)**: Frontend auth gate — independently testable via login redirect/logout
- **US2 (P1)**: Backend JWT — independently testable via curl + test JWT; full chat E2E needs US1 + US3
- **US3 (P2)**: Terraform — independent `terraform apply` verification; unblocks production-like US1/US2 testing

### Recommended Execution Order

1. Phase 1 → Phase 2
2. **US3 Terraform (Phase 5) — mandatory before real Auth0 E2E**: T031–T038 + `terraform apply` + populate `.env` files
3. US1 + US2 in parallel (different developers) after Phase 2; full E2E after step 2
4. Phase 6 polish

### Parallel Opportunities

- **Phase 1**: T002, T003, T004, T005 in parallel after T001
- **Phase 2**: T007, T008, T011, T012 in parallel after T006
- **US1**: T013–T016, T020 in parallel; then T017–T019 sequential
- **US2**: T021, T022, T046 parallel after T012; T023–T025 sequential; T027–T028 parallel with T030
- **US3**: T031, T032 parallel; then T033–T036
- **Polish**: T040, T041, T042, T045 parallel

---

## Parallel Example: User Story 2

```bash
# Tests in parallel (after T012 JWT fixtures):
T021: apps/backend/tests/unit/test_auth_jwt.py
T022: apps/backend/tests/integration/test_auth_api.py
T046: apps/backend/tests/contract/*.py + test_chat_history_context.py

# After middleware lands, parallel frontend/backend:
T027: apps/frontend/src/services/chatApi.ts
T030: apps/backend/src/agentos_chat/api/*.py
```

---

## Implementation Strategy

### MVP First (US1 + US2 with manual Auth0 tenant)

1. Complete Phase 1 + Phase 2
2. Apply US3 Terraform (or configure Auth0 dashboard once) for tenant credentials
3. Complete US1 frontend auth + US2 backend JWT
4. **STOP and VALIDATE** per quickstart manual verification
5. Deploy via Railway with updated env sync

### Incremental Delivery

1. Setup + Foundational → SSR and settings ready
2. US3 Terraform → tenant provisioned
3. US1 → login/logout/middleware
4. US2 → JWT + chat API → **MVP authenticated chat**
5. Polish → smoke tests, docs, mock removal audit

### Task Summary

| Phase | Tasks | Story |
|-------|-------|-------|
| Setup | T001–T005 (5) | — |
| Foundational | T006–T012 (7) | — |
| US1 Sign In | T013–T020 (8) | US1 |
| US2 Secure API | T021–T030, T046 (11) | US2 |
| US3 Terraform | T031–T038 (8) | US3 |
| Polish | T039–T045 (7) | — |
| **Total** | **46** | |

**Suggested MVP scope**: Phase 1–2 + US3 (apply) + US1 + US2 (T001–T030, T038, T046) — authenticated chat with real Auth0.

**Independent test criteria**:

- **US1**: Private window `/chat` → Google login → logout → re-auth required
- **US2**: Bearer chat API works; no token → 401; wrong scope → 403; lazy UserIdentity create
- **US3**: `terraform apply` idempotent; env outputs documented; allowlist blocks non-Gmail

---

## Notes

- Mock-owned chat history remains in DB but is not visible to Auth0 users (clean break)
- Email allowlist enforced only in Auth0 Action — not in backend code
- Frontend SSR migration is mandatory for `middleware.ts` (research.md §6)
- Run `make check` and targeted auth tests after each checkpoint
