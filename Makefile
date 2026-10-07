.PHONY: setup dev seed stop logs check contracts sync-webfleet

setup:
	python3 scripts/bootstrap.py

dev:
	docker compose up --build -d --wait

seed:
	docker compose exec api python -m app.db.seed

stop:
	docker compose down

logs:
	docker compose logs -f --tail=100 api web

check:
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run pytest
	cd frontend && npm run lint && npm run format:check && npm run typecheck && npm test && npm run build
	python3 -m unittest discover -s scripts/github/tests

contracts:
	cd backend && uv run python scripts/export_openapi.py
	cd frontend && npm run api:generate

sync-webfleet:
	docker compose exec api python -m app.integrations.webfleet.sync
