help: ## Show the help message
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.git/hooks/pre-commit:
	@ln -s $(shell pwd)/scripts/pre-commit.githook .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo pre-commit hook installed

git: .git/hooks/pre-commit ## install the pre-commit hook

.venv:
	@poetry config virtualenvs.in-project true
	@echo installing dependencies
	@poetry install -q

test: .venv ## Run the tests
	@poetry run pytest

coverage: .venv ## Generate and show coverage reports
	@poetry run coverage run -m pytest -qq && poetry run coverage xml && coverage report -m

clean: ## Clean up
	@rm -rf .venv coverage.xml .coverage .pytest_cache .ruff_cache

run: .venv ## Runs the step specified by `step` argument
	@poetry run platform_input_support -s $(step)

.PHONY: git test help
.DEFAULT_GOAL: help
