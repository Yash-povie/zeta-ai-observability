.PHONY: up down build logs ps init-db test lint

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build

logs:
	docker-compose logs -f

ps:
	docker-compose ps

init-db:
	docker-compose exec eval-worker python -m eval_worker.init_db

alembic-upgrade:
	docker-compose exec eval-worker alembic upgrade head

test:
	python -m pytest tests/ -v --tb=short

lint:
	ruff check . --fix

shell-db:
	docker-compose exec postgres psql -U admin -d zeta_telemetry

open-grafana:
	start http://localhost:3000

open-jaeger:
	start http://localhost:16686

open-prometheus:
	start http://localhost:9090