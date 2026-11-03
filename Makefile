.PHONY: install test lint format run
install:
	python -m pip install -e '.[dev]'

test:
	pytest

lint:
	ruff check src tests
	ruff format --check src tests

format:
	ruff check --fix src tests
	ruff format src tests

run:
	uvicorn myeconomy.main:app --reload
