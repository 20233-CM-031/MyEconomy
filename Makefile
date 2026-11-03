.PHONY: install migrate downgrade test lint format run check

install:
	python -m pip install -e '.[dev]'

migrate:
	alembic upgrade head

downgrade:
	alembic downgrade -1

test:
	pytest -q

lint:
	ruff check src tests migrations
	ruff format --check src tests migrations

format:
	ruff check --fix src tests migrations
	ruff format src tests migrations

run:
	uvicorn myeconomy.main:app --reload

check: lint test
