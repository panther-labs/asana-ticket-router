import os

from ruamel.yaml import comments

from pyshared.aws_consts import get_aws_const
from pyshared.cloudformation_yaml import get_group_policy_statements
from pyshared.ddb_hosted_deploy_retriever import DdbHostedDeployAccountInfo
from pyshared.git_ops import git_clone, git_add_commit_push
from pyshared.date_utils import get_tomorrow_str
from pyshared.os_utils import tmp_change_dir
from pyshared.yaml_utils import load_yaml_cfg, save_yaml_cfg

REPOSITORY = "hosted-aws-management"
GROUPS_FILE_REL_PATH = "panther-hosted-root/us-west-2/panther-hosted-root-groups.yml"
DYNAMO_REGION = get_aws_const(const_name="HOSTED_DYNAMO_RO_ROLE_REGION")
DYNAMO_RO_ROLE_ARN = get_aws_const(const_name="HOSTED_DYNAMO_RO_ROLE_ARN")
CLOUDFORMATION_READ_ONLY_ROLE_ARN = get_aws_const("CLOUDFORMATION_READ_ONLY_ROLE_ARN")


def get_aws_account_id(fairytale_name: str) -> str:
    account_info = DdbHostedDeployAccountInfo(fairytale_name=fairytale_name,
                                              ddb_arn=DYNAMO_RO_ROLE_ARN,
                                              ddb_region=DYNAMO_REGION)
    return account_info.get_customer_attr(attr="aws_account_id")


def create_customer_policy_statement(params: dict) -> comments.CommentedMap:
    role = comments.CommentedSeq([params['role_arn']])
    role.yaml_add_eol_comment(params['comment'], 0, 0)
    role.yaml_set_comment_before_after_key(0, f"Customer: {params['fairytale_name']}", 18)
    role.yaml_set_comment_before_after_key(0, params["reason"], 18)
    return comments.CommentedMap({
        "Effect": "Allow",
        "Action": "sts:AssumeRole",
        "Resource": role
    })


def find_customer_policy_statement(policy_statements: comments.CommentedMap,
                                   aws_account_id: str) -> comments.CommentedMap or None:
    for policy_statement in policy_statements:
        for resource in policy_statement["Resource"]:
            if aws_account_id in resource:
                return policy_statement


def add_customer_to_group(cfn_yaml: comments.CommentedMap, params: dict) -> None:
    policy_statements = get_group_policy_statements(cfn_yaml, params['group_name'], params['policy_name'])

    if find_customer_policy_statement(policy_statements, params["aws_account_id"]):
        raise Exception(f"Customer '{params['fairytale_name']}' is already added to the {params['group_name']} group")

    customer_policy_statement = create_customer_policy_statement(params)
    policy_statements.append(customer_policy_statement)


def remove_customer_from_group(cfn_yaml: comments.CommentedMap, params: dict) -> None:
    policy_statements = get_group_policy_statements(cfn_yaml, params['group_name'], params['policy_name'])

    customer_policy_statement = find_customer_policy_statement(policy_statements, params["aws_account_id"])
    if not customer_policy_statement:
        raise Exception(f"Customer '{params['fairytale_name']}' not found in the {params['group_name']} group")

    policy_statements.remove(customer_policy_statement)


def main(params: dict) -> None:
    params["aws_account_id"] = get_aws_account_id(params['fairytale_name'])

    if params["add_or_remove"] == "Add" and params.get("temporary"):
        if not params.get("expires"):
            params["expires"] = get_tomorrow_str()
        params["reason"] = f'Temporary: {params["reason"]} Expires: {params["expires"]}'

    repository_dir = git_clone(repo=REPOSITORY,
                               github_setup=True,
                               existing_dir=params.get("hosted_aws_management_dir"))

    groups_file_abs_path = os.path.join(repository_dir, GROUPS_FILE_REL_PATH)
    cfn_yaml = load_yaml_cfg(cfg_filepath=groups_file_abs_path,
                             error_msg=f"Groups file not found: '{groups_file_abs_path}'")

    group = params["group"]

    if group == "Deployment":
        params["group_name"] = "Deployment"
        params["policy_name"] = "AssumeDeployRoles"
        params["role_arn"] = f"arn:aws:iam::{params['aws_account_id']}:role/PantherDeploymentRole*"
        params["comment"] = "Panther Deployment Role - Used to manage panther deployments\n\n"

    elif group == "DataAccess":
        params["group_name"] = "DataAccessGroup"
        params["policy_name"] = "AssumeDataAccessRole"
        params["role_arn"] = f"arn:aws:iam::{params['aws_account_id']}:role/PantherDataAccessRole*"
        params["comment"] = "Panther Data Access Role - Used for on-call support to Panther instances\n\n"
    else:
        raise Exception(f'Unexpected value for group: ${group}')

    operation = params["add_or_remove"]
    if operation == "Add":
        add_customer_to_group(cfn_yaml, params)
    elif operation == "Remove":
        remove_customer_from_group(cfn_yaml, params)
    else:
        raise Exception(f'Unexpected value for operation: ${operation}')

    save_yaml_cfg(groups_file_abs_path, cfn_yaml)

    with tmp_change_dir(change_dir=repository_dir):
        git_add_commit_push(files=[GROUPS_FILE_REL_PATH],
                            title=f"{operation}s {params['fairytale_name']} to/from {params['group_name']} group",
                            test_run=params["airplane_test_run"])
