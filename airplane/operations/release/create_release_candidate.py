from dataclasses import dataclass
import datetime
from typing import List
import re

from pyshared.git_ops import AirplaneModifyGitTask


@dataclass
class AirplaneParams:
    version: str
    airplane_test_run: bool


@dataclass
class ParsedParams:
    version: str
    airplane_test_run: bool


class CreateReleaseBranch(AirplaneModifyGitTask):

    def __init__(self, params, git_repo, version_file=None):
        super().__init__(params=params, git_repo=git_repo)
        self.parsed_params = self._parse_params(airplane_params=AirplaneParams(**params))
        self.version_file = version_file

    def _format_version(version) -> str:
        if version.startswith("v"):
            version = version[1:]  # strip the leading v
        
        if re.match('^\d\.\d+$', version):
            return version

        raise InvalidPantherVersion(f"The version should be in X.YY format: {version}")
    
    def _parse_params(self, airplane_params: AirplaneParams) -> ParsedParams:
        return ParsedParams(version=self._format_version(airplane_params.version), airplane_test_run=airplane_params.airplane_test_run)

    def get_git_title(self):
        return f"Create Release Candidate {self.parsed_params.version}"
    
    def get_release_branch_name(self):
        branch_prefix = 'release-'
        return f"{branch_prefix}{self.parsed_params.version}"

    def change_files(self) -> List[str]:
        self.checkout_new_branch(self.get_release_branch_name())
        if self.version_file:
            with open(self.version_file, "w") as f:
                f.write(f"{self.parsed_params.version}.0-RC-0000-{datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}")
        return [self.version_file, ]


class InvalidPantherVersion(Exception):
    pass


def main(params):
    CreateReleaseBranch(params, 'panther-enterprise', version_file='VERSION').main()
    CreateReleaseBranch(params, 'panther-auxilary').main()
