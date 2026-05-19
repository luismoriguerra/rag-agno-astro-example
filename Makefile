.PHONY: install dev check test db-up db-down migrate smoke-local \
	railway-preflight railway-up railway-deploy railway-status railway-smoke \
	railway-logs-backend railway-logs-frontend

BACKEND_DIR := apps/backend
FRONTEND_DIR := apps/frontend
E2E_DIR := apps/playwright_e2e

install:
	cd $(BACKEND_DIR) && pip install -e ".[dev]"
	cd $(FRONTEND_DIR) && npm install

e2e-install:
	cd $(E2E_DIR) && npm install
	cd $(E2E_DIR) && npx playwright install chromium

e2e:
	@echo "Requires: make db-up migrate, make dev (or dev-frontend + dev-backend)"
	cd $(E2E_DIR) && npm test

e2e-headed:
	cd $(E2E_DIR) && npm run test:headed

e2e-ui:
	cd $(E2E_DIR) && npm run test:ui

db-up:
	docker compose up -d postgres

db-down:
	docker compose down

migrate:
	cd $(BACKEND_DIR) && alembic upgrade head

dev:
	$(MAKE) -j2 dev-backend dev-frontend

dev-backend:
	cd $(BACKEND_DIR) && uvicorn agentos_chat.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd $(FRONTEND_DIR) && npm run dev

check:
	cd $(BACKEND_DIR) && ruff check src tests && mypy src
	cd $(FRONTEND_DIR) && npm run check

test:
	cd $(BACKEND_DIR) && pytest -q
	cd $(FRONTEND_DIR) && npm test

smoke-local:
	python infra/railway/smoke_test.py --local

railway-preflight:
	@command -v railway >/dev/null || (echo "Install Railway CLI: https://docs.railway.com/develop/cli" && exit 1)
	@command -v jq >/dev/null || (echo "Install jq" && exit 1)

railway-up:
	bash infra/railway/railway_up.sh

railway-deploy:
	railway up --service agentos-chat-backend
	railway up --service agentos-chat-frontend

railway-status:
	railway status

railway-smoke:
	python infra/railway/smoke_test.py

railway-logs-backend:
	railway logs --service agentos-chat-backend

railway-logs-frontend:
	railway logs --service agentos-chat-frontend
