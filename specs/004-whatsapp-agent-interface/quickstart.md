# Quickstart: WhatsApp Agent Interface

## Prerequisites

- Python 3.12, Node.js 22, Make, Docker (local Postgres)
- Auth0 tenant configured (see `specs/003-auth0-integration/quickstart.md`)
- Meta Developer account with WhatsApp Business API access
- ngrok (or similar) for local webhook tunneling
- OpenRouter API key (existing)

## 1. Meta App setup (one-time)

1. Create app at [Meta Developer Dashboard](https://developers.facebook.com/apps/).
2. Add **WhatsApp** product → **API Setup**.
3. Note **Phone number ID**, generate **Temporary access token** (or System User token for production).
4. Set a **Verify token** string (any secret you choose) — same value as `WHATSAPP_VERIFY_TOKEN`.
5. Under **Configuration**, set webhook callback URL (after backend is reachable):
   - Local: `https://{ngrok-subdomain}.ngrok.io/whatsapp/webhook`
   - Production: `https://{railway-backend}/whatsapp/webhook`
6. Subscribe to **messages** field.
7. Copy **App Secret** from App Settings → Basic → `WHATSAPP_APP_SECRET`.

Reference: [Agno WhatsApp docs](https://docs.agno.com/agent-os/interfaces/whatsapp/introduction)

## 2. Backend environment

Add to `apps/backend/.env`:

```bash
# Existing vars (DATABASE_URL, AUTH0_*, OPENROUTER_API_KEY, ...)

# WhatsApp (optional — app starts without these)
WHATSAPP_ACCESS_TOKEN=your-meta-access-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_VERIFY_TOKEN=your-chosen-verify-token
WHATSAPP_APP_SECRET=your-meta-app-secret

# Local dev only
WHATSAPP_SKIP_SIGNATURE_VALIDATION=true
```

If WhatsApp vars are omitted, backend starts normally; WhatsApp routes are not mounted.

## 3. Database migration

```bash
make db-up
make migrate   # applies 002_whatsapp_settings when implemented
```

## 4. Local run

**Terminal 1 — app**:

```bash
make install
make dev
```

**Terminal 2 — webhook tunnel**:

```bash
ngrok http 8000
```

Register ngrok HTTPS URL + `/whatsapp/webhook` in Meta dashboard. Click **Verify and save** while backend is running.

## 5. Enable WhatsApp via Profile

1. Open `http://localhost:4321/` → sign in via Auth0.
2. Navigate to **Profile** in sidebar.
3. Toggle **Enable WhatsApp chat** ON.
4. (Optional) Add your phone in E.164 format to allowlist.
5. Send a WhatsApp message to the Meta test number from your phone.

## 6. Manual verification checklist

| # | Step | Expected |
|---|------|----------|
| 1 | Backend without WhatsApp env vars | Starts; logs warning; `/health` 200 |
| 2 | Meta webhook verify (GET) | 200 + challenge echo |
| 3 | Invalid signature POST (prod mode) | 403 |
| 4 | WhatsApp disabled in Profile | Inbound messages silently ignored |
| 5 | Enable + empty allowlist | Bot replies to any number |
| 6 | Add allowlist entry | Only that number gets replies |
| 7 | Send follow-up question | Context-aware answer (10-turn window) |
| 8 | Send `/new` then question | No prior context referenced |
| 9 | REST `/chat` still works | No regression (SC-006) |
| 10 | Force agent error (e.g. invalid model key in dev) | User receives FR-007 generic error text; no silent failure |
| 11 | SC-002 parity set (§7 below) | ≥9/10 questions pass vs REST |

## 7. SC-002 REST/WhatsApp parity question set

Run each prompt through **REST chat** and **WhatsApp** (bot enabled). Mark **pass** when the WhatsApp reply contains the same core factual claim as the REST reply.

| # | Prompt | Core claim to match |
|---|--------|---------------------|
| 1 | What is the capital of France? | Paris |
| 2 | What is 15 × 7? | 105 |
| 3 | Who wrote Romeo and Juliet? | Shakespeare / William Shakespeare |
| 4 | What is the chemical symbol for gold? | Au |
| 5 | In what year did World War II end? | 1945 |
| 6 | What is the largest planet in our solar system? | Jupiter |
| 7 | What language is primarily spoken in Brazil? | Portuguese |
| 8 | How many continents are there? | 7 / seven |
| 9 | What is the speed of light in vacuum (approx.)? | ~300,000 km/s or 299,792 km/s |
| 10 | Who painted the Mona Lisa? | Leonardo da Vinci / da Vinci |

**SC-002 pass**: ≥9/10 marked pass. Record results in task T049.

## 8. Railway production deploy

1. Add WhatsApp keys to `infra/railway/project.env` → `BACKEND_ENV_SYNC_KEYS`.
2. Set vars in `apps/backend/.env` locally, then:

```bash
make railway-preflight
make railway-deploy
make railway-cleanup   # sync URLs, smoke
```

3. Update Meta webhook URL to `https://{backend-service}-production.up.railway.app/whatsapp/webhook`.
4. Set production System User token (not temporary 24h token).
5. **Do not** set `WHATSAPP_SKIP_SIGNATURE_VALIDATION` in production.
6. Enable WhatsApp via Profile on production frontend.

## 9. Smoke commands

```bash
# Backend health (no auth)
curl -s http://localhost:8000/health

# Settings API (requires Bearer token)
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/whatsapp/settings

# Webhook verify (simulate Meta)
curl -s "http://localhost:8000/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=$WHATSAPP_VERIFY_TOKEN&hub.challenge=test123"
```

## 10. Troubleshooting

| Issue | Fix |
|-------|-----|
| No messages received | Confirm Meta webhook subscribed to `messages`; URL matches ngrok/Railway |
| 401 on webhook | Add `/whatsapp/webhook` to JWT excluded paths |
| 403 on webhook | Check `WHATSAPP_APP_SECRET` or use skip flag locally |
| Bot not replying | Check Profile toggle enabled; allowlist; token not expired |
| SSL errors (macOS) | `export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")` |
