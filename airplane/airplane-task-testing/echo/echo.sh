#!/bin/sh -eu
# Linked to https://app.airplane.dev/t/echo [do not edit this line]

# Setup

PATH=$PATH:util # For running airplane locally

REPOSITORY=aws-vault-config git-clone
echo "aws-vault-config"
ls aws-vault-config

REPOSITORY=hosted-aws-management git-clone
echo "hosted-aws-management"
ls hosted-aws-management

REPOSITORY=hosted-deployments git-clone
echo "hosted-deployments"
ls hosted-deployments

REPOSITORY=staging-deployments git-clone
echo "staging-deployments"
ls staging-deployments

export $(cat-aws-consts)
echo "Customer support role: ${CUSTOMER_SUPPORT_ROLE_ARN}"