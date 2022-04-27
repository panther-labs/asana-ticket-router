import datetime

from dataclasses import asdict, dataclass

from pyshared.deployments_file import DeploymentsRepo, get_deployment_filepath
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
            cfg["ManualDeploy"] = str(datetime.datetime.now())

    def get_git_title(self):
        return f"Manually redeploy {self.airplane_params.fairytale_name}"


def main(params):
    ManualCustomerDeploy(params).main()


def test_manual():
    params = AirplaneParams(fairytale_name="tangible-dinosaur")
    main(asdict(params))
