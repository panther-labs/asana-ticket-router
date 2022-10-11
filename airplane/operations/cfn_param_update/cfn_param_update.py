import copy
import re
from dataclasses import dataclass
from typing import Any

from pyshared.git_ops import AirplaneModifyGitTask
from v2.consts.github_repos import GithubRepo
from v2.pyshared.deployments_file import generate_configs, get_customer_deployment_filepath, lint_configs, \
    pip_install_auto_scripts_requirements
from v2.pyshared.yaml_utils import load_yaml_cfg, save_yaml_cfg


@dataclass
class AirplaneParams:
    fairytale_name: str
    cfn_param_key_vals: str
    show_changes_only: bool = False
    requires_parent_execution: bool = False


@dataclass
class ParsedParams:
    fairytale_name: str
    cfn_params: dict[str, Any]
    show_changes_only: bool
    requires_parent_execution: bool = False


class CfnParamUpdate(AirplaneModifyGitTask):
    CFN_KEY = "CloudFormationParameters"

    def __init__(self, params):
        super().__init__(params=params,
                         git_repo=GithubRepo.HOSTED_DEPLOYMENTS,
                         requires_parent_execution=params.requires_parent_execution)
        self.parsed_params = self.parse_params(params)
        self.customer_deploy_file = get_customer_deployment_filepath(fairytale_name=self.parsed_params.fairytale_name)
        self.old_cfn_cfg = None
        self.new_cfn_cfg = None

    @staticmethod
    def parse_params(params: AirplaneParams) -> ParsedParams:
        # Use same regex as the validation on Airplane form
        cfn_param_matches = re.findall(r"([^,]+)=([^,]+)", params.cfn_param_key_vals)
        cfn_params = {
            group[0].strip(): CfnParamUpdate.convert_value_to_proper_type(group[1])
            for group in cfn_param_matches
        }
        return ParsedParams(fairytale_name=params.fairytale_name,
                            cfn_params=cfn_params,
                            show_changes_only=params.show_changes_only)

    @staticmethod
    def convert_value_to_proper_type(val: str):
        """Converts the string value from the Airplane form to a best-guess data type - required for schema
        validation."""
        val = val.strip()
        if val.lower() == "true":
            return True
        if val.lower() == "false":
            return False
        if val.isnumeric():
            return int(val)
        try:
            return float(val)
        except ValueError:
            # Assume the val is a string
            return val

    @staticmethod
    def gen_changed_values(old_cfg: dict[str, Any], new_cfg: dict[str, Any]):
        new_items = {}
        changed_items = {}

        for key in new_cfg:
            if key not in old_cfg:
                new_items[key] = new_cfg[key]
            elif old_cfg[key] != new_cfg[key]:
                changed_items[key] = f"{old_cfg[key]} -> {new_cfg[key]}"
        return {"new_items": new_items, "changed_items": changed_items}

    def _get_cfn_vals(self):
        self.old_cfn_cfg = load_yaml_cfg(cfg_filepath=self.customer_deploy_file)
        self.new_cfn_cfg = copy.deepcopy(self.old_cfn_cfg)
        self.new_cfn_cfg.setdefault(self.CFN_KEY, {}).update(self.parsed_params.cfn_params)

    def change_files(self):
        save_yaml_cfg(cfg_filepath=self.customer_deploy_file, cfg=self.new_cfn_cfg)
        pip_install_auto_scripts_requirements(repo_path=".")
        lint_configs(repo_path=".")
        generate_configs(repo_path=".")
        return ["."]

    def get_git_title(self):
        return f"Update CFN params for {self.parsed_params.fairytale_name}"

    def get_git_description(self):
        updates = "\n  ".join(self.parsed_params.cfn_params.keys())
        return f"Params updated:\n  {updates}"

    def main_within_cloned_dir(self):
        self._get_cfn_vals()
        if not self.parsed_params.show_changes_only:
            super().main_within_cloned_dir()
        return self.gen_changed_values(self.old_cfn_cfg[self.CFN_KEY], self.new_cfn_cfg[self.CFN_KEY])


def main(params):
    return CfnParamUpdate(AirplaneParams(**params)).main()
