from dataclasses import dataclass

from pyshared.date_utils import get_today_str
from pyshared.deployments_file import DeploymentsRepo, get_deployment_filepath, gen_cfgs
from pyshared.git_ops import AirplaneModifyGitTask
from pyshared.yaml_utils import change_yaml_file


@dataclass
class AirplaneParams:
    fairytale_name: str


class ManualCustomerDeploy(AirplaneModifyGitTask):

    def __init__(self, params):
        super().__init__(params=params, git_repo=DeploymentsRepo.HOSTED)
        self.airplane_params = AirplaneParams(**params)

    def change_files(self):
        with change_yaml_file(cfg_filepath=get_deployment_filepath(
                fairytale_name=self.airplane_params.fairytale_name)) as cfg:
            cfg["ManualDeploy"] = get_today_str()
        gen_cfgs()
        return ["."]

    def get_git_title(self):
        return f"Manually redeploy {self.airplane_params.fairytale_name}"


def main(params):
    ManualCustomerDeploy(params).main()
