#!/bin/sh
# Used for running lint commands easily while developing and/or hooking into pipenv scripts, if thats being used
pylint sentry_asana_integration --ignore src --disable duplicate-code,fixme,missing-module-docstring,too-few-public-methods,missing-class-docstring,missing-function-docstring,no-self-use,protected-access
pylint sentry_asana_integration --ignore tests --disable duplicate-code,fixme,missing-module-docstring,too-few-public-methods
bandit sentry_asana_integration --recursive --exclude tests
mypy sentry_asana_integration --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --no-error-summary
# Main Pulumi file linting
pylint ./__main__.py --disable duplicate-code,fixme,missing-module-docstring,too-few-public-methods
bandit ./__main__.py
mypy ./__main__.py --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --no-error-summary
