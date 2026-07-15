.PHONY: help install install-dev dev api worker frontend test lint clean migrate-configs migrate-results docker-up docker-down

# ── Default target ─────────────────────────────────────────────────────────────
help:
	@echo "Nexus Algo Terminal — available targets:"
	@echo ""
	@echo "  Setup"
	@echo "    make install         Install Python production dependencies"
	@echo "    make install-dev     Install Python dev dependencies (includes pytest)"
	@echo "    make install-fe      Install frontend Node dependencies"
	@echo ""
	@echo "  Development"
	@echo "    make dev             Start all services (api + worker + frontend) in parallel"
	@echo "    make api             Start FastAPI server only"
	@echo "    make worker          Start Celery worker only"
	@echo "    make frontend        Start Vite dev server only"
	@echo ""
	@echo "  Testing & Linting"
	@echo "    make test            Run pytest suite"
	@echo "    make lint            Run ruff linter"
	@echo ""
	@echo "  Migration"
	@echo "    make migrate-configs  Migrate algo_configs.py → algo_configs.json"
	@echo "    make migrate-results  Migrate results/CSV → nexus_results.db"
	@echo ""
	@echo "  Docker"
	@echo "    make docker-up       Start Redis + API + Celery via docker-compose"
	@echo "    make docker-down     Stop all docker-compose services"
	@echo ""
	@echo "  Cleanup"
	@echo "    make clean           Remove __pycache__, .pytest_cache, build artifacts"

# ── Setup ──────────────────────────────────────────────────────────────────────
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

install-fe:
	cd frontend && npm install

# ── Development ────────────────────────────────────────────────────────────────
dev:
	@echo "Starting Nexus services..."
	@trap 'kill 0' SIGINT; \
	  uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload & \
	  python -m celery -A backend.router.celery_app worker --loglevel=info --pool=solo & \
	  cd frontend && npm run dev; \
	  wait

api:
	uvicorn server.main:app --host 0.0.0.0 --port $${API_PORT:-8000} --reload

worker:
	python -m celery -A backend.router.celery_app worker --loglevel=info --pool=solo

frontend:
	cd frontend && npm run dev

# ── Testing ────────────────────────────────────────────────────────────────────
test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

lint:
	ruff check . --fix

# ── Migration ──────────────────────────────────────────────────────────────────
migrate-configs:
	python scripts/migrate_configs_to_json.py

migrate-results:
	python scripts/migrate_results_to_sqlite.py

# ── Docker ─────────────────────────────────────────────────────────────────────
docker-up:
	docker-compose up -d redis api worker
	@echo "Services started. API: http://localhost:8000"

docker-dev:
	docker-compose --profile dev up

docker-down:
	docker-compose down

# ── Cleanup ────────────────────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf frontend/dist
	@echo "Cleaned."
