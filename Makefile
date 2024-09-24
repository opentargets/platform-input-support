### HOUSEKEEPING TARGETS ###
.PHONY: help clean

help: ## Show the help message
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-9s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

clean: ## Clean up
	@rm -rf .venv build dist platform_input_support.egg-info coverage.xml .coverage .pytest_cache .ruff_cache .git/hooks/pre-commit


### DEVELOPMENT TARGETS ###
.git/hooks/pre-commit:
	@ln -s $(shell pwd)/pre-commit.githook .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo pre-commit hook installed

.venv/bin/pytest: # If we have pytest, it means we have installed dev dependencies
	@uv sync --all-extras --dev --quiet
	@echo dev dependencies installed

dev: .venv/bin/pytest .git/hooks/pre-commit ## Install development dependencies and pre-commit hook

test: .install ## Run the tests
	@source .venv/bin/activate; pytest; deactivate

coverage: .install ## Generate and show coverage reports
	@source .venv/bin/activate; python -m coverage run -m pytest -qq && python -m coverage xml && python -m coverage report -m; deactivate


### MAIN TARGETS ###
run: ## Runs the step specified by `step` argument
	@[ -n "$(step)" ] && uv run pis -s $(step) || uv run pis -h
