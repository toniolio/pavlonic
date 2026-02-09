VENV_PY := ./.venv/bin/python
VENV_RUFF := ./.venv/bin/ruff

PY := $(shell if [ -x "$(VENV_PY)" ]; then echo "$(VENV_PY)"; else command -v python3 || command -v python; fi)
RUFF := $(shell if [ -x "$(VENV_RUFF)" ]; then echo "$(VENV_RUFF)"; else command -v ruff; fi)

.PHONY: setup lint test specs dev db-init db-migrate db-reset db-seed

setup:
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install ruff pytest fastapi uvicorn httpx sqlalchemy alembic

lint:
	$(RUFF) check .

test:
	$(PY) -m pytest

specs:
	$(PY) scripts/spec_export_stub.py

dev:
	./scripts/dev.sh

db-init:
	python -c "from apps.api.db import get_db_url, init_sqlite_file; p=get_db_url(); fp=init_sqlite_file(p); print(f'Initialized DB: {fp}')"

db-migrate:
	alembic -c apps/api/migrations/alembic.ini upgrade head

db-reset:
	python -c "from apps.api.db import get_db_url, resolve_sqlite_file_path; url=get_db_url(); path=resolve_sqlite_file_path(url); path.exists() and path.unlink()"
	$(MAKE) db-init
	$(MAKE) db-migrate

db-seed:
	$(MAKE) db-migrate
	python -c "from apps.api.seed import seed_db; seed_db()"
