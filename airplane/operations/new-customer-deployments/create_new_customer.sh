#!/bin/bash
# Linked to https://app.airplane.dev/t/add_pr_for_new_customer_skv [do not edit this line]
set -eu

PATH=$PATH:util # For running airplane locally
REPOSITORY=hosted-deployments git-clone
cd hosted-deployments
git checkout "${HOSTED_DEPLOYMENTS_BRANCH}"
printf "\nWorking in hosted deployments branch (which is an Airplane environment variable) '%s'\n\n" \
  $(git branch --show-current)

pip3 install -r automation-scripts/requirements.txt
printf "\n\n=== Generating customer files ===\n"
FAIRYTALE_NAME=$(python3 automation-scripts/create_config_from_airplane.py)
python3 automation-scripts/generate.py
python3 automation-scripts/lint.py
GEN_FILE="deployment-metadata/generated/${FAIRYTALE_NAME}.yml"
PANTHER_TEMPLATE_URL=$(yq e '.PantherTemplateURL' "${GEN_FILE}")
# shellcheck disable=SC2001
PANTHER_VERSION=$(echo "${PANTHER_TEMPLATE_URL}" | sed 's%.*s3.amazonaws.com/v\(.*\)/panther.yml%\1%')

printf "\nNew/changed files are:\n%s" "$(git status --porcelain | sed s/^...//)"
printf "\n=== Finished generating customer files ===\n\n"

git add deployment-metadata
TITLE="Creating customer '${PARAM_ACCOUNT_NAME}'" git-commit
TEST_RUN="${PARAM_AIRPLANE_TEST_RUN}" git-push

echo "airplane_output_set {\"fairytale_name\": \"${FAIRYTALE_NAME}\", \"panther_version\": \"${PANTHER_VERSION}\"}"
