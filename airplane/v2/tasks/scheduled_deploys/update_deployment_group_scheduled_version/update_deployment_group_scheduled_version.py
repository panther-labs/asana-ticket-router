import re

from v2.tasks.scheduled_deploys.shared import validate_deployment_version, update_group_deployment_schedule, \
    parse_deployment_schedule
from v2.consts.github_repos import GithubRepo
from v2.pyshared.os_util import tmp_change_dir
from v2.pyshared.yaml_utils import change_yaml_file, get_top_level_comments
from v2.pyshared.deployments_file import get_deployment_group_filepath
from v2.pyshared.airplane_logger import logger
from v2.task_models.airplane_git_task import AirplaneGitTask


def get_group_name(param_name: str) -> str or None:
    re_result = re.match("^group_(.*)$", param_name)
    if re_result:
        # Do the replacement for 'legacy_sf' -> 'legacy-sf'
        return re_result.group(1).replace("_", "-")


def get_group_deployments_to_update(params: dict) -> set:
    groups_to_cancel = set()
    cancel_all_groups = params["all_groups"]
    for key, cancel_group in params.items():
        group_name = get_group_name(key)
        if group_name:
            if cancel_group or cancel_all_groups:
                groups_to_cancel.add(group_name)
    return groups_to_cancel


class UpdateDeploymentGroupScheduledVersion(AirplaneGitTask):

    def run(self, params: dict):
        repo_abs_path = self.clone_repo_or_get_local(repo_name=GithubRepo.HOSTED_DEPLOYMENTS,
                                                     local_repo_abs_path=params.get("hosted_deployments_path"))

        updated_groups = []
        groups_to_update = get_group_deployments_to_update(params)
        for group in groups_to_update:
            deployment_group_filepath = get_deployment_group_filepath(group, repo_path=repo_abs_path)
            with change_yaml_file(deployment_group_filepath) as cfg_yaml:
                top_level_comments = get_top_level_comments(cfg_yaml)
                if top_level_comments:
                    new_version = params["deployment_version"]
                    deployment_time, old_version = parse_deployment_schedule(top_level_comments)
                    validate_deployment_version(group, old_version=old_version, new_version=new_version)
                    logger.info(f"Group '{group}': updating deployment version from '{old_version}' to '{new_version}'")
                    update_group_deployment_schedule(cfg_yaml, new_version, deployment_time)
                    updated_groups.append(group)
                else:
                    logger.info(f"Group {group}: no deployment schedule found.")

        if not updated_groups:
            raise ValueError(f"No deployment schedules were found for the requested groups. No changes will be made.")

        with tmp_change_dir(repo_abs_path):
            self.git_add_commit_and_push(title=f'Update deployment schedules for groups {updated_groups}')


def main(params: dict) -> None:
    UpdateDeploymentGroupScheduledVersion().run(params)
