#!/bin/bash
# Linked to https://app.airplane.dev/t/update_customer_pat_role [do not edit this line]

set -eu

export REPOSITORY="hosted-aws-management"
BRANCH="${BRANCH_OVERRIDE:-master}"
DIRECTORY_PREFIX="panther-hosted-"
IAM_ROLES_FILENAME="iam-roles.yml"

fairytale_name="${PARAM_FAIRYTALE_NAME}"
account_directory="${DIRECTORY_PREFIX}${fairytale_name}"
test_run="${PARAM_AIRPLANE_TEST_RUN}"

# Source accounts are entered into Airplane comma separated. Splits them into the array `source_accounts_and_arns`
IFS=',' read -ra source_accounts_and_arns <<< "${PARAM_SOURCE_ACCOUNTS_AND_ARNS}"

PATH=$PATH:${PWD}/util # For running airplane locally

rm -rf "${REPOSITORY}"
git-clone

cd "${REPOSITORY}"
git checkout "${BRANCH}"
printf "\nWorking in hosted deployments branch (overridable by Airplane environment variable BRANCH_OVERRIDE) '%s'\n\n" \
  $(git branch --show-current)

# TODO: in the future if no directory or file exists, have the ability to lookup region and create directory structure and file
if [ ! -d "${account_directory}" ]
then
    echo "No directory exists for ${account_directory}"
    exit 1
fi

iam_roles_file=$(find "panther-hosted-${fairytale_name}" -name "${IAM_ROLES_FILENAME}")
if [ -z "${iam_roles_file}" ]; then
  echo "No file named ${IAM_ROLES_FILENAME} exists for ${fairytale_name}"
fi

for arn in "${source_accounts_and_arns[@]}"; do
  # if only an account number is provided, change it to a full ARN. Although not required, this does follow the current pattern.
  full_arn=$(echo "${arn}" | sed -e 's|^\([0-9]\{12\}\)$|arn:aws:iam::\1:root|')
  yq e -i '.Resources.CustomerAccess.Properties.AssumeRolePolicyDocument.Statement[0].Principal.AWS += ["'"${full_arn}"'"]' "${iam_roles_file}"
done

git add "${iam_roles_file}"
TITLE="Updating PAT role(s) for '${fairytale_name}'" git-commit
TEST_RUN="${test_run}" git-push
