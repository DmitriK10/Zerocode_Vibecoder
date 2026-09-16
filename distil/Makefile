# Convenience targets. All real work is done by docker compose and pytest.
# On Windows, use Git Bash or WSL to run these, or copy the underlying commands.

.PHONY: help up down logs migrate seed test lint fmt clean

help:
	@echo "up       - build and start app + db"
	@echo "down     - stop and remove containers (keeps volume)"
	@echo "logs     - tail app logs"
	@echo "migrate  - run alembic upgrade head inside the app container"
	@echo "seed     - load tests_data/inputs.jsonl into the DB"
	@echo "test     - run pytest locally (venv)"
	@echo "lint     - run ruff"
	@echo "clean    - stop and remove containers AND volume"

up:
	docker compose up --build -d
	docker compose exec app alembic upgrade head

down:
	docker compose down

logs:
	docker compose logs -f app

migrate:
	docker compose exec app alembic upgrade head

seed:
	docker compose exec app python -m scripts.seed

test:
	python -m pytest -q

lint:
	python -m ruff check app tests

fmt:
	python -m ruff format app tests

clean:
	docker compose down -v