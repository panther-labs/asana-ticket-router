# Linked to https://app.airplane.dev/t/add_remove_customer_to_from_deployment_group [do not edit this line]

import datetime
import os

from ruamel.yaml import YAML, comments

from pyshared.aws_consts import get_aws_const
from pyshared.cloudformation_yaml import get_group_policy_statements
from pyshared.ddb_hosted_deploy_retriever import DdbHostedDeployAccountInfo
from pyshared.git_ops import git_clone, git_add, git_commit, git_push

REPOSITORY = "hosted-aws-management"
GROUPS_FILE_PATH = "panther-hosted-root/us-west-2/panther-hosted-root-groups.yml"
DYNAMO_REGION = get_aws_const(const_name="HOSTED_DYNAMO_RO_ROLE_REGION")
DYNAMO_RO_ROLE_ARN = get_aws_const(const_name="HOSTED_DYNAMO_RO_ROLE_ARN")
CLOUDFORMATION_READ_ONLY_ROLE_ARN = get_aws_const("CLOUDFORMATION_READ_ONLY_ROLE_ARN")


def get_aws_account_id(fairytale_name: str) -> str:
    account_info = DdbHostedDeployAccountInfo(fairytale_name=fairytale_name,
                                              ddb_arn=DYNAMO_RO_ROLE_ARN,
                                              ddb_region=DYNAMO_REGION)
    return account_info.get_customer_attr(attr="aws_account_id")


def create_customer_policy_statement(params: dict) -> comments.CommentedMap:
    deployment_role = comments.CommentedSeq([f"arn:aws:iam::{params['account_id']}:role/PantherDeploymentRole*"])
    deployment_role.yaml_add_eol_comment("Panther Deployment Role - Used to manage panther deployments\n\n", 0, 0)
    deployment_role.yaml_set_comment_before_after_key(0, f"Customer: {params['fairytale_name']}", 18)
    deployment_role.yaml_set_comment_before_after_key(0, params["reason"], 18)
    return comments.CommentedMap({
        "Effect": "Allow",
        "Action": "sts:AssumeRole",
        "Resource": deployment_role
    })


def add_customer_to_deployment_group(cfn_yaml: comments.CommentedMap, params: dict) -> None:
    customer_policy_statement = create_customer_policy_statement(params)
    policy_statements = get_group_policy_statements(cfn_yaml, "Deployment", "AssumeDeployRoles")
    policy_statements.append(customer_policy_statement)


def remove_customer_from_deployment_group(cfn_yaml: comments.CommentedMap, params: dict) -> None:
    policy_statements = get_group_policy_statements(cfn_yaml, "Deployment", "AssumeDeployRoles")

    if len(policy_statements) <= 1:
        raise Exception("Unable to remove customer. This would leave the policy document empty.")

    for policy_statement in policy_statements:
        for resource in policy_statement["Resource"]:
            if params["account_id"] in resource:
                policy_statements.remove(policy_statement)
                return
    raise Exception(f"Customer '{params['fairytale_name']}' not found in the deployment group")


def main(params: dict) -> None:
    params["account_id"] = get_aws_account_id(params['fairytale_name'])

    if params["add_or_remove"] == "Add" and params.get("temporary", True):
        if not params.get("expires"):
            params["expires"] = datetime.date.today() + datetime.timedelta(days=1)  # default to tomorrow
        params["reason"] = f'Temporary: {params["reason"]} Expires: {params["expires"]}'

    repository_dir = (params["hosted_aws_management_dir"]
                      if "hosted_aws_management_dir" in params else git_clone(repo=REPOSITORY, github_setup=True))

    data_path = os.path.join(repository_dir, GROUPS_FILE_PATH)

    yaml = YAML(pure=True)
    yaml.indent(mapping=2, sequence=4, offset=2)
    with open(data_path, 'r') as file:
        cfn_yaml = yaml.load(file)

    operation = params["add_or_remove"]

    if operation == "Add":
        add_customer_to_deployment_group(cfn_yaml, params)
    elif operation == "Remove":
        remove_customer_from_deployment_group(cfn_yaml, params)
    else:
        raise Exception(f'Unexpected value for operation: ${operation}')

    with open(data_path, 'w') as file:
        yaml.dump(cfn_yaml, file)

    os.chdir(repository_dir)
    git_add([GROUPS_FILE_PATH])
    git_commit(f"{operation}s {params['fairytale_name']} to/from deployment group")
    git_push(test_run=params["airplane_test_run"])
