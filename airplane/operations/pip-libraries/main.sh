#!/bin/sh -eu
# Linked to https://app.airplane.dev/t/set_piplibraries [do not edit this line]

# Params are in environment variables as PARAM_{SLUG}, e.g. PARAM_USER_ID
: "${PARAM_CUSTOMERID:?Expected CUSTOMERID param}"
: "${PARAM_PIPLIBRARIES:?Expected PIPLIBRARIES param}"

PATH=$PATH:util # For running airplane locally
REPOSITORY=hosted-deployments git-clone

echo "Customer: ${PARAM_CUSTOMERID}"

cd hosted-deployments

pip3 install -r automation-scripts/requirements.txt

CONFIG_FILE="deployment-metadata/deployment-targets/${PARAM_CUSTOMERID}.yml"

yq e -i '.CloudFormationParameters.PipLibraries = strenv(PARAM_PIPLIBRARIES)' "${CONFIG_FILE}"

if [ git diff --quiet ] ; then
    echo "No changes made"
    exit 0
fi

python3 automation-scripts/generate.py
python3 automation-scripts/lint.py

echo "Changes"
git diff

git add .

echo "Staged changes"
git status

TITLE="Updating '${PARAM_CUSTOMERID}' PipLibraries from airplane" git-commit

TEST_RUN="${PARAM_AIRPLANE_TEST_RUN}" git-push
