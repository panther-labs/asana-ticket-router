from dataclasses import dataclass

from pyshared.git_ops import AirplaneModifyGitTask
from v2.pyshared.deployments_file import get_github_repo_from_organization, manually_deploy_customer


@dataclass
class AirplaneParams:
    fairytale_name: str
    organization: str


class ManualCustomerDeploy(AirplaneModifyGitTask):

    def __init__(self, params):
        self.ap_params = AirplaneParams(**params)
        super().__init__(params=params, git_repo=get_github_repo_from_organization(self.ap_params.organization))

    def change_files(self):
        manually_deploy_customer(fairytale_name=self.ap_params.fairytale_name)
        return ["."]

    def get_git_title(self):
        return f"Manually redeploy {self.ap_params.fairytale_name}"


def main(params):
    ManualCustomerDeploy(params).main()
