# Linked to https://app.airplane.dev/t/remove_panther_deployment [do not edit this line]
import os

from pyshared.aws_creds import get_credentialed_resource
from pyshared.ddb_hosted_deploy_retriever import DdbHostedDeployAccountInfo

CUSTOMER_SUPPORT_ROLE_ARN = os.environ.get("CUSTOMER_SUPPORT_ROLE_ARN")
DYNAMO_REGION = os.environ.get("DYNAMO_REGION", "us-west-2")
DYNAMO_RO_ROLE_ARN = os.environ.get("DYNAMO_RO_ROLE_ARN")


def get_account_info(fairytale_name):
    account_info = DdbHostedDeployAccountInfo(fairytale_name=fairytale_name,
                                              ddb_arn=DYNAMO_RO_ROLE_ARN,
                                              ddb_region=DYNAMO_REGION)

    region = account_info.get_customer_attr(attr="region")
    aws_account_id = account_info.get_customer_attr(attr="aws_account_id")

    account_support_role_arn = f"arn:aws:iam::{aws_account_id}:role/PantherSupportRole-{region}"
    arns = (CUSTOMER_SUPPORT_ROLE_ARN, account_support_role_arn) if CUSTOMER_SUPPORT_ROLE_ARN else None

    return region, arns


def delete_deploy_stacks(cfn, fairytale_name, test_run):
    delete_stacks = [stack for stack in cfn.stacks.all() if stack.name == "panther"]
    if not delete_stacks:
        raise RuntimeError(f"Could not find 'panther' stack to delete for {fairytale_name}")

    delete_stack_names = [stack.name for stack in delete_stacks]
    if test_run:
        print(f"Test run, not deleting the following stacks: {delete_stack_names}")
    else:
        for stack in delete_stacks:
            stack.delete()
        print(f"Deleted the following stacks: {delete_stack_names}")


def remove_panther_deployment(fairytale_name, test_run):
    region, arns = get_account_info(fairytale_name)
    cfn = get_credentialed_resource(service_name="cloudformation",
                                    arns=arns,
                                    desc=f"cfn_remove_{fairytale_name}_panther_deploy",
                                    region=region)
    delete_deploy_stacks(cfn=cfn, fairytale_name=fairytale_name, test_run=test_run)


def main(params):
    remove_panther_deployment(params["fairytale_name"], test_run=params["airplane_test_run"])
