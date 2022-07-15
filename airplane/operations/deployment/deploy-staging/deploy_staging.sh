#!/bin/sh -eu
# Linked to https://app.airplane.dev/t/deploy_staging_smq [do not edit this line]

check_if_published() {
    VERSION_STR="${1}"
    VERSION_TYPE="${2}"

    PUBLISH_TIME=$(TZ=UTC aws s3 ls s3://panther-enterprise-us-west-2/${VERSION_STR}/panther.yml | awk '{print $1"T"$2}')
    if [ "${PUBLISH_TIME}" = "" ]; then
        echo "${VERSION_TYPE} ${VERSION_STR} publish is not complete"
        exit 1
    fi

    echo "Found latest ${VERSION_TYPE}: ${VERSION_STR}"
}

# https://jonlabelle.com/snippets/view/shell/compare-semver-versions-in-bash
is_greater_version() { test "$(echo "$@" | tr " " "\n" | sort -V | head -n 1)" != "$1"; }

get_latest_version() {
  LATEST_RC="${1}"
  LATEST_GA="${2}"

  # Trim latest RC to Major.Minor.Patch only
  LATEST_RC_TRIMMED=$(echo "${LATEST_RC}" | cut -d "-" -f1)

  # With latest RC trimmed, we can compare versions using 'sort -V'
  if is_greater_version "${LATEST_RC_TRIMMED}" "${LATEST_GA}"; then
    echo "${LATEST_RC}"
  else
    echo "Using latest GA version (${LATEST_GA}) for latest RC version (${LATEST_RC})">&2
    echo "${LATEST_GA}"
  fi
}

# Find latest artifacts
LATEST_RC=$(aws s3 ls s3://panther-enterprise-us-west-2/v | awk '{ print $2 }' | grep RC | grep -v 'RC/' | sort -V | tail -n1 | awk -F '/' '{print $1}')
LATEST_GA=$(aws s3 ls s3://panther-enterprise-us-west-2/v | awk '{ print $2 }' | grep '[0-9]\+\.[0-9]\+\.[0-9]\+/' | sort -V | tail -n1 | awk -F '/' '{print $1}')

check_if_published "${LATEST_RC}" "RC"
check_if_published "${LATEST_GA}" "GA"

# If the latest GA is higher (newer) than the latest RC, use it, otherwise, keep RC as is
LATEST_RC=$(get_latest_version "${LATEST_RC}" "${LATEST_GA}")

update_version_in_repo() {
    REPO_NAME="${1}"
    DEFAULT_BRANCH="${2}"
    CONFIG_FILE="${3}"
    VERSION="${4}"
    COMMIT_MSG="${5}"

    printf "\n\n=== Generating changes for ${REPO_NAME} ===\n"

    if [ ! -d "${REPO_NAME}" ]; then
        REPOSITORY="${REPO_NAME}" git-clone
    fi

    (
        cd "${REPO_NAME}"
        echo "$(pwd)"
        git checkout "${DEFAULT_BRANCH}"
        echo "pip3 install --quiet -r automation-scripts/requirements.txt"
        pip3 install --quiet -r automation-scripts/requirements.txt

        export VERSION
        yq e -i '.Version = strenv(VERSION)' "${CONFIG_FILE}"

        if $(git diff --quiet deployment-metadata); then
            echo "No changes made"
            exit 0
        fi

        # Generate and lint
        python3 automation-scripts/generate.py
        python3 automation-scripts/lint.py

        #echo "Changes"
        git diff deployment-metadata
        git add deployment-metadata

        echo "Staged changes"
        git status

        TITLE="${COMMIT_MSG}" git-commit
        TEST_RUN=false git-push
    )
}


## staging-deployment
(
    CONFIG_FILE="deployment-metadata/deployment-groups/staging.yml"
    MSG="Updating staging to '${LATEST_RC}'"
    update_version_in_repo "staging-deployments" "main" "${CONFIG_FILE}" "${LATEST_RC}" "${MSG}"
)

## staging-deployment GA
{
    CONFIG_FILE="deployment-metadata/deployment-groups/ga.yml"
    MSG="Updating staging GA to '${LATEST_GA}'"
    update_version_in_repo "staging-deployments" "main" "${CONFIG_FILE}" "${LATEST_GA}" "${MSG}"
}

## hosted-deployment internal
(
    CONFIG_FILE="deployment-metadata/deployment-groups/internal.yml"
    MSG="Updating internal group to '${LATEST_RC}'"
    update_version_in_repo "hosted-deployments" "master" "${CONFIG_FILE}" "${LATEST_RC}" "${MSG}"
)

## hosted-deployment alpha
(
    CONFIG_FILE="deployment-metadata/deployment-groups/alpha.yml"
    MSG="Updating alpha group to '${LATEST_GA}'"
    update_version_in_repo "hosted-deployments" "master" "${CONFIG_FILE}" "${LATEST_GA}" "${MSG}"
)

## hosted-deployment latest-ga-fridays
export TZ=America/Los_Angeles
FRIDAY=5
current_day=$(date +%u)
current_hour=$(date +%H)

# Friday afternoon for a time that works for most people in PT to ET timezones in case it needs to be debugged
if [ "${current_day}" = "${FRIDAY}" ] && [ "${current_hour}" -gt "11" ] && [ "${current_hour}" -lt "14" ]; then
(
    CONFIG_FILE="deployment-metadata/deployment-groups/latest-ga-fridays.yml"
    MSG="Updating latest-ga-fridays group to '${LATEST_GA}'"
    update_version_in_repo "hosted-deployments" "master" "${CONFIG_FILE}" "${LATEST_GA}" "${MSG}"
)
fi

## Airplane output
echo "airplane_output_set {\"rc_version\": \"${LATEST_RC}\", \"ga_version\": \"${LATEST_GA}\"}"
