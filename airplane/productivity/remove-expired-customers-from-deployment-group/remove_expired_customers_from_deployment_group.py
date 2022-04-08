# Linked to https://app.airplane.dev/t/remove_expired_customers_from_deployment_group [do not edit this line]
import os
import re
from datetime import datetime
from collections.abc import Iterable

from ruamel.yaml import YAML, comments

from pyshared.aws_consts import get_aws_const
from pyshared.cloudformation_yaml import get_group_policy_statements
from pyshared.git_ops import git_add, git_clone, git_commit, git_push

REPOSITORY = "hosted-aws-management"
GROUPS_FILE_PATH = "panther-hosted-root/us-west-2/panther-hosted-root-groups.yml"
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
        expiration_date = datetime.strptime(re_result.group(1), '%Y-%m-%d')
        return expiration_date < datetime.now()
    return False


def extract_fairytale_name(comment: str) -> str or None:
    re_result = re.search(CUSTOMER_COMMENT_REGEX, comment)
    if re_result:
        return re_result.group(1)


def remove_expired_customers(cfn_yaml: comments.CommentedMap) -> list:
    policy_statements = get_group_policy_statements(cfn_yaml, "Deployment", "AssumeDeployRoles")

    if len(policy_statements) <= 1:
        raise Exception("Unable to remove customer. This would leave the policy document empty.")

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


def main(params):
    repository_dir = (params["hosted_aws_management_dir"]
                      if "hosted_aws_management_dir" in params else git_clone(repo=REPOSITORY, github_setup=True))

    data_path = os.path.join(repository_dir, GROUPS_FILE_PATH)

    yaml = YAML(pure=True)
    yaml.indent(mapping=2, sequence=4, offset=2)
    with open(data_path, 'r') as file:
        cfn_yaml = yaml.load(file)

    removed_customers = remove_expired_customers(cfn_yaml)

    if not removed_customers:
        return

    with open(data_path, 'w') as file:
        yaml.dump(cfn_yaml, file)

    commit_title = f'Remove expired customers from Deployment group {datetime.now().strftime("%Y-%m-%d")}'
    commit_description = ''
    for fairytale_name in removed_customers:
        commit_description += f"Remove customer '{fairytale_name}' from the Deployment group\n"

    os.chdir(repository_dir)
    git_add([GROUPS_FILE_PATH])
    git_commit(title=commit_title, description=commit_description)
    git_push(test_run=params["airplane_test_run"])
