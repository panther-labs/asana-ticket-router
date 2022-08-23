from dataclasses import asdict, dataclass
from datetime import datetime
from typing import List

from operations.deprovisions import DEPROV_TZ
from pyshared.deployments_file import DeploymentsRepo, get_deployment_targets, get_fairytale_name_from_target_file
from pyshared.deprov_info import DeprovInfoDeployFile
from pyshared.git_ops import AirplaneMultiCloneGitTask


@dataclass
class TaskOutput:
    dns_removal_ready: List[str]
    teardown_ready: List[str]


class DeploymentDeletionChecker(AirplaneMultiCloneGitTask):

    def __init__(self):
        super().__init__(git_repos=(DeploymentsRepo.HOSTED, DeploymentsRepo.STAGING))
        self.now = datetime.now(DEPROV_TZ)
        self.output = TaskOutput(dns_removal_ready=[], teardown_ready=[])

    def main(self, params=None):
        for repo_dir in self.git_dirs.values():
            for filepath in get_deployment_targets(repo_dir=repo_dir):
                self._add_teardowns_for_customer(filepath)
        return asdict(self.output)

    def _add_teardowns_for_customer(self, filepath):
        deprov_info = DeprovInfoDeployFile(filepath).retrieve_deprov_info()
        if deprov_info.dns_removal_time and deprov_info.dns_removal_time < self.now:
            self.output.dns_removal_ready.append(get_fairytale_name_from_target_file(filepath))
        if deprov_info.teardown_time and deprov_info.teardown_time < self.now:
            self.output.teardown_ready.append(get_fairytale_name_from_target_file(filepath))

    def get_failure_slack_channel(self):
        return "#triage-deployment"


def main(_):
    return DeploymentDeletionChecker().main_notify_failures({})
