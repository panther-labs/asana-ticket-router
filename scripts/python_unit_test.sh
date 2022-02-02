#!/usr/bin/env bash

# Exit script if you try to use an uninitialized variable.
set -o nounset

# Exit script if a statement returns a non-true return value.
set -o errexit

# Use the error status of the first failure, rather than that of the last item in a pipeline.
set -o pipefail

# Used for running test commands easily while developing and/or hooking into pipenv scripts, if thats being used
cd sentry_asana/src

# Running legacy tests for the Consumer
python -m unittest tests/legacy_test_asana.py
python -m unittest tests/legacy_test_sentry.py

# Run new tests for the Producer (pytest)
pytest --cov-report term-missing  --cov=producer tests/
cd ../..
