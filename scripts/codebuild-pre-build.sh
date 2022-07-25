#!/usr/bin/env bash

# Exit script if you try to use an uninitialized variable.
set -o nounset

# Exit script if a statement returns a non-true return value.
set -o errexit

# Use the error status of the first failure, rather than that of the last item in a pipeline.
set -o pipefail

# install pulumi-cli
curl -fsSL https://get.pulumi.com | sh -s -- --version 3.35.2
export PATH="/root/.pulumi/bin:$PATH"
pulumi version
pulumi whoami

# init our venv
python -m venv venv
# activate venv
source venv/bin/activate
# install base python deps
pip install pulumi==3.35.2 pulumi-aws==5.9.2

# run pulumi commands
pulumi stack init --stack $STACK_NAME || echo "stack already exists"
