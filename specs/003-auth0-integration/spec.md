# Feature Specification: Auth0 Integration

**Feature Branch**: `003-auth0-integration`  
**Created**: 2026-05-18  
**Status**: Draft  
**Input**: User description: "add auth0 integration for frontend and backend. Infrastructure uses Auth0 Terraform provider; infra/auth0-terraform based on jobs-analyzer example; M2M token for Terraform; frontend global page protection; backend API authorization tokens; backend JWT token validation."

## Clarifications

### Session 2026-05-18

- Q: What happens to chat history created under the mock identity when real Auth0 is enabled? → A: Clean break — mock-owned history is not visible after Auth0 sign-in; users start fresh under their Auth0 identity.
- Q: Who may sign in and use the app? → A: Email allowlist enforced at Auth0 login via Auth0 Action with a hardcoded list; currently only `luismoridev@gmail.com` is permitted.
- Q: Local development authentication mode? → A: Auth0 required everywhere — local development must always use real Auth0; mock identity is not supported.
- Q: Auth0 tenant strategy across environments? → A: Single tenant — one Auth0 tenant and SPA/API for local and production; different callback/logout/origin URLs in the same client.
- Q: Access credential expires during an active chat request? → A: Silent refresh — attempt token refresh automatically, retry the failed request once; if refresh fails, prompt re-auth without losing page state or unsent input.
- Q: Sign-in connection types? → A: Google social login only — user must sign in with Google using the allowlisted Gmail address.
- Q: Auth0 Action allowlist deployment method? → A: Full Terraform — email-allowlist Action is a Terraform resource in `infra/auth0-terraform` alongside SPA/API.
- Q: Public routes exempt from sign-in? → A: Standard SPA — auth callback/logout routes, static assets (favicon, fonts, bundled public files), and backend `/health`; all application pages require sign-in.
- Q: User identity record on first sign-in? → A: Lazy provisioning — backend auto-creates the UserIdentity record on the first authenticated API request.
- Q: Backend email allowlist enforcement? → A: Action-only — backend validates token authenticity only; email allowlist enforced solely by Auth0 Action at login.
- Q: Backend API scope enforcement? → A: Enforce scope — JWT middleware RBAC enabled; all protected endpoints require the `access:api` scope in the token.
- Q: Sign-out behavior? → A: Federated logout — clear app session and redirect through Auth0 logout to end the IdP session.
- Q: Frontend global auth gate mechanism? → A: Hybrid — Astro middleware gate before render + Auth0 client SDK for login, tokens, refresh, and API authorization headers.
- Q: Deployment smoke test for auth-gated frontend? → A: Reachability smoke — frontend smoke accepts 302/307 redirect to Auth0/login as success; backend `/health` still requires 2xx.
- Q: Backend JWT signing key verification? → A: Dynamic JWKS — backend fetches/uses Auth0 tenant JWKS from the issuer URL (supports key rotation).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sign In to Use the Application (Priority: P1)

A visitor who opens any application page is guided to sign in through the identity provider
before they can view content or use chat features. After successful sign-in, they return to the
application and can use protected features without re-entering credentials until their session
expires or they sign out.

**Why this priority**: Without real authentication, persisted chat history and agent access
remain vulnerable. Sign-in is the foundation for every other protected capability.

**Independent Test**: Open the application in a private browser window, confirm redirect to
sign-in, complete login, and verify the chat page loads with the authenticated user's identity.

**Acceptance Scenarios**:

1. **Given** a visitor is not signed in, **When** they open any protected application page, **Then** Astro middleware redirects them to sign in before page content is rendered.
2. **Given** a visitor completes sign-in successfully, **When** they return to the application, **Then** they can access protected pages and their identity is recognized for the session.
3. **Given** a signed-in visitor, **When** they sign out, **Then** the application session is cleared, Auth0 federated logout completes, and they cannot access protected pages without signing in again through Google.
4. **Given** a signed-in visitor whose session expires, **When** they attempt to use the application, **Then** they are prompted to sign in again and see a clear message rather than a broken page.
5. **Given** a visitor attempts sign-in with an email not on the allowlist, **When** Auth0 processes login, **Then** access is denied before the application receives valid credentials and the visitor sees a clear unauthorized message.
6. **Given** a visitor opens Universal Login, **When** they view available sign-in options, **Then** only Google social login is offered (no email/password or other connections).

---

### User Story 2 - Secure Chat and Data Access (Priority: P1)

A signed-in visitor uses chat and related features knowing that only their authenticated
identity can load their history and invoke backend capabilities. Every backend interaction
carries proof of identity, and the server rejects unauthenticated or invalid requests before
any personal data or agent tools are reached.

**Why this priority**: The application stores user-owned chat history and exposes agent
capabilities. Token-backed access control is required to replace the temporary mock identity
and satisfy production security expectations.

**Independent Test**: Sign in, send a chat message, reload the page and confirm history
restores for the same user; attempt the same API call without credentials and confirm access
is denied.

**Acceptance Scenarios**:

1. **Given** a signed-in visitor submits a chat message, **When** the frontend calls the backend, **Then** the request includes a valid access credential issued for the application API.
2. **Given** a request arrives without a valid access credential, **When** the backend handles a protected endpoint, **Then** the request is rejected with an unauthorized response and no user data is returned.
3. **Given** a request arrives with a valid token missing the `access:api` scope, **When** the backend handles a protected endpoint, **Then** the request is rejected with a forbidden response and no user data is returned.
4. **Given** a signed-in visitor reloads the chat page, **When** history is restored, **Then** only sessions owned by that visitor's identity are loaded.
5. **Given** a visitor signs in with Google for the first time, **When** they make their first authenticated API request, **Then** a UserIdentity record is created automatically and subsequent chat data is owned by that Auth0 subject.
6. **Given** two different signed-in visitors, **When** each loads chat history, **Then** neither can view or modify the other's sessions or messages.
7. **Given** an access credential is expired or tampered with, **When** the visitor calls a protected endpoint, **Then** the backend rejects the request and the frontend attempts silent token refresh, retries the request once, and only then prompts re-authentication or shows a recoverable error while preserving page state and unsent input.

---

### User Story 3 - Provision and Deploy Authentication Configuration (Priority: P2)

A maintainer provisions the identity provider configuration—API resource, web application
registration, allowed URLs, and access scopes—in a repeatable way, then maps the resulting
values into local and deployed environment configuration so frontend and backend services
authenticate against the same tenant.

**Why this priority**: Manual dashboard setup is error-prone and hard to reproduce across
local, staging, and production environments. Declarative provisioning unblocks consistent
deployment.

**Independent Test**: Run the documented provisioning workflow from a clean state, apply
configuration, and verify sign-in works locally and that output values map to the expected
environment variables for frontend and backend services.

**Acceptance Scenarios**:

1. **Given** a maintainer has tenant administrator credentials, **When** they run the documented provisioning workflow, **Then** an API resource, web application, and required access scope are created or updated idempotently.
2. **Given** provisioning completes successfully, **When** the maintainer reviews outputs, **Then** they receive the values needed to configure frontend sign-in and backend token validation (issuer, API audience, client identifier).
3. **Given** local and production deployment URLs differ, **When** the maintainer updates allowed callback, logout, and origin URLs, **Then** sign-in and sign-out work in each environment without manual dashboard edits beyond the provisioning workflow, using a single Auth0 tenant and SPA client with all environment URLs registered.
4. **Given** provisioning secrets for automation, **When** stored locally, **Then** they are excluded from version control and documented only through example templates.
5. **Given** provisioning completes successfully, **When** the maintainer reviews identity configuration, **Then** the email-allowlist Auth0 Action is deployed as a Terraform-managed resource with the initial permitted address.

---

### Edge Cases

- Visitor bookmarks a protected page and returns after session expiry.
- Visitor opens multiple tabs; sign-out in one tab invalidates access in others after federated logout completes.
- Identity provider is temporarily unavailable during sign-in or token refresh.
- Frontend has a token but backend validation fails due to audience or issuer mismatch.
- Deployment uses new public URLs that were not yet added to allowed callback or origin lists.
- Maintainer re-runs provisioning and expects no unintended destructive changes to existing clients.
- Visitor attempts direct API access bypassing the frontend.
- Chat streaming request fails mid-response due to expired credentials; frontend attempts silent refresh and retries once before prompting re-auth.
- Local development environment uses different host/port than production and requires Auth0 callback URLs registered for localhost.
- A first-time Google sign-in triggers UserIdentity creation on the first authenticated backend request, not at login redirect.
- A developer cannot run the application locally without valid Auth0 tenant configuration and allowlisted credentials.
- A visitor had chat history under the mock identity before Auth0 was enabled; after Auth0 sign-in they see no prior mock-owned sessions.
- Mock-owned sessions remain in storage but are inaccessible to Auth0 identities unless a future migration feature is added.
- A visitor attempts sign-in with a non-Google connection or a Google account whose email is not on the allowlist.
- Allowlist changes require updating the Terraform-managed Auth0 Action and running plan/apply; manual dashboard edits are not the source of truth.
- Auth0 rotates signing keys; backend dynamic JWKS lookup must resolve the correct key by `kid` without redeployment.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST require sign-in before displaying any protected frontend application page via Astro server middleware; exempt frontend routes are limited to auth callback/logout handlers and static assets (backend `/health` is public per FR-014, not gated by Astro middleware). The Auth0 client SDK handles login, token storage, refresh, and attaching authorization headers to backend API calls.
- **FR-002**: System MUST use a centralized sign-in experience hosted by the identity provider (Universal Login) with Google as the only enabled connection.
- **FR-003**: System MUST support sign-out by clearing the application session and completing federated logout through Auth0 so the identity provider session is also terminated.
- **FR-004**: System MUST obtain access credentials scoped for the application backend API after successful sign-in.
- **FR-005**: System MUST attach a valid access credential to every frontend-initiated call to protected backend endpoints.
- **FR-006**: System MUST validate access credentials on the backend before serving protected endpoints, including chat, session history, and agent runs; validation covers token authenticity (RS256 signature via Auth0 tenant JWKS from issuer URL, issuer, audience, expiry) and RBAC scope enforcement requiring the `access:api` scope; email allowlist checks are not duplicated in backend code.
- **FR-007**: System MUST derive the authenticated user identity from validated token claims and use it for all owner-scoped data access; on first authenticated request for a new Auth0 subject, the backend MUST auto-create the corresponding UserIdentity record (lazy provisioning).
- **FR-008**: System MUST reject requests with missing, expired, or invalid credentials without exposing protected data.
- **FR-009**: System MUST continue to enforce per-identity ownership of chat sessions and messages established in the prior feature.
- **FR-010**: System MUST remove the temporary mock identity mechanism; all environments including local development MUST use real Auth0 authentication with no mock bypass (supersedes former FR-023).
- **FR-019**: System MUST NOT expose chat sessions or messages owned by mock identities to Auth0-authenticated users; Auth0 sign-in starts with empty history for that identity.
- **FR-020**: System MUST restrict application access to an allowlisted set of email addresses; only allowlisted users may complete sign-in and obtain API credentials.
- **FR-021**: System MUST enforce the email allowlist at identity-provider login time (Auth0 Action) so non-allowlisted users are blocked before receiving access credentials.
- **FR-022**: System MUST maintain the allowlist as a configurable hardcoded list; the initial allowed address is `luismoridev@gmail.com`.
- **FR-011**: System MUST allow maintainers to provision identity configuration reproducibly via Terraform, including API resource, web application, Google social connection, callback URLs, logout URLs, web origins, API access scope, and the email-allowlist Auth0 Action as code in `infra/auth0-terraform`.
- **FR-012**: System MUST document required environment values for frontend sign-in and backend validation after provisioning.
- **FR-013**: System MUST exclude provisioning secrets and live credentials from version control.
- **FR-014**: System MUST keep the following accessible without user sign-in: auth callback and logout handler routes, static assets (favicon, fonts, bundled public files), and backend `/health` (or equivalent smoke-test path).
- **FR-027**: System MUST NOT require sign-in for static asset requests or auth protocol handler routes; all other frontend application pages (`/`, `/chat`, and future app routes) require sign-in.
- **FR-028**: System MUST NOT duplicate email allowlist enforcement in backend application code; the Terraform-managed Auth0 Action is the sole allowlist gate at login.
- **FR-015**: System MUST handle token refresh or re-authentication so visitors can continue using the app without unexpected data loss when credentials expire during an active session; on credential failure the frontend MUST attempt silent token refresh, retry the failed protected request once, and only then prompt re-authentication while preserving page state and unsent input.
- **FR-016**: System MUST show user-readable errors when authentication fails, without exposing internal validation details or secrets. Minimum required error states and guidance:
  - **Session expired** (silent refresh failed): message such as "Your session expired. Sign in again to continue." with a sign-in action; visible chat transcript and compose input MUST be preserved.
  - **Allowlist denied**: visitor sees Auth0's unauthorized message before reaching the application (no API credentials issued).
  - **Identity provider unavailable**: message such as "Sign-in is temporarily unavailable. Try again in a few minutes." with a retry affordance.
  - **API authorization failed** (401/403 after silent refresh retry): message such as "Unable to access your data. Sign in again or contact support." without token, issuer, or audience details.
- **FR-017**: System MUST support separate allowed URL configuration for local development and deployed environments within a single Auth0 tenant and SPA client (localhost and production callback, logout, and origin URLs registered together).
- **FR-018**: System MUST map provisioning outputs to frontend public configuration (domain, client ID, API audience) and backend validation configuration (issuer, API audience); the same tenant values apply locally and in production.
- **FR-024**: System MUST enable only the Google social login connection in Auth0; email/password (database) and other connections are disabled.
- **FR-025**: System MUST require allowlisted users to authenticate via Google with the Google account whose email matches an entry on the allowlist.
- **FR-026**: System MUST define the email-allowlist Auth0 Action as a Terraform-managed resource; allowlist changes are applied through Terraform plan/apply, not manual dashboard edits.
- **FR-029**: System MUST implement a hybrid frontend auth gate: Astro server middleware enforces authentication before page render on protected routes using an httpOnly server session cookie established at OAuth callback (signed with `AUTH0_SECRET`); the Auth0 client SDK separately manages OAuth login/logout, API access token lifecycle, silent refresh, and `Authorization` headers on backend requests.
- **FR-030**: System MUST update deployment smoke tests so backend `/health` requires a 2xx response and frontend smoke treats 302/307 redirect to Auth0/login as successful reachability for unauthenticated requests to protected pages.
- **FR-031**: System MUST verify JWT signatures using dynamic JWKS from the Auth0 tenant issuer URL so key rotation is supported without redeployment.

### Constitution Requirements *(mandatory when applicable)*

- **RAG Grounding**: N/A — this feature does not change retrieval sources. Existing chat answers remain grounded in public search results; authentication ensures only the owning identity triggers agent runs and receives history context.
- **Agent Behavior**: Agent tool permissions remain unchanged. Every agent run MUST continue to receive only the authenticated identity's active session history. Authentication failures MUST prevent agent invocation.
- **Auth0 Authorization**: Real Auth0-backed identity replaces the temporary stand-in identity in all environments including local development; mock identity is removed. Backend MUST validate access credentials (signature, issuer, audience, expiry) and enforce the `access:api` scope via JWT middleware RBAC on all protected endpoints; email allowlist checks are not duplicated in application code. Persisted chat history MUST remain partitioned by verified user identifier from the identity provider. A single first-party API access scope (`access:api`) grants baseline backend access; elevated admin scopes are out of scope unless added in a future feature. Access is limited to an email allowlist enforced by a Terraform-managed Auth0 Action at login; only `luismoridev@gmail.com` is permitted initially.
- **Data and Vector Search**: No schema changes required. Existing owner identity fields MUST bind to verified Auth0 subjects. Authorization-aware filters MUST apply before returning sessions or messages.
- **Deployment and Observability**: Auth configuration MUST integrate with Railway deployment: frontend and backend services receive documented environment variables; smoke tests MUST verify backend `/health` returns 2xx without user tokens and frontend reachability accepts 302/307 redirect to Auth0/login for unauthenticated requests to protected pages; auth failures MUST emit structured logs suitable for diagnosing issuer, audience, or expiry mismatches without logging token contents.

### Key Entities *(include if feature involves data)*

- **Authenticated User**: A person who has completed sign-in; identified by a stable subject claim from the identity provider.
- **Access Credential**: A short-lived JWT access token authorizing calls to the application backend API, including audience and expiry; obtained via the Auth0 SPA SDK and sent as `Authorization: Bearer`.
- **Server Session**: An httpOnly cookie set after OAuth callback; used by Astro middleware to gate SSR on protected frontend routes; distinct from the API access credential.
- **Identity Configuration**: The set of provisioned resources defining how the web application and backend API trust one another (application registration, API identifier, allowed URLs, scopes).
- **Provisioning Credentials**: Maintainer-only credentials used to automate identity configuration setup; never exposed to end users or client code.
- **Protected Page**: Any application route that requires sign-in before rendering application content (excludes auth handlers and static assets).
- **Public Route**: Auth callback/logout handlers, static assets, and backend health endpoints reachable without sign-in.
- **User Identity** (existing): Maps an Auth0 subject to persisted chat ownership; auto-created on first authenticated API request for a new subject (lazy provisioning).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of unauthenticated attempts to open protected application pages result in redirect to sign-in within 2 seconds.
- **SC-002**: 95% of visitors complete sign-in and reach a protected page within 30 seconds under normal identity provider availability.
- **SC-003**: 100% of protected backend requests without a valid access credential are rejected with no user-owned data returned.
- **SC-004**: 100% of chat history restore operations after sign-in return only data owned by the authenticated identity.
- **SC-005**: 100% of cross-identity access attempts (viewing or modifying another user's sessions) are blocked.
- **SC-006**: A maintainer can provision identity configuration from documented steps and achieve working local sign-in within 20 minutes when tenant credentials are available.
- **SC-007**: Re-running provisioning against an unchanged desired configuration produces no unintended resource drift in 100% of verification runs.
- **SC-008**: 100% of frontend calls to protected backend endpoints include an access credential when the visitor is signed in.
- **SC-009**: 95% of signed-in visitors who reload the chat page see their history restored within 2 seconds.
- **SC-010**: 100% of authentication error states shown to visitors include actionable guidance (sign in again, retry, or contact support) without exposing secrets or token contents.
- **SC-011**: 100% of Auth0 sign-in attempts return zero mock-owned chat sessions in the restored history.
- **SC-012**: 100% of sign-in attempts from non-allowlisted email addresses are blocked before the application issues or accepts API credentials.
- **SC-013**: 100% of credential-expiry failures during protected requests trigger silent refresh and a single retry before showing a re-authentication prompt.
- **SC-014**: 100% of protected backend requests with a valid token missing the `access:api` scope are rejected with no user-owned data returned.
- **SC-015**: 100% of deployment smoke test runs pass when backend `/health` returns 2xx and frontend returns 302/307 to Auth0/login for unauthenticated `/` requests.

## Assumptions

- Auth0 is the identity provider, consistent with project constitution and prior feature design.
- The application has a single web client (SPA) and a single backend API resource with one baseline access scope (e.g., `access:api`).
- Universal Login is the sign-in method with Google as the only enabled connection; email/password, other social providers, and multi-tenant B2B organizations are out of scope.
- All current application pages (`/` redirect and `/chat`) require authentication; auth callback/logout handler routes, static assets, and backend health checks remain public.
- Provisioning follows an established reference pattern from a prior project in the same organization, adapted to this application's name, URLs, and deployment environments; the email-allowlist Action is included as Terraform code (extension beyond the reference module).
- Automation credentials used only for provisioning are supplied via local secrets files or environment variables, not committed to the repository.
- Local development uses the same real Auth0 authentication flow as deployed environments; mock identity is not supported.
- A single Auth0 tenant, API resource, and SPA client serve both localhost and production; provisioning registers callback, logout, and web-origin URLs for all environments in one client.
- Transitioning to Auth0 is a clean break: mock-owned chat history is not migrated or linked to Auth0 identities; Auth0 users begin with empty history.
- Application access is restricted to an email allowlist enforced by an Auth0 Action at login; the initial allowlist contains only `luismoridev@gmail.com`.
- Adding or removing allowed emails requires updating the Terraform-managed Auth0 Action allowlist and running plan/apply; self-service user management is out of scope.
- Re-authentication after failed silent refresh preserves visible chat transcript and any text in the compose input.
- Role-based access beyond baseline API access is out of scope for this release.
- Email allowlist enforcement is exclusively at Auth0 login via Terraform-managed Action; the backend trusts valid tokens without re-checking email claims.
- Backend JWT middleware enables RBAC and requires the `access:api` scope on all protected endpoints.
- Frontend uses hybrid auth: Astro server middleware gates protected pages via an httpOnly session cookie set at OAuth callback (`AUTH0_SECRET`); Auth0 client SDK separately manages API access tokens and `Authorization` headers.
- Backend JWT verification uses dynamic JWKS from the Auth0 issuer URL (RS256); static key files are not the primary approach.
