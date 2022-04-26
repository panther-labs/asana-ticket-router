#!/bin/bash
# Linked to https://app.airplane.dev/t/invite_new_user_to_panther [do not edit this line]

set -eu

PATH=$PATH:${PWD}/util # For running airplane locally

fairytale_name="${PARAM_FAIRYTALE_NAME}"
email_address="${PARAM_EMAIL_ADDRESS}"
first_name="${PARAM_FIRST_NAME}"
last_name="${PARAM_LAST_NAME}"
resend_invitation="${PARAM_RESEND_INVITATION}"
test_run="${PARAM_AIRPLANE_TEST_RUN}"
user_role="${PARAM_ROLE}"
export $(cat-aws-consts)

# Retrieve deployment metadata
deployment_metadata=$(ddb-get-deployment-metadata -f "${fairytale_name}" -p "Item")

deployment_metadata_value () {
  retval=$(printf '%s\n' "${deployment_metadata}" | jq -r "${1}")
  if [ "${retval}" = "null" ]; then
    printf "\nValue lookup failed for %s\n" "${1}"
    exit 1
  fi
  printf "${retval}"
}

# Lookup version number for fairytale_name
current_version=$(deployment_metadata_value '.PantherTemplateURL.S' | awk 'BEGIN { FS = "/" } ; { print $4 }')
printf "\n${fairytale_name}'s current version is ${current_version}\n"

# Lookup the number from DynamoDB
account_id=$(deployment_metadata_value '.AWSConfiguration.M.AccountId.S')

# Lookup the region from DynamoDB
account_region=$(deployment_metadata_value '.GithubConfiguration.M.CustomerRegion.S')

# Download utils for the current version
tools_dir="tools"
tools_archive_file="${tools_dir}/tools.zip"
download-panther-tools -v "${current_version}" -o "${tools_archive_file}"

# reads the binary filename into a variable
opslambda_file="${tools_dir}/$(unzip -Z1 ${tools_archive_file})"
unzip -o -d "${tools_dir}" "${tools_archive_file}"
rm -rf "${tools_archive_file}"

# Assume the role for the hosted-root with CustomerSupport role.
export $(printf "AWS_ACCESS_KEY_ID=%s AWS_SECRET_ACCESS_KEY=%s AWS_SESSION_TOKEN=%s" \
  $(aws sts assume-role \
  --role-arn "${CUSTOMER_SUPPORT_ROLE_ARN}" \
  --role-session-name Airplane \
  --query "Credentials.[AccessKeyId,SecretAccessKey,SessionToken]" \
  --output text))

# Assume the role for the fairytale_name with Invoke lambda permissions
export $(printf "AWS_ACCESS_KEY_ID=%s AWS_SECRET_ACCESS_KEY=%s AWS_SESSION_TOKEN=%s" \
  $(aws sts assume-role \
  --role-arn "arn:aws:iam::${account_id}:role/PantherSupportRole-${account_region}" \
  --role-session-name Airplane \
  --query "Credentials.[AccessKeyId,SecretAccessKey,SessionToken]" \
  --output text))

# Send invite using the tools
if [ "${test_run}" = "true" ]; then
  printf "\n\n=== This is a test run! ===\n"
  aws --region "${account_region}" lambda list-functions | jq .Functions[].FunctionName
else
  resend=''
  if [ "${resend_invitation}" = "true" ]; then
    resend='-resend'
  fi
  "${opslambda_file}" invite \
    -email "${email_address}" \
    -first "${first_name}" \
    -last "${last_name}" \
    -role "${user_role}" \
    "${resend}"
fi