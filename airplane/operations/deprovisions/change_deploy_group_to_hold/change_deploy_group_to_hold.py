from dataclasses import dataclass

from pyshared.git_ops import AirplaneModifyGitTask
from v2.pyshared.deployments_file import get_customer_deployment_filepath, get_github_repo_from_organization, \
    generate_configs
from v2.pyshared.yaml_utils import change_yaml_file


@dataclass
class AirplaneParams:
    fairytale_name: str
    organization: str


class DeployGroupHold(AirplaneModifyGitTask):

    def __init__(self, params):
        self.ap_params = AirplaneParams(**params)
        super().__init__(params=params,
                         git_repo=get_github_repo_from_organization(self.ap_params.organization),
                         requires_runbook=True)

    def get_git_title(self):
        return f"Move {self.ap_params.fairytale_name} to hold deploy group"

    def change_files(self):
        with change_yaml_file(cfg_filepath=get_customer_deployment_filepath(
                fairytale_name=self.ap_params.fairytale_name)) as cfg:
            cfg["DeploymentGroup"] = "hold"
        generate_configs()
        return "."

    def get_failure_slack_channel(self):
        return "#triage-deployment"


def main(params):
    DeployGroupHold(params).main_notify_failures(params)
