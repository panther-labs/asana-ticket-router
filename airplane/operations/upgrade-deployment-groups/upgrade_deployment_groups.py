from dataclasses import dataclass
from typing import List

from pyshared.airplane_utils import main
from pyshared.deployments_file import (DeploymentsRepo, gen_cfgs, get_deployment_group_choices,
                                       get_deployment_group_filepath)
from pyshared.git_ops import AirplaneGitTask
from pyshared.os_utils import tmp_change_dir
from pyshared.yaml_utils import load_yaml_cfg, save_yaml_cfg


@dataclass
class AirplaneParams:
    deployment_groups: str
    version: str


@dataclass
class ParsedParams:
    deployment_groups: str
    deployment_group_filepaths: List[str]
    version: str


class UpgradeDeploymentGroups(AirplaneGitTask):

    def __init__(self, params):
        super().__init__(params=params, git_repo=DeploymentsRepo.HOSTED)
        self.parsed_params = self._parse_params(airplane_params=AirplaneParams(**params))

    def _parse_params(self, airplane_params: AirplaneParams) -> ParsedParams:
        with tmp_change_dir(change_dir=self.git_dir):
            parsed_deployment_groups = [group.strip().lower() for group in airplane_params.deployment_groups.split(",")]
            invalid_groups = set(parsed_deployment_groups) - set(get_deployment_group_choices())

            if invalid_groups:
                raise ValueError(
                    f"Invalid groups were specified for upgrade: {invalid_groups}, parsed from {airplane_params.deployment_groups}"
                )

            return ParsedParams(deployment_group_filepaths=[
                get_deployment_group_filepath(group_name=group) for group in parsed_deployment_groups
            ],
                                deployment_groups=airplane_params.deployment_groups,
                                version=airplane_params.version
                                if airplane_params.version.startswith("v") else f"v{airplane_params.version}")

    def get_git_title(self):
        return f"Upgrading groups {self.parsed_params.deployment_groups} to {self.parsed_params.version}"

    def change_files(self):
        for filepath in self.parsed_params.deployment_group_filepaths:
            cfg = load_yaml_cfg(filepath)
            cfg["Version"] = self.parsed_params.version
            save_yaml_cfg(cfg_filepath=filepath, cfg=cfg)
        gen_cfgs()
