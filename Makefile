.PHONY: install dev check test db-up db-down migrate smoke-local \
	railway-preflight railway-up railway-cleanup railway-deploy railway-status railway-smoke \
	railway-logs-backend railway-logs-frontend

BACKEND_DIR := apps/backend
FRONTEND_DIR := apps/frontend
E2E_DIR := apps/playwright_e2e

# Source infra/railway/project.env into a Railway recipe. Use as:
#   $(RAILWAY_ENV); <command using $$BACKEND_SERVICE etc.>
RAILWAY_ENV := set -a && . infra/railway/project.env && set +a

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

railway-cleanup:
	bash infra/railway/cleanup.sh

railway-deploy:
	@$(RAILWAY_ENV) && \
		railway up "$$BACKEND_DIR" --path-as-root --service "$$BACKEND_SERVICE" --detach -m "Deploy backend" && \
		railway up "$$FRONTEND_DIR" --path-as-root --service "$$FRONTEND_SERVICE" --detach -m "Deploy frontend"

railway-status:
	railway status

railway-smoke:
	@$(RAILWAY_ENV) && \
		eval "$$(bash infra/railway/configure_urls.sh 2>/dev/null | sed -nE 's/^(BACKEND_URL|FRONTEND_URL)=/export \1=/p')" && \
		RAILWAY_BACKEND_SERVICE="$$BACKEND_SERVICE" \
		RAILWAY_FRONTEND_SERVICE="$$FRONTEND_SERVICE" \
		SMOKE_BACKEND_PATH="$$SMOKE_BACKEND_PATH" \
		SMOKE_FRONTEND_PATH="$$SMOKE_FRONTEND_PATH" \
		python infra/railway/smoke_test.py

railway-logs-backend:
	@$(RAILWAY_ENV) && railway logs --service "$$BACKEND_SERVICE"

railway-logs-frontend:
	@$(RAILWAY_ENV) && railway logs --service "$$FRONTEND_SERVICE"
