SHELL := /bin/bash
NODE_BIN := $(HOME)/.nvm/versions/node/v$(shell cat .nvmrc)/bin
export PATH := $(NODE_BIN):$(PATH)

.PHONY: help install secrets sample-data dev-backend dev-frontend build test test-backend test-frontend e2e lint typecheck check docker

help:
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-16s %s\n", $$1, $$2}'

install: ## Install backend and frontend dependencies
	cd backend && uv sync --frozen
	cd frontend && npm ci

secrets: ## Print fresh random values for SESSION_SECRET, KEK_KEYS, LOG_HASH_PEPPER
	@cd backend && uv run python -c "import secrets,base64;print('SESSION_SECRET='+secrets.token_urlsafe(48));print('KEK_KEYS='+base64.urlsafe_b64encode(secrets.token_bytes(32)).decode());print('LOG_HASH_PEPPER='+secrets.token_urlsafe(48))"

dev-backend: ## Run the API with reload on :8000
	cd backend && uv run uvicorn app.main:create_app --factory --reload --port 8000 --env-file ../.env

dev-frontend: ## Run the Angular dev server on :4200 (proxies /api to :8000)
	cd frontend && npx ng serve

sample-data: ## Rebuild .eml files and PDFs from sample_data sources
	uv run --project backend python scripts/build_sample_data.py

build: ## Production build of the frontend
	cd frontend && npx ng build

test: test-backend test-frontend ## Run unit and integration tests

test-backend:
	cd backend && uv run pytest --cov --cov-report=term-missing

test-frontend:
	cd frontend && npx ng test --watch=false

e2e: build ## Playwright E2E (starts its own API server)
	cd frontend && npx playwright test

lint: ## Lint and format-check
	cd backend && uv run ruff check . && uv run ruff format --check .
	cd frontend && npx prettier --check "src/**/*.{ts,html,css}"

typecheck: ## Static type checks
	cd backend && uv run mypy app

check: lint typecheck test e2e ## Everything CI runs locally

docker: ## Build the production image
	docker build -t officehand:dev .
