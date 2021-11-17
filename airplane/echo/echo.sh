#!/bin/sh -eu
# Linked to https://app.airplane.dev/t/echo [do not edit this line]

# Setup
eval `ssh-agent -s`
setup-github
REPOSITORY=hosted-deployments git-clone

ls hosted-deployments
