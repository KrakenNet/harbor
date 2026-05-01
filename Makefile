.PHONY: install lint typecheck test test-all docs-build docs-serve docs-clean release publish version-bump

install:
	uv sync --group dev --group docs

lint:
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

typecheck:
	uv run pyright

test:
	uv run pytest -m unit

test-all:
	uv run pytest

docs-build:
	uv run mkdocs build --strict

docs-serve:
	uv run mkdocs serve

docs-clean:
	rm -rf site/

release:
	@./scripts/release.sh

publish:
	uv build
	uv run twine upload dist/*

version-bump:
	@./scripts/version_bump.sh
