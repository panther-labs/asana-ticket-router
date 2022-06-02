#!/usr/bin/env bash

# Exit script if you try to use an uninitialized variable.
set -o nounset

# Exit script if a statement returns a non-true return value.
set -o errexit

# Use the error status of the first failure, rather than that of the last item in a pipeline.
set -o pipefail

# Pulumi is installed in the pre-build step,
# but we need to export our PATH again becuase we're executing
# in a context of a new shell.
export PATH="/root/.pulumi/bin:$PATH"
pulumi version
pulumi whoami

# activate venv
source venv/bin/activate

# run pulumi commands
pulumi up --skip-preview --yes --stack $STACK_NAME --config-file Pulumi.sentry-asana.yaml