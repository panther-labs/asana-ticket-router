import os
import re
from collections.abc import Iterable

from ruamel.yaml import comments

from pyshared.aws_consts import get_aws_const
from pyshared.cloudformation_yaml import get_group_policy_statements
from pyshared.date_utils import parse_date_str, is_past_date, get_today_str
from pyshared.git_ops import git_clone, git_add_commit_push
from pyshared.os_utils import tmp_change_dir
from pyshared.yaml_utils import load_yaml_cfg, save_yaml_cfg

REPOSITORY = "hosted-aws-management"
GROUPS_FILE_REL_PATH = "panther-hosted-root/us-west-2/panther-hosted-root-groups.yml"
CLOUDFORMATION_READ_ONLY_ROLE_ARN = get_aws_const("CLOUDFORMATION_READ_ONLY_ROLE_ARN")
CUSTOMER_COMMENT_REGEX = "^# Customer: ([a-z][a-z]*-[a-z]+)(\\n)*"
TEMP_COMMENT_REGEX = "^# Temporary: .+ Expires: (20\d{2}-\d{1,2}-\d{1,2})(\\n)*$"


def flatten_list(nd_list: list) -> list:
    if isinstance(nd_list, Iterable):
        return [item for sublist in nd_list for item in flatten_list(sublist)]
    else:
        return [nd_list]


def extract_comments(policy_statement: comments.CommentedMap) -> list:
    # Flatten comment list (due to CFN policy statement nestedness)
    comments_flattened = flatten_list(policy_statement.ca.items.values())
    # Filter out None values
    return list(filter(lambda comment: comment is not None, comments_flattened))


def is_membership_expired(comment: str) -> bool:
    re_result = re.match(TEMP_COMMENT_REGEX, comment)
    if re_result:
        expiration_date = parse_date_str(re_result.group(1))
        return is_past_date(expiration_date)
    return False


def extract_fairytale_name(comment: str) -> str or None:
    re_result = re.search(CUSTOMER_COMMENT_REGEX, comment)
    if re_result:
        return re_result.group(1)


def remove_expired_customers(cfn_yaml: comments.CommentedMap) -> list:
    policy_statements = get_group_policy_statements(cfn_yaml, "Deployment", "AssumeDeployRoles")

    removed_customers = []

    for policy_statement in policy_statements:
        is_expired = False
        fairytale_name = None
        policy_comments = extract_comments(policy_statement)
        for comment in policy_comments:
            if fairytale_name is None:
                fairytale_name = extract_fairytale_name(comment.value)
            if not is_expired:
                is_expired = is_membership_expired(comment.value)
        if is_expired:
            removed_customers.append(fairytale_name)
            policy_statements.remove(policy_statement)

    return removed_customers


def main(params: dict) -> None:
    repository_dir = git_clone(repo=REPOSITORY,
                               github_setup=True,
                               existing_dir=params.get("hosted_aws_management_dir"))

    groups_file_abs_path = os.path.join(repository_dir, GROUPS_FILE_REL_PATH)
    cfn_yaml = load_yaml_cfg(cfg_filepath=groups_file_abs_path,
                             error_msg=f"Groups file not found: '{groups_file_abs_path}'")

    removed_customers = remove_expired_customers(cfn_yaml)
    if not removed_customers:
        return

    save_yaml_cfg(groups_file_abs_path, cfn_yaml)

    commit_title = f'Remove expired customers from Deployment group {get_today_str()}'
    commit_description = ''
    for fairytale_name in removed_customers:
        commit_description += f"Remove customer '{fairytale_name}' from the Deployment group\n"

    with tmp_change_dir(change_dir=repository_dir):
        git_add_commit_push(files=[GROUPS_FILE_REL_PATH],
                            title=commit_title,
                            description=commit_description,
                            test_run=params["airplane_test_run"])
