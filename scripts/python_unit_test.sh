#!/usr/bin/env bash

# Exit script if you try to use an uninitialized variable.
set -o nounset

# Exit script if a statement returns a non-true return value.
set -o errexit

# Use the error status of the first failure, rather than that of the last item in a pipeline.
set -o pipefail

PYTHONPATH=sentry_asana/src python3 -m pytest -vv --cov-report term-missing \
  --cov=sentry_asana/src/consumer \
  --cov=sentry_asana/src/producer \
  --cov=sentry_asana/src/common \
  sentry_asana/src/tests
