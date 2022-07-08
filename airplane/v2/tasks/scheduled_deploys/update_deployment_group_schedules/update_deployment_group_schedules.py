import re

from v2.tasks.scheduled_deploys.shared import validate_deployment_version, validate_deployment_time, \
    update_group_deployment_schedule, get_deployment_time_now
from v2.consts.github_repos import GithubRepo
from v2.pyshared.os_util import tmp_change_dir
from v2.pyshared.yaml_utils import change_yaml_file
from v2.pyshared.deployments_file import get_deployment_group_filepath
from v2.pyshared.airplane_logger import logger
from v2.task_models.airplane_git_task import AirplaneGitTask


def get_group_name(param_name: str) -> str or None:
    re_result = re.match("^group_(.*)_deployment_.*$", param_name)
    if re_result:
        return re_result.group(1)


def get_deployment_group_names(params: dict) -> set:
    group_names = set()
    for key in params.keys():
        group_name = get_group_name(key)
        if group_name:
            group_names.add(group_name)
    return group_names


def get_group_deployment_time(params: dict, group_name: str) -> str:
    date_key = f"group_{group_name}_deployment_date"
    time_key = f"group_{group_name}_deployment_time"

    if date_key not in params or time_key not in params:
        raise AttributeError(f"Missing deployment date or time for deployment group '{group_name}'.")

    if params[time_key] == "now":
        params[time_key] = get_deployment_time_now()

    return f"{params[date_key]} {params[time_key]}"


def get_deployment_group_schedules(params: dict, group_names: set) -> dict:
    group_schedules = {}
    for group_name in group_names:
        deployment_time = get_group_deployment_time(params, group_name)
        validate_deployment_time(group_name, deployment_time)
        kebab_case_group_name = group_name.replace("_", "-")
        group_schedules[kebab_case_group_name] = deployment_time
    return group_schedules


class UpdateDeploymentGroupSchedules(AirplaneGitTask):

    def run(self, params: dict):
        deployment_version = params["deployment_version"]

        group_names = get_deployment_group_names(params)
        if not group_names:
            raise ValueError("No deployment group schedules found.")

        group_schedules = get_deployment_group_schedules(params, group_names)
        repo_abs_path = self.clone_repo_or_get_local(repo_name=GithubRepo.HOSTED_DEPLOYMENTS,
                                                     local_repo_abs_path=params.get("hosted_deployments_path"))

        for group, deployment_time in group_schedules.items():
            deployment_group_filepath = get_deployment_group_filepath(group, repo_path=repo_abs_path)
            with change_yaml_file(deployment_group_filepath) as cfg_yaml:
                validate_deployment_version(group, old_version=cfg_yaml["Version"], new_version=deployment_version)
                update_group_deployment_schedule(cfg_yaml, deployment_version, deployment_time)
                logger.info(f"Group '{group}' will be upgraded to '{deployment_version}' on {deployment_time}")

        with tmp_change_dir(repo_abs_path):
            self.git_add_commit_and_push(title=f'Update deployment schedules for groups {group_names}')


def main(params: dict) -> None:
    UpdateDeploymentGroupSchedules().run(params)
