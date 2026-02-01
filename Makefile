.PHONY: setup lint test

setup:
	python -m pip install -r requirements.txt

lint:
	ruff check .

test:
	python -m pytest
