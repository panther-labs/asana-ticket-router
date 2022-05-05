import re

from v2.consts.github_repos import GithubRepo
from v2.pyshared.os_util import tmp_change_dir
from v2.pyshared.yaml_utils import change_yaml_file
from v2.pyshared.deployments_file import get_deployment_group_filepath
from v2.pyshared.airplane_logger import logger
from v2.task_models.airplane_git_task import AirplaneGitTask


def extract_group_name(param_name: str) -> str or None:
    re_result = re.match("^group_(.*)$", param_name)
    if re_result:
        # Do the replacement for 'legacy_sf' -> 'legacy-sf'
        return re_result.group(1).replace("_", "-")


def extract_group_deployments_to_cancel(params: dict) -> set:
    groups_to_cancel = set()
    cancel_all_groups = params["all_groups"]
    for key, cancel_group in params.items():
        group_name = extract_group_name(key)
        if group_name:
            if cancel_group or cancel_all_groups:
                groups_to_cancel.add(group_name)
    return groups_to_cancel


class CancelDeploymentGroupSchedules(AirplaneGitTask):

    def run(self, params: dict):
        repo_abs_path = self.clone_repo_or_get_local(repo_name=GithubRepo.HOSTED_DEPLOYMENTS,
                                                     local_repo_abs_path=params.get("hosted_deployments_path"))

        groups_to_cancel = extract_group_deployments_to_cancel(params)
        logger.info(f"Deployment schedules will be canceled for the following groups: {groups_to_cancel}")
        for group in groups_to_cancel:
            deployment_group_filepath = get_deployment_group_filepath(group, repo_path=repo_abs_path)
            with change_yaml_file(deployment_group_filepath) as cfg_yaml:
                # Remove top level comment
                cfg_yaml.ca.comment = None

        with tmp_change_dir(repo_abs_path):
            self.git_add_commit_and_push(title=f'Cancel deployment schedules for groups {groups_to_cancel}')


def main(params: dict) -> None:
    CancelDeploymentGroupSchedules().run(params)
