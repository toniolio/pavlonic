VENV_PY := ./.venv/bin/python
VENV_RUFF := ./.venv/bin/ruff

PY := $(shell if [ -x "$(VENV_PY)" ]; then echo "$(VENV_PY)"; else command -v python3 || command -v python; fi)
RUFF := $(shell if [ -x "$(VENV_RUFF)" ]; then echo "$(VENV_RUFF)"; else command -v ruff; fi)

.PHONY: setup lint test specs dev db-init

setup:
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install ruff pytest fastapi uvicorn httpx

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
