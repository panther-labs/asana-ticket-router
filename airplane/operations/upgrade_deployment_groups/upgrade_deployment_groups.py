from dataclasses import dataclass
from typing import List

from pyshared.deployments_file import (DeploymentsRepo, gen_cfgs, get_deployment_group_choices,
                                       get_deployment_group_filepath)
from pyshared.git_ops import AirplaneModifyGitTask
from pyshared.os_utils import tmp_change_dir
from pyshared.yaml_utils import load_yaml_cfg, save_yaml_cfg
from v2.exceptions import ConflictingParameterException

@dataclass
class AirplaneParams:
    version: str
    all_groups: bool = False
    deployment_groups: str = ""


@dataclass
class ParsedParams:
    deployment_groups: str
    deployment_group_filepaths: List[str]
    version: str

class UpgradeDeploymentGroups(AirplaneModifyGitTask):
    def __init__(self, params):
        super().__init__(params=params, git_repo=DeploymentsRepo.HOSTED)
        self.eligible_groups = [group for group in get_deployment_group_choices(repo_dir=self.git_dir) if group not in ['internal', 'demo', 'hold']]
        self.parsed_params = self._parse_params(ap_params=AirplaneParams(**params))

    @staticmethod
    def _format_version(version) -> str:
        if version.startswith("v"):
            return version
        return f"v{version}"

    def get_group_filepaths(self, ap_params: AirplaneParams) -> list:
        if ap_params.all_groups:
            groups = self.eligible_groups
        else:
            groups = [group.strip().lower() for group in ap_params.deployment_groups.split(",") if group in self.eligible_groups]

        return [get_deployment_group_filepath(group_name=group) for group in groups]

    def _parse_params(self, ap_params: AirplaneParams) -> ParsedParams:
        if ap_params.deployment_groups and ap_params.all_groups:
            raise ConflictingParameterException(
                f"ERROR: Cannot use both `all_groups` and `deployment_groups`. Please only use one of the parameters"
            )
        with tmp_change_dir(change_dir=self.git_dir):
            group_filepaths = self.get_group_filepaths(ap_params)
            return ParsedParams(deployment_group_filepaths=group_filepaths,
                                deployment_groups=ap_params.deployment_groups,
                                version=self._format_version(ap_params.version))

    def get_git_title(self):
        return f"Upgrading groups {self.parsed_params.deployment_groups} to {self.parsed_params.version}"

    def change_files(self):
        for filepath in self.parsed_params.deployment_group_filepaths:
            cfg = load_yaml_cfg(filepath)
            cfg["Version"] = self.parsed_params.version
            save_yaml_cfg(cfg_filepath=filepath, cfg=cfg)
        gen_cfgs()
        return ("deployment-metadata", )


def main(params):
    UpgradeDeploymentGroups(params).main()
