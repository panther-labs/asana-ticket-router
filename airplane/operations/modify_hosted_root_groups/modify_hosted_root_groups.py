import os

from ruamel.yaml import comments

from pyshared.aws_consts import get_aws_const
from pyshared.cloudformation_yaml import get_cloudformation_export_name, get_group_membership_list
from pyshared.date_utils import get_tomorrow_str
from pyshared.git_ops import git_clone, git_add_commit_push
from pyshared.os_utils import tmp_change_dir
from pyshared.yaml_utils import load_yaml_cfg, save_yaml_cfg

REPOSITORY = "hosted-aws-management"
GROUPS_FILE_REL_PATH = "panther-hosted-root/us-west-2/panther-hosted-root-groups.yml"
CLOUDFORMATION_READ_ONLY_ROLE_ARN = get_aws_const("CLOUDFORMATION_READ_ONLY_ROLE_ARN")


def find_user_in_group(group_members: comments.CommentedMap, cfn_export_name: str) -> comments.TaggedScalar or None:
    for member in group_members:
        if member.value == cfn_export_name:
            return member


def add_user_to_group(cfn: comments.CommentedMap, params: dict) -> bool:
    group_members = get_group_membership_list(cfn, params["group"])
    cfn_export_name = get_cloudformation_export_name(username=params["aws_username"],
                                                     role_arn=CLOUDFORMATION_READ_ONLY_ROLE_ARN)

    if find_user_in_group(group_members, cfn_export_name):
        print(f"Warning: user '{params['aws_username']}' is already a part of '{params['group']}' group.")
        return False

    user_import_value = comments.TaggedScalar(tag='!ImportValue', value=cfn_export_name)
    group_members.insert(0, user_import_value)
    group_members.yaml_add_eol_comment(params["reason"], 0)
    return True


def remove_user_from_group(cfn: comments.CommentedMap, params: dict) -> bool:
    group_members = get_group_membership_list(cfn, params["group"])
    cfn_export_name = get_cloudformation_export_name(username=params["aws_username"],
                                                     role_arn=CLOUDFORMATION_READ_ONLY_ROLE_ARN)

    member = find_user_in_group(group_members, cfn_export_name)
    if not member:
        print(f"Warning: user '{params['aws_username']}' not found in group '{params['group']}'")
        return False

    group_members.remove(member)
    return True


def main(params: dict) -> None:
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

    operation = params["add_or_remove"]
    if operation == "Add":
        is_group_modified = add_user_to_group(cfn_yaml, params)
    elif operation == "Remove":
        is_group_modified = remove_user_from_group(cfn_yaml, params)
    else:
        raise Exception(f'Unexpected value for operation: ${operation}')

    if not is_group_modified:
        print("Exiting without modifying group membership.")
        return

    save_yaml_cfg(groups_file_abs_path, cfn_yaml)

    with tmp_change_dir(change_dir=repository_dir):
        git_add_commit_push(files=[GROUPS_FILE_REL_PATH],
                            title=f"{operation}s {params['aws_username']} to/from {params['group']}",
                            test_run=params["airplane_test_run"])
