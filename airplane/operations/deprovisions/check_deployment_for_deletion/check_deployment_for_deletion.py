from dataclasses import asdict, dataclass
from datetime import datetime

from operations.deprovisions import DEPROV_TZ
from pyshared.deployments_file import DeploymentsRepo, get_deployment_targets, get_fairytale_name_from_target_file
from pyshared.deprov_info import DeprovInfoDeployFile
from pyshared.git_ops import AirplaneMultiCloneGitTask


@dataclass
class TaskOutput:
    aws_account_id: str = ""
    deprov_type: str = ""
    fairytale_name: str = ""
    org: str = ""
    region: str = ""


class DeploymentDeletionChecker(AirplaneMultiCloneGitTask):
    """Only one account will be torn down at a time. The first account found wins. If multiple accounts need to be torn
    down at the same time, they will be found on the next run of this task. This greatly simplfies the logic of all
    future deprovisioning tasks."""

    def __init__(self):
        super().__init__(git_repos=(DeploymentsRepo.HOSTED, DeploymentsRepo.STAGING))
        self.now = datetime.now(DEPROV_TZ)

    def main(self, params=None):
        for repo_dir in self.git_dirs.values():
            for filepath in get_deployment_targets(repo_dir=repo_dir):
                task_output = self._add_teardowns_for_customer(filepath)
                if task_output is not None:
                    return asdict(task_output)
        return asdict(TaskOutput())

    def _add_teardowns_for_customer(self, filepath):
        deprov_info_deploy_file = DeprovInfoDeployFile(filepath)
        deprov_info = deprov_info_deploy_file.retrieve_deprov_info()
        deprov_type = None
        if deprov_info.dns_removal_time and deprov_info.dns_removal_time < self.now:
            deprov_type = "dns"
        elif deprov_info.teardown_time and deprov_info.teardown_time < self.now:
            deprov_type = "teardown"
        if deprov_type is not None:
            return TaskOutput(deprov_type=deprov_type,
                              fairytale_name=get_fairytale_name_from_target_file(filepath),
                              aws_account_id=deprov_info.aws_account_id,
                              org=deprov_info.organization,
                              region=deprov_info_deploy_file.get_deprov_region())
        return None


def main(_):
    return DeploymentDeletionChecker().main({})
