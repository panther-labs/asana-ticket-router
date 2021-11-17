#!/bin/sh -eu
# Linked to https://app.airplane.dev/t/echo [do not edit this line]

# Params are in environment variables as PARAM_{SLUG}, e.g. PARAM_USER_ID
echo "Hello World!"
echo "Printing env for debugging purposes:"
env

git --version

mkdir -p ~/.ssh

echo ${HOSTED_DEPLOYMENTS_BASE64} | base64 -d > ~/.ssh/id_github
chmod 600 ~/.ssh/id_github

set -x

eval `ssh-agent -s`
ssh-add ~/.ssh/id_github

ssh -T git@github.com || echo "ok"

## Real things

git clone git@github.com:panther-labs/hosted-deployments

ls

ls hosted-deployments
