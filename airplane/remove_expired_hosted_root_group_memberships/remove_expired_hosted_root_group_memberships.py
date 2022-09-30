import os
import re
from collections import namedtuple

from pyshared.airplane_utils import AirplaneTask
from pyshared.aws_consts import get_aws_const
from pyshared.cloudformation_yaml import group_name_from_resource, get_cloudformation_export_value
from pyshared.date_utils import is_past_date, parse_date_str, get_today_str
from pyshared.git_ops import git_clone, git_add_commit_push
from pyshared.os_utils import tmp_change_dir
from pyshared.yaml_utils import load_yaml_cfg, save_yaml_cfg

REPOSITORY = "hosted-aws-management"
GROUPS_FILE_REL_PATH = "panther-hosted-root/us-west-2/panther-hosted-root-groups.yml"
CLOUDFORMATION_READ_ONLY_ROLE_ARN = get_aws_const("CLOUDFORMATION_READ_ONLY_ROLE_ARN")
TEMP_COMMENT_REGEX = "^# Temporary: .+ Expires: (20\d{2}-\d{1,2}-\d{1,2})(\\n)*$"

GroupUser = namedtuple('GroupUser', ['group', 'user'])


class HostedRootGroupMembershipRemover(AirplaneTask):

    @staticmethod
    def is_membership_expired(comment: str) -> bool:
        re_result = re.match(TEMP_COMMENT_REGEX, comment)
        if re_result:
            expiration_date = parse_date_str(re_result.group(1))
            return is_past_date(expiration_date)
        return False

    def remove_expired_users(self, data):
        removed_memberships = []

        for key, value in data['Resources'].items():
            if value['Type'] != 'AWS::IAM::UserToGroupAddition':
                continue

            # We iterate over a list copy of the members because iterating over and modifying `data` raises a
            # CollectionChanged exception. This requires us to keep up with the count of previously removed members
            # so we remove the correct entry.
            previously_removed_user_count = 0
            for index, comment in list(value['Properties']['Users'].ca.items.items()):
                if self.is_membership_expired(comment[0].value):
                    removed_memberships.append(
                        GroupUser(group=group_name_from_resource(data, value['Properties']['GroupName'].value),
                                  user=get_cloudformation_export_value(
                                      export_name=value['Properties']['Users'][index -
                                                                               previously_removed_user_count].value,
                                      role_arn=CLOUDFORMATION_READ_ONLY_ROLE_ARN)))
                    value['Properties']['Users'].pop(index - previously_removed_user_count)
                    print(f"Removing {removed_memberships[-1].user} from {removed_memberships[-1].group}")
                    previously_removed_user_count += 1
        return removed_memberships

    def main(self, params):
        repository_dir = git_clone(repo=REPOSITORY,
                                   github_setup=True,
                                   existing_dir=params.get("hosted_aws_management_dir"))

        groups_file_abs_path = os.path.join(repository_dir, GROUPS_FILE_REL_PATH)
        cfn_yaml = load_yaml_cfg(cfg_filepath=groups_file_abs_path,
                                 error_msg=f"Groups file not found: '{groups_file_abs_path}'")

        removed_memberships = self.remove_expired_users(cfn_yaml)
        if not removed_memberships:
            return

        save_yaml_cfg(groups_file_abs_path, cfn_yaml)

        commit_title = f'removes expired hosted-root group memberships {get_today_str()}'
        commit_description = ''
        for membership in removed_memberships:
            commit_description += f"{membership.user} removed from {membership.group}\n"

        with tmp_change_dir(change_dir=repository_dir):
            git_add_commit_push(files=[GROUPS_FILE_REL_PATH],
                                title=commit_title,
                                description=commit_description,
                                test_run=params["airplane_test_run"])


def main(params):
    return HostedRootGroupMembershipRemover().main(params)
