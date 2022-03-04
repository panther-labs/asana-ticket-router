# Linked to https://app.airplane.dev/t/python_test [do not edit this line]
from pyshared.aws_secrets import get_secret_value
from pyshared.aws_consts import get_aws_const
from pyshared.git_ops import git_clone


def main(params):
    git_clone(repo="aws-vault-config", github_setup=True)
    git_clone(repo="hosted-aws-management", github_setup=False)
    git_clone(repo="hosted-deployments", github_setup=False)
    git_clone(repo="staging-deployments", github_setup=False)
    print(f"Hosted DDB ARN: {get_aws_const(const_name='HOSTED_DYNAMO_RO_ROLE_ARN')}")
    return {"value_from_airplane_test_secret": get_secret_value("airplane/testsecret")}
