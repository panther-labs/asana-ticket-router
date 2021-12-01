#!/bin/bash
# Linked to https://app.airplane.dev/t/add_pr_for_new_customer_skv [do not edit this line]
set -eu

REPOSITORY=hosted-deployments git-clone
cd hosted-deployments
git checkout "${HOSTED_DEPLOYMENTS_BRANCH}"
printf "\nWorking in hosted deployments branch (which is an Airplane environment variable) '%s'\n\n" \
  $(git branch --show-current)

pip3 install -r automation-scripts/requirements.txt
printf "\n\n=== Generating customer files ===\n"
python3 automation-scripts/create_config_from_airplane.py
python3 automation-scripts/lint.py
python3 automation-scripts/generate.py
printf "\nNew/changed files are:\n%s" "$(git status --porcelain | sed s/^...//)"
printf "\n=== Finished generating customer files ===\n\n"

git add deployment-metadata
TITLE="Creating customer '${PARAM_CUSTOMER_NAME}'" git-commit
git push


FAIRYTALE_NAME=$(yq e '.CustomerId' deployments/deployment-metadata/deployment-targets/${PARAM_CUSTOMER_NAME}.yml)
echo "airplane_output_set:fairytale_name ${FAIRYTALE_NAME}"
