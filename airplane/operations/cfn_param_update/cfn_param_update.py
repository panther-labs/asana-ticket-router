import re
from dataclasses import dataclass
from typing import Any

from pyshared.git_ops import AirplaneModifyGitTask
from v2.consts.github_repos import GithubRepo
from v2.pyshared.deployments_file import generate_configs, get_customer_deployment_filepath, lint_configs, \
    pip_install_auto_scripts_requirements
from v2.pyshared.yaml_utils import change_yaml_file


@dataclass
class AirplaneParams:
    fairytale_name: str
    cfn_param_key_vals: str


@dataclass
class ParsedParams:
    fairytale_name: str
    cfn_params: dict[str, Any]


class CfnParamUpdate(AirplaneModifyGitTask):

    def __init__(self, params):
        super().__init__(params=params, git_repo=GithubRepo.HOSTED_DEPLOYMENTS)
        self.parsed_params = self.parse_params(params)

    @staticmethod
    def parse_params(params: AirplaneParams) -> ParsedParams:
        # Use same regex as the validation on Airplane form
        cfn_param_matches = re.findall(r"([^,]+)=([^,]+)", params.cfn_param_key_vals)
        cfn_params = {
            group[0].strip(): CfnParamUpdate.convert_value_to_proper_type(group[1])
            for group in cfn_param_matches
        }
        return ParsedParams(fairytale_name=params.fairytale_name, cfn_params=cfn_params)

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

    def change_files(self):
        with change_yaml_file(cfg_filepath=get_customer_deployment_filepath(
                fairytale_name=self.parsed_params.fairytale_name)) as cfg:
            cfg.setdefault("CloudFormationParameters", {}).update(self.parsed_params.cfn_params)
        pip_install_auto_scripts_requirements(repo_path=".")
        lint_configs(repo_path=".")
        generate_configs(repo_path=".")
        return ["."]

    def get_git_title(self):
        return f"Adding or modifying {self.parsed_params.cfn_params.keys()} for {self.parsed_params.fairytale_name}"


def main(params):
    CfnParamUpdate(AirplaneParams(**params)).main()
