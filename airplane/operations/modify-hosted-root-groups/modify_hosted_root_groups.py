# Linked to https://app.airplane.dev/t/modify_hosted_root_groups_zav [do not edit this line]

import os

from pyshared.aws_consts import get_aws_const
from pyshared.cloudformation_yaml import get_cloudformation_export_name, get_group_membership_list
from pyshared.git_ops import git_add, git_clone, git_commit, git_push
from ruamel.yaml import YAML
from ruamel.yaml.comments import TaggedScalar

REPOSITORY = "hosted-aws-management"
GROUPS_FILE_PATH = "panther-hosted-root/us-west-2/panther-hosted-root-groups.yml"
CLOUDFORMATION_READ_ONLY_ROLE_ARN = get_aws_const("CLOUDFORMATION_READ_ONLY_ROLE_ARN")


def add_user_to_group(data, params):
    group_members = get_group_membership_list(data, params["group"])

    user_import_value = TaggedScalar(tag='!ImportValue',
                                     value=get_cloudformation_export_name(username=params["aws_username"],
                                                                          role_arn=CLOUDFORMATION_READ_ONLY_ROLE_ARN))
    group_members.append(user_import_value)

    if params["temporary"]:
        params["reason"] = f'Temporary: {params["reason"]} Expires: {params["expires"]}'
    group_members.yaml_add_eol_comment(params["reason"], len(group_members) - 1)


def remove_user_from_group(data, params):
    group = params["group"]
    username = params["aws_username"]
    cloudformation_export_name = get_cloudformation_export_name(username=username,
                                                                role_arn=CLOUDFORMATION_READ_ONLY_ROLE_ARN)

    group_members = get_group_membership_list(data, group)

    for member in group_members:
        if member.value == cloudformation_export_name:
            group_members.remove(member)
            return
    raise Exception(f'Error: user "{username}" not found in group "{group}"')


def main(params):
    if (params["add_or_remove"] == "Add") and params.get("temporary", True) and (not params.get("expires")):
        raise Exception("Expiration must be set if access is temporary")

    repository_dir = (params["hosted_aws_management_dir"]
                      if "hosted_aws_management_dir" in params else git_clone(repo=REPOSITORY, github_setup=True))

    data_path = os.path.join(repository_dir, GROUPS_FILE_PATH)

    yaml = YAML(pure=True)
    yaml.indent(mapping=2, sequence=4, offset=2)
    with open(data_path, 'r') as file:
        cfn_yaml = yaml.load(file)

    operation = params["add_or_remove"]

    if operation == "Add":
        add_user_to_group(cfn_yaml, params)
    elif operation == "Remove":
        remove_user_from_group(cfn_yaml, params)
    else:
        raise Exception(f'Unexpected value for operation: ${operation}')

    with open(data_path, 'w') as file:
        yaml.dump(cfn_yaml, file)

    os.chdir(repository_dir)
    git_add([GROUPS_FILE_PATH])
    git_commit(f"{operation}s {params['aws_username']} to/from {params['group']}")
    git_push(test_run=params["airplane_test_run"])
