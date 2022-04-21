import os

from pyshared.aws_creds import get_credentialed_resource, get_credentialed_client
from pyshared.aws_consts import get_aws_const
from pyshared.deployments_file import get_deployment_filepath, DeploymentsRepo
from pyshared.git_ops import git_clone
from pyshared.yaml_utils import load_yaml_cfg

DEFAULT_MASTER_STACK_NAME = "panther"
CUSTOMER_TEARDOWN_ROLE_ARN = get_aws_const(const_name="CUSTOMER_TEARDOWN_ROLE_ARN")


def get_customer_teardown_role_arns(aws_account_id: str) -> tuple[str, str]:
    return CUSTOMER_TEARDOWN_ROLE_ARN, f"arn:aws:iam::{aws_account_id}:role/PantherTeardownRole"


def get_master_stack_name(fairytale_name: str, repo_dir: str) -> str:
    deployment_file = get_deployment_filepath(fairytale_name=fairytale_name, repo_dir=repo_dir)
    try:
        cfn_yaml = load_yaml_cfg(cfg_filepath=deployment_file,
                                 error_msg=f"Customer deployment file not found: '{deployment_file}'")
        return cfn_yaml.get("PantherStackName", DEFAULT_MASTER_STACK_NAME)
    except ValueError as e:
        print(e)
        return DEFAULT_MASTER_STACK_NAME


def delete_master_stack(params: dict, stack_name: str, test_run: bool) -> None:
    cfn_kwargs = {
        "service_name": "cloudformation",
        "arns": get_customer_teardown_role_arns(params["aws_account_id"]),
        "desc": f"cfn_remove_{params['fairytale_name']}_master_stack",
        "region": params["region"]
    }
    stack = get_credentialed_resource(**cfn_kwargs).Stack(stack_name)

    if test_run:
        print(f"Test run, not deleting the '{stack.name}' stack.")
        return

    # Delete the stack
    stack.delete()
    print(f"Initiated '{stack_name}' stack deletion.")

    # The waiter will make at most 60 attempts with 60s interval in between
    waiter_cfg = {"MaxAttempts": 60, "Delay": 60}

    # Wait for status 'stack_delete_complete'
    get_credentialed_client(**cfn_kwargs) \
        .get_waiter("stack_delete_complete") \
        .wait(StackName=stack_name, WaiterConfig=waiter_cfg)

    print(f"Deleted the '{stack_name}' stack")


def main(params: dict) -> None:
    hosted_deploy_dir = git_clone(repo=DeploymentsRepo.HOSTED,
                                  github_setup=True,
                                  existing_dir=params.get("hosted_deploy_dir"))
    master_stack_name = get_master_stack_name(fairytale_name=params["fairytale_name"], repo_dir=hosted_deploy_dir)
    delete_master_stack(params=params, stack_name=master_stack_name, test_run=params["airplane_test_run"])
