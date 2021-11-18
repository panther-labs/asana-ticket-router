#!/bin/sh -eu
# Linked to https://app.airplane.dev/t/set_piplibraries [do not edit this line]

# Params are in environment variables as PARAM_{SLUG}, e.g. PARAM_USER_ID
: "${PARAM_CUSTOMERID:?Expected CUSTOMERID param}"
: "${PARAM_PIPLIBRARIES:?Expected PIPLIBRARIES param}"

REPOSITORY=hosted-deployments git-clone

echo "Customer: ${PARAM_CUSTOMERID}"

cd hosted-deployments

CONFIG_FILE="deployment-metadata/deployment-targets/${PARAM_CUSTOMERID}.yml"

yq e -i '.CloudFormationParameters.PipLibraries = strenv(PARAM_PIPLIBRARIES)' "${CONFIG_FILE}"

git diff

# TODO commit / push
