# Linked to https://app.airplane.dev/t/python_test [do not edit this line]
import boto3

from pyshared.aws_secrets import get_secret_value
from pyshared.git_ops import git_clone


def main(params):
    git_clone(repo="aws-vault-config", github_setup=True)
    git_clone(repo="hosted-aws-management", github_setup=False)
    git_clone(repo="hosted-deployments", github_setup=False)
    git_clone(repo="staging-deployments", github_setup=False)
    return {"value_from_airplane_test_secret": get_secret_value("airplane/testsecret")}
