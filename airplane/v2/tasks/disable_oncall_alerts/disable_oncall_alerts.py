import ruamel.yaml

from v2.consts.airplane_env import AirplaneEnv
from v2.pyshared.os_util import tmp_change_dir
from v2.pyshared.deployments_file import generate_configs, get_customer_deployment_filepath, \
    get_github_repo_from_organization
from v2.pyshared.airplane_logger import logger
from v2.pyshared.yaml_utils import change_yaml_file
from v2.task_models.airplane_git_task import AirplaneGitTask


class DisableOncallAlerts(AirplaneGitTask):

    def run(self, params: dict):
        fairytale_name = params['fairytale_name']
        repo_name = get_github_repo_from_organization(params["organization"])
        repo_abs_path = self.clone_repo_or_get_local(
            repo_name=repo_name, local_repo_abs_path=params.get(f"{repo_name.replace('-', '_')}_path"))
        logger.info(f"Disabling Datadog and Sentry for '{fairytale_name}'")

        with change_yaml_file(cfg_filepath=get_customer_deployment_filepath(fairytale_name=fairytale_name,
                                                                            repo_path=repo_abs_path)) as yaml_cfg:
            yaml_cfg.setdefault("CloudFormationParameters", {}).update({
                "DatadogEnabled": False,
                "DatadogAWSEnabled": False,
                "SentryEnabled": False,
            })

        if not AirplaneEnv.is_local_env():
            logger.info("Updating deployment targets.")
            generate_configs(repo_path=repo_abs_path)

        with tmp_change_dir(repo_abs_path):
            self.git_add_commit_and_push(title=f"Disable Datadog and Sentry for '{fairytale_name}'")


def main(params: dict) -> None:
    DisableOncallAlerts(requires_parent_execution=True).run(params)
