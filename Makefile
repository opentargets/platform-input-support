help: ## Show the help message
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-9s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# git targets
.git/hooks/pre-commit:
	@ln -s $(shell pwd)/scripts/pre-commit.githook .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo pre-commit hook installed

git: .venv install .git/hooks/pre-commit ## install the pre-commit hook


# virtualenv and installation related targets
.venv:
	virtualenv .venv

.venv/installed: .venv
	@source .venv/bin/activate; pip install --no-deps -r requirements.dev.txt && pip install --no-deps ".[dev,test]"; deactivate
	@touch .venv/installed

install: .venv/installed ## Create virtual environment and install dependencies

install-dev: .venv/installed install ## Install the package in editable mode, for development inside the virtual environment
	@source .venv/bin/activate; pip install --editable .; deactivate

# test related targets
test: .venv install ## Run the tests
	@source .venv/bin/activate; pytest; deactivate

coverage: .venv install ## Generate and show coverage reports
	@source .venv/bin/activate; python -m coverage run -m pytest -qq && python -m coverage xml && python -m coverage report -m; deactivate


# run target
run: .venv ## Runs the step specified by `step` argument
	@source .venv/bin/activate; [ -n "$(step)" ] && pis -s $(step) || pis -h; deactivate


# clean up and maintenance targets
clean: ## Clean up
	@rm -rf .venv build dist platform_input_support.egg-info coverage.xml .coverage .pytest_cache .ruff_cache

.PHONY: git test help
.DEFAULT_GOAL: help
