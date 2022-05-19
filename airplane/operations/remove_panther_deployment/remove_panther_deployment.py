# Linked to https://app.airplane.dev/t/remove_panther_deployment [do not edit this line]
import glob
import os
import yaml

from pyshared.aws_creds import get_credentialed_resource
from pyshared.ddb_hosted_deploy_retriever import DdbHostedDeployAccountInfo
from pyshared.git_ops import git_clone
from pyshared.aws_consts import get_aws_const

CUSTOMER_SUPPORT_ROLE_ARN = get_aws_const(const_name="CUSTOMER_SUPPORT_ROLE_ARN")
HOSTED_DYNAMO_REGION = get_aws_const(const_name="HOSTED_DYNAMO_RO_ROLE_REGION")
HOSTED_DYNAMO_RO_ROLE_ARN = get_aws_const(const_name="HOSTED_DYNAMO_RO_ROLE_ARN")


def get_account_info(fairytale_name):
    account_info = DdbHostedDeployAccountInfo(fairytale_name=fairytale_name,
                                              ddb_arn=HOSTED_DYNAMO_RO_ROLE_ARN,
                                              ddb_region=HOSTED_DYNAMO_REGION)

    region = account_info.get_customer_attr(attr="region")
    aws_account_id = account_info.get_customer_attr(attr="aws_account_id")

    account_support_role_arn = f"arn:aws:iam::{aws_account_id}:role/PantherSupportRole-{region}"
    arns = (CUSTOMER_SUPPORT_ROLE_ARN, account_support_role_arn)

    return region, arns


def get_stack_name(fairytale_name, hosted_deploy_dir):
    default_stack = "panther"

    deployment_file = os.path.join(hosted_deploy_dir, "deployment-metadata", "deployment-targets",
                                   f"{fairytale_name}.yml")
    if os.path.exists(deployment_file):
        with open(deployment_file, "r") as file_handler:
            cfg = yaml.safe_load(file_handler)
            return cfg.get("PantherStackName", default_stack)
    return default_stack


def delete_deploy_stacks(cfn, stack_name, test_run):
    stack = cfn.Stack(stack_name)

    if test_run:
        print(f"Test run, not deleting the '{stack.name}' stack ")
    else:
        stack.delete()
        print(f"Deleted the '{stack.name}' stack")


def remove_panther_deployment(fairytale_name, stack_name, test_run):
    region, arns = get_account_info(fairytale_name)
    cfn = get_credentialed_resource(service_name="cloudformation",
                                    arns=arns,
                                    desc=f"cfn_remove_{fairytale_name}_panther_deploy",
                                    region=region)
    delete_deploy_stacks(cfn=cfn, stack_name=stack_name, test_run=test_run)


def main(params):
    raise RuntimeError("This task is not yet ready for production use. Which role removes the stack? How does one "
                       "access that role?")
    hosted_deploy_dir = (params["hosted_deploy_dir"]
                         if "hosted_deploy_dir" in params else git_clone(repo="hosted-deployments", github_setup=True))
    remove_panther_deployment(params["fairytale_name"],
                              stack_name=get_stack_name(fairytale_name=params["fairytale_name"],
                                                        hosted_deploy_dir=hosted_deploy_dir),
                              test_run=params["airplane_test_run"])
