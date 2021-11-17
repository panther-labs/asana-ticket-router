#!/bin/sh -eu
# Linked to https://app.airplane.dev/t/load_configuration [do not edit this line]

# Params are in environment variables as PARAM_{SLUG}, e.g. PARAM_USER_ID
: "${PARAM_CUSTOMERID:?Expected CUSTOMERID param}"

echo "Setup"
eval `ssh-agent -s`
setup-github
REPOSITORY=hosted-deployments git-clone

echo "================================"

echo "Customer: ${PARAM_CUSTOMERID}"
CONFIG=$(cat hosted-deployments/deployment-metadata/deployment-targets/${PARAM_CUSTOMERID}.yml)
JSON_CONFIG=$(echo "${CONFIG}" | yq eval -o=json -)
JSON_COMPACT_CONFIG=$(echo "${JSON_CONFIG}" | jq -c)

echo "airplane_output_set ${JSON_COMPACT_CONFIG}"
