#!/usr/bin/env bash

# Exit script if you try to use an uninitialized variable.
set -o nounset

# Exit script if a statement returns a non-true return value.
set -o errexit

# Use the error status of the first failure, rather than that of the last item in a pipeline.
set -o pipefail

# Used for running lint commands easily while developing and/or hooking into pipenv scripts, if thats being used
pylint sentry_asana --ignore src --disable duplicate-code,fixme,missing-module-docstring,too-few-public-methods,missing-class-docstring,missing-function-docstring,no-self-use,protected-access
pylint sentry_asana --ignore tests --disable duplicate-code,fixme,missing-module-docstring,too-few-public-methods
bandit sentry_asana --recursive --exclude tests
mypy sentry_asana --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --no-error-summary
black -S --check --diff sentry_asana

# Main Pulumi file linting
pylint ./__main__.py --disable duplicate-code,fixme,missing-module-docstring,too-few-public-methods
bandit ./__main__.py
mypy ./__main__.py --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --no-error-summary
