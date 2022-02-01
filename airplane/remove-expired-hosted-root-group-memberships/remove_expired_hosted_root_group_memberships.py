# Linked to https://app.airplane.dev/t/remove_expired_hosted_root_group_memberships [do not edit this line]
from datetime import datetime
import os
import re
from pyshared.cloudformation_yaml import group_name_from_resource, get_cloudformation_export_value
from pyshared.git_ops import git_add, git_clone, git_commit, git_push
from ruamel.yaml import YAML
from collections import namedtuple

REPOSITORY = "hosted-aws-management"
GROUPS_FILE_PATH = "panther-hosted-root/us-west-2/panther-hosted-root-groups.yml"
CLOUDFORMATION_READ_ONLY_ROLE_ARN = os.environ.get(
    "CLOUDFORMATION_READ_ONLY_ROLE_ARN",
    "arn:aws:iam::255674391660:role/AirplaneCloudFormationReadOnly"
)
TEMP_COMMENT_REGEX = "^# Temporary: .+ Expires: (20\d{2}-\d{1,2}-\d{1,2})(\\n)*$"

GroupUser = namedtuple('GroupUser', ['group', 'user'])


def is_membership_expired(comment):
    re_result = re.match(TEMP_COMMENT_REGEX, comment)
    if re_result:
        expiration_date = datetime.strptime(re_result.group(1), '%Y-%m-%d')
        if expiration_date < datetime.now():
            return True
    return False


def remove_expired_users(data):
    removed_memberships = []

    for key, value in data['Resources'].items():
        if value['Type'] != 'AWS::IAM::UserToGroupAddition':
            continue

        for index, comment in list(value['Properties']['Users'].ca.items.items()):
            if is_membership_expired(comment[0].value):
                removed_memberships.append(
                    GroupUser(
                        group=group_name_from_resource(data, value['Properties']['GroupName'].value),
                        user=get_cloudformation_export_value(
                            export_name=value['Properties']['Users'][index].value,
                            role_arn=CLOUDFORMATION_READ_ONLY_ROLE_ARN
                        )
                    )
                )
                value['Properties']['Users'].pop(index)
    return removed_memberships


def main(params):
    repository_dir = (params["hosted_aws_management_dir"] if "hosted_aws_management_dir" in params
                      else git_clone(repo=REPOSITORY, github_setup=os.environ.get("DEPLOY_KEY_BASE64")))

    data_path = os.path.join(repository_dir, GROUPS_FILE_PATH)

    yaml = YAML(pure=True)
    yaml.indent(mapping=2, sequence=4, offset=2)
    with open(data_path, 'r') as file:
        cfn_yaml = yaml.load(file)

    removed_memberships = remove_expired_users(cfn_yaml)

    if not removed_memberships:
        return

    with open(data_path, 'w') as file:
        yaml.dump(cfn_yaml, file)

    commit_title = f'removes expired hosted-root group memberships {datetime.now().strftime("%Y-%m-%d")}'
    commit_description = ''
    for membership in removed_memberships:
        commit_description += f"{membership.user} removed from {membership.group}\n"

    os.chdir(repository_dir)
    git_add([GROUPS_FILE_PATH])
    git_commit(title=commit_title, description=commit_description)
    git_push(test_run=params["airplane_test_run"])
