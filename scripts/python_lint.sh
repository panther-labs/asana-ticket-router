#!/bin/sh
pylint sentry_asana_integration --ignore src --disable duplicate-code,fixme,missing-module-docstring,too-few-public-methods,missing-class-docstring,missing-function-docstring,no-self-use,protected-access
pylint sentry_asana_integration --ignore tests --disable duplicate-code,fixme,missing-module-docstring,too-few-public-methods
bandit sentry_asana_integration/src --recursive
mypy sentry_asana_integration --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --no-error-summary
