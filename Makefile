.PHONY: setup dev api web lint format test docker-up docker-down

setup:
	./scripts/setup.sh

dev:
	./scripts/dev.sh

api:
	cd apps/api && uvicorn orbit_api.main:app --reload --port 8000

web:
	npm run dev --workspace=@orbit/web

lint:
	./scripts/lint.sh

format:
	./scripts/format.sh

test:
	cd apps/api && pytest

docker-up:
	docker compose -f docker/docker-compose.yml up --build

docker-down:
	docker compose -f docker/docker-compose.yml down
