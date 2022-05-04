import re
import semver

from v2.consts.github_repos import GithubRepo
from v2.pyshared.os_util import tmp_change_dir
from v2.pyshared.yaml_utils import change_yaml_file
from v2.pyshared.deployments_file import get_deployment_group_filepath
from v2.pyshared.airplane_logger import logger
from v2.pyshared.date_utils import parse_datetime_str, is_past_date
from v2.task_models.airplane_git_task import AirplaneGitTask


def extract_group_name(param_name: str) -> str or None:
    re_result = re.match("^group_(.*)_deployment_.*$", param_name)
    if re_result:
        # Do the replacement for 'legacy_sf' -> 'legacy-sf'
        return re_result.group(1).replace("_", "-")


def extract_deployment_group_names(params: dict) -> set:
    group_names = set()
    for key in params.keys():
        group_name = extract_group_name(key)
        if group_name:
            group_names.add(group_name)
    return group_names


def validate_deployment_time(datetime_str: str) -> None:
    deployment_datetime = parse_datetime_str(datetime_str)
    if is_past_date(deployment_datetime):
        raise AttributeError(f"{datetime_str} is a past date")


def extract_group_deployment_time(params: dict, group_name: str) -> str:
    date_key = f"group_{group_name}_deployment_date"
    time_key = f"group_{group_name}_deployment_time"

    if date_key not in params or time_key not in params:
        raise AttributeError(f"Missing deployment date or time for deployment group '{group_name}'.")

    deployment_time = f"{params[date_key]} {params[time_key]}"
    validate_deployment_time(deployment_time)
    return deployment_time


def get_deployment_group_schedules(params: dict, group_names: set) -> dict:
    group_schedules = {}
    for group_name in group_names:
        group_schedules[group_name] = extract_group_deployment_time(params, group_name)
    return group_schedules


def validate_version(group: str, current_version: str, new_version: str) -> None:
    # Strip v's from versions
    stripped_current_version = current_version[1:]
    stripped_new_version = new_version[1:]
    # Make sure the new version is higher than the current one
    if semver.compare(stripped_new_version, stripped_current_version) <= 0:
        raise AttributeError(
            f"Group '{group}': new version '{new_version}' is not higher than the current '{current_version}'")


class UpdateDeploymentGroupSchedules(AirplaneGitTask):

    def run(self, params: dict):
        deployment_version = params["deployment_version"]

        group_names = extract_deployment_group_names(params)
        if not group_names:
            raise ValueError("No deployment group schedules found.")

        group_schedules = get_deployment_group_schedules(params, group_names)
        repo_abs_path = self.clone_repo_or_get_local(repo_name=GithubRepo.HOSTED_DEPLOYMENTS,
                                                     local_repo_abs_path=params.get("hosted_deployments_path"))

        for group, deployment_datetime in group_schedules.items():
            deployment_group_filepath = get_deployment_group_filepath(group, repo_path=repo_abs_path)
            with change_yaml_file(deployment_group_filepath) as cfg_yaml:
                current_version = cfg_yaml["Version"]
                validate_version(group, current_version, deployment_version)
                cfg_yaml.yaml_set_start_comment(
                    f"Version: {deployment_version} Deployment Time: {deployment_datetime} (PDT)")
                logger.info(f"Group '{group}' will be upgraded to '{deployment_version}' on {deployment_datetime}")

        with tmp_change_dir(change_dir=repo_abs_path):
            self.git_add_commit_and_push(filepaths=[repo_abs_path],
                                         title=f'Update deployment schedules for groups {group_names}')


def main(params: dict) -> None:
    UpdateDeploymentGroupSchedules().run(params)
