from dataclasses import dataclass
import glob
import os
import shutil

from pyshared.airplane_utils import AirplaneTask
from pyshared.deployments_file import alter_deployment_file
from pyshared.git_ops import git_clone, git_add_commit_push
from pyshared.os_utils import tmp_change_dir
from v2.consts.github_repos import GithubRepo
from v2.pyshared.deployments_file import get_github_repo_from_organization


@dataclass
class AirplaneParams:
    fairytale_name: str
    organization: str


class DeploymentFileRemover(AirplaneTask):

    def remove_management_files(self, ap_params):
        repo_name = GithubRepo.HOSTED_AWS_MANAGEMENT
        git_dir = git_clone(repo=repo_name, github_setup=True, existing_dir=os.environ.get(repo_name))
        with tmp_change_dir(change_dir=git_dir):
            dirs_to_delete = glob.glob(f"*{ap_params.fairytale_name}*")
            [shutil.rmtree(dir_to_delete) for dir_to_delete in dirs_to_delete]
            git_add_commit_push(files=dirs_to_delete,
                                title=f"Removing dirs for {ap_params.fairytale_name}",
                                test_run=self.is_test_run())

    def main(self, params):
        ap_params = AirplaneParams(**params)
        alter_deployment_file(deployments_repo=get_github_repo_from_organization(ap_params.organization),
                              ap_params=params,
                              alter_callable=lambda filepath: os.remove(filepath),
                              commit_title=f"Removing deployment files for {params['fairytale_name']}",
                              apply_to_generated_file=True)
        if ap_params.organization == "hosted":
            self.remove_management_files(ap_params=ap_params)


def main(params):
    DeploymentFileRemover(requires_parent_execution=True).main(params)
