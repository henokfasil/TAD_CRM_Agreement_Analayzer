.PHONY: setup dev test lint format migrate seed worker scheduler streamlit

setup:
	uv sync --extra dev

dev:
	uv run uvicorn app.main:app --reload

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run black .
	uv run ruff check . --fix

migrate:
	uv run alembic upgrade head

seed:
	uv run python scripts/seed_codebook.py

worker:
	@echo "Worker is planned for a later phase."

scheduler:
	@echo "Scheduler is planned for a later phase."

streamlit:
	uv run streamlit run streamlit_app/Home.py

