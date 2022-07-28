#!/bin/sh
set -eu

PATH=$PATH:util # For running airplane locally
. util/task-dir
cd_to_task_dir

REPOSITORY=aws-vault-config git-clone
cd aws-vault-config

pip install -e .

if [ "${PARAM_ADD_OR_REMOVE}" = "Add" ]; then
  # Only need to check account ID, as other params are required by Airplane or are lists with a default
  if [ -z "${PARAM_AWS_ACCOUNT_ID}" ]; then echo "AWS Account ID is required"; exit 1; fi

  args="--name ${PARAM_FAIRYTALE_NAME} --account-id ${PARAM_AWS_ACCOUNT_ID} --region ${PARAM_REGION} \
    --deployment-type ${PARAM_SERVICE_TYPE}"

  if [ "${PARAM_SERVICE_TYPE}" = "CPaaS" ]; then
    args="${args} --profile-types deployment support"
  fi
  aws-vault-config add-customer $(echo ${args})
else
  args="--name ${PARAM_FAIRYTALE_NAME}"
  aws-vault-config remove-customer $(echo ${args})
fi


git add aws_vault_config/aws_config.yml
TITLE="${PARAM_ADD_OR_REMOVE} ${PARAM_FAIRYTALE_NAME} profiles" git-commit
TEST_RUN="${PARAM_AIRPLANE_TEST_RUN}" git-push
