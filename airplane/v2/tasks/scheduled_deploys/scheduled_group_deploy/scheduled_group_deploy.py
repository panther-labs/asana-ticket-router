from v2.consts.airplane_env import AirplaneEnv
from v2.consts.deployment_groups import HostedDeploymentGroup
from v2.consts.github_repos import GithubRepo
from v2.exceptions import UnpublishedPantherVersion
from v2.pyshared.os_util import tmp_change_dir
from v2.pyshared.yaml_utils import change_yaml_file, get_top_level_comments, remove_top_level_comments
from v2.pyshared.deployments_file import get_deployment_group_filepath, generate_configs
from v2.pyshared.airplane_logger import logger
from v2.pyshared.panther_version_util import is_version_published
from v2.task_models.airplane_git_task import AirplaneGitTask
from v2.tasks.scheduled_deploys.shared import validate_deployment_version, contains_deployment_schedule, \
    parse_deployment_schedule, is_due_deployment, get_time_until_deployment


class ScheduledGroupDeploy(AirplaneGitTask):

    def __init__(self, is_dry_run: bool = False):
        """
        :param is_dry_run: Flag indicating a dry run
        """
        super().__init__(is_dry_run)
        self._deployment_summary = {}

    def _add_to_deployment_summary(self, group_name: str, version: str) -> None:
        if version not in self._deployment_summary:
            self._deployment_summary[version] = []
        self._deployment_summary[version].append(group_name)

    @property
    def _short_deployment_summary(self) -> str:
        groups_to_deploy = []
        for groups in self._deployment_summary.values():
            groups_to_deploy.extend(groups)
        return f"Upgrade group(-s) {', '.join(groups_to_deploy)}"

    @property
    def _long_deployment_summary(self) -> str:
        long_deployment_summary = ""
        for version, groups in self._deployment_summary.items():
            long_deployment_summary += f"Upgrade group(-s) {', '.join(groups)} to {version}\n"
        return long_deployment_summary

    def run(self, params: dict):
        repo_abs_path = self.clone_repo_or_get_local(repo_name=GithubRepo.HOSTED_DEPLOYMENTS,
                                                     local_repo_abs_path=params.get("hosted_deployments_path"))

        for group in HostedDeploymentGroup.get_values():
            deployment_group_filepath = get_deployment_group_filepath(group, repo_path=repo_abs_path)
            with change_yaml_file(deployment_group_filepath) as cfg_yaml:
                if contains_deployment_schedule(cfg_yaml):
                    comments = get_top_level_comments(cfg_yaml)
                    time, version = parse_deployment_schedule(comments)
                    if is_due_deployment(time):
                        validate_deployment_version(group, old_version=cfg_yaml["Version"], new_version=version)
                        if not is_version_published(version=version):
                            raise UnpublishedPantherVersion(version=version)
                        logger.info(f"Group '{group}' is due deployment - upgrading to '{version}'.")
                        cfg_yaml["Version"] = version
                        remove_top_level_comments(cfg_yaml)
                        self._add_to_deployment_summary(group, version)
                    else:
                        time_until_deployment = get_time_until_deployment(time)
                        logger.info(f"Group '{group}' is not due deployment for the next {time_until_deployment}")

        if not self._deployment_summary:
            logger.info("No groups due deployment found. Exiting without changes.")
            return

        if not AirplaneEnv.is_local_env():
            logger.info("Updating deployment targets.")
            generate_configs(repo_path=repo_abs_path)

        with tmp_change_dir(repo_abs_path):
            self.git_add_commit_and_push(title=self._short_deployment_summary,
                                         description=self._long_deployment_summary)

    def get_failure_slack_channel(self):
        return "#triage-productivity"


def main(params: dict) -> None:
    ScheduledGroupDeploy().run_notify_failures(params)
