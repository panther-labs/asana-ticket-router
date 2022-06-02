#!/usr/bin/env bash

# Exit script if you try to use an uninitialized variable.
set -o nounset

# Exit script if a statement returns a non-true return value.
set -o errexit

# Use the error status of the first failure, rather than that of the last item in a pipeline.
set -o pipefail

# install pulumi
curl -fsSL https://get.pulumi.com | sh -s -- --version 3.33.2

# install base deps
source venv/bin/activate
pip install pulumi==3.28.0 pulumi-aws==5.1.2
