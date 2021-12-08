#!/bin/sh
# Linked to https://app.airplane.dev/t/update_vault_config [do not edit this line]
set -eu

REPOSITORY=aws-vault-config git-clone
cd aws-vault-config

pip install -e .

args="--name ${PARAM_CUSTOMER_NAME} --account-id ${PARAM_ACCOUNT_ID} --region ${PARAM_AWS_REGION} \
  --deployment-type ${PARAM_DEPLOYMENT}"

if [ "${PARAM_DEPLOYMENT}" = "CPaaS" ]; then
  args="${args} --profile-types deployment support"
fi

aws-vault-config add-customer $(echo ${args})

git add aws_vault_config/aws_config.yml
TITLE="Add ${PARAM_CUSTOMER_NAME} profiles" git-commit
git-push
