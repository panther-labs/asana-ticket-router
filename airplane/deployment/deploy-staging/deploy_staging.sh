#!/bin/sh -eu
# Linked to https://app.airplane.dev/t/deploy_staging_smq [do not edit this line]

REPOSITORY=staging-deployments git-clone
cd staging-deployments
git checkout main

pip3 install -r automation-scripts/requirements.txt
printf "\n\n=== Generating changes for staging deploy ===\n"

# Find latest RC artifact
LATEST_RC=$(aws s3 ls s3://panther-enterprise-us-west-2/v | awk '{ print $2 }' | grep RC | grep -v 'RC/' | sort -V | tail -n1 | awk -F '/' '{print $1}')

PUBLISH_TIME=$(TZ=UTC aws s3 ls s3://panther-enterprise-us-west-2/${LATEST_RC}/panther.yml | | awk '{print $1"T"$2}')
if [ "${PUBLISH_TIME}" = "" ]; then
    echo "RC ${LATEST_RC} publish is not complete"
    exit 1
fi

echo "Found latest RC: ${LATEST_RC}"
export LATEST_RC

CONFIG_FILE="deployment-metadata/deployment-groups/staging.yml"

yq e -i '.Version = strenv(LATEST_RC)' "${CONFIG_FILE}"

git diff

if $(git diff --quiet deployment-metadata); then
    echo "No changes made"
    exit 0
fi

# Generate and lint
python3 automation-scripts/generate.py
python3 automation-scripts/lint.py

echo "Changes"
git diff deployment-metadata

git add deployment-metadata

echo "Staged changes"
git status

TITLE="Updating staging to '${LATEST_RC}'" git-commit
TEST_RUN=false git-push

echo "airplane_output_set {\"version\": \"${LATEST_RC}\"}"
