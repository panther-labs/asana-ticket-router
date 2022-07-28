#!/bin/bash
# Linked to https://app.airplane.dev/t/update_customer_pat_role [do not edit this line]

set -eu
source util/task-dir
cd_to_task_dir

pip3 install cfn-lint PyYAML

export REPOSITORY="hosted-aws-management"
BRANCH="${BRANCH_OVERRIDE:-master}"
DIRECTORY_PREFIX="panther-hosted-"
IAM_ROLES_FILENAME="iam-roles.yml"
YAML_PRINCIPAL_PATH=".Resources.CustomerAccess.Properties.AssumeRolePolicyDocument.Statement[0].Principal.AWS"
fairytale_name="${PARAM_FAIRYTALE_NAME}"
account_directory="${DIRECTORY_PREFIX}${fairytale_name}"
test_run="${PARAM_AIRPLANE_TEST_RUN}"
export $(cat-aws-consts)

# Source accounts are entered into Airplane comma separated. Splits them into the array `source_accounts_and_arns`
IFS=',' read -ra source_accounts_and_arns <<< "${PARAM_SOURCE_ACCOUNTS_AND_ARNS}"

PATH=$PATH:${PWD}/util # For running airplane locally

rm -rf "${REPOSITORY}"
git-clone

cd "${REPOSITORY}"
git checkout "${BRANCH}"
printf "\nWorking in hosted deployments branch (overridable by Airplane environment variable BRANCH_OVERRIDE) '%s'\n" \
  $(git branch --show-current)

# assume the role if declared, should only run on ECS
if [ -n "${HOSTED_DYNAMO_RO_ROLE_ARN:-}" ]; then
  # https://stackoverflow.com/a/67636523
  export $(printf "AWS_ACCESS_KEY_ID=%s AWS_SECRET_ACCESS_KEY=%s AWS_SESSION_TOKEN=%s" \
    $(aws sts assume-role \
    --role-arn "${HOSTED_DYNAMO_RO_ROLE_ARN}" \
    --role-session-name Airplane \
    --query "Credentials.[AccessKeyId,SecretAccessKey,SessionToken]" \
    --output text))
fi

# Retrieve the region and AWS account ID from DynamoDB
account_info=$(aws dynamodb get-item \
    --table-name "${HOSTED_DEPLOYMENTS_METADATA}" \
    --key '{"CustomerId": {"S": "'"${fairytale_name}"'"}}')
account_region=$(echo "${account_info}" | jq -r '.Item.GithubConfiguration.M.CustomerRegion.S')
aws_account_id=$(echo "${account_info}" | jq -r '.Item.AWSConfiguration.M.AccountId.S')
if [ "${account_region}" = "None" ]; then
  printf "\nRegion not found in DynamoDB table for %s\n" "${fairytale_name}"
  exit 1
fi
if [ "${aws_account_id}" = "None" ]; then
  printf "\nAWS account ID not found in DynamoDB table for %s\n" "${fairytale_name}"
  exit 1
fi

iam_roles_file="${account_directory}/${account_region}/${IAM_ROLES_FILENAME}"
if [ ! -f "${iam_roles_file}" ]; then
  printf "\nNo file named ${IAM_ROLES_FILENAME} exists for ${fairytale_name}, copying from templates/${IAM_ROLES_FILENAME}\n"
  mkdir -p "${account_directory}/${account_region}"
  cp "templates/${IAM_ROLES_FILENAME}" "${iam_roles_file}"
fi

for arn in "${source_accounts_and_arns[@]}"; do
  # if only an account number is provided, change it to a full ARN. Although not required, this does follow the current pattern.
  full_arn=$(echo "${arn}" | sed -e 's|^\([0-9]\{12\}\)$|arn:aws:iam::\1:root|')
  printf "\nAdding ${full_arn} to PAT roles\n"
  yq e -i "${YAML_PRINCIPAL_PATH}"' += ["'"${full_arn}"'"]' "${iam_roles_file}"
done

# In the case of a new file, delete the placeholder entry "arn:aws:iam::{REPLACE_ME}:root"
# We do this last because of yq's way of adding elements to an empty array uses brackets over single hyphenated lines.
printf "\nRemoving placeholder entry from template if exists\n"
yq e -i 'del('"${YAML_PRINCIPAL_PATH}"[]' | select(. == "arn:aws:iam::{REPLACE_ME}:root"))' "${iam_roles_file}"

if ! grep -q "hosted-${fairytale_name}" account-mapping.yml; then
  echo "hosted-${fairytale_name}: \"${aws_account_id}\"" >> account-mapping.yml
  git add account-mapping.yml
fi

python3 repository-deployment-automation/generate_codepipeline.py
git add panther-hosted-root/us-west-2/codepipeline.yml

echo "Running lint. This takes a bit..."
for directory in $(find . -maxdepth 1 -type d ! -name .git  ! -name .github); do
  if ! cfn-lint "${directory}"/**/*.yml; then
    echo "Linting failed on directory \"${directory}\""
    exit 1;
  fi
done
echo "Finished running lint."

git add "${iam_roles_file}"
TITLE="Updating PAT role(s) for '${fairytale_name}'" git-commit
TEST_RUN="${test_run}" git-push
printf "\nProcess complete\n"