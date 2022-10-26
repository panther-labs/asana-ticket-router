import tempfile

from semver import VersionInfo

from deployment_info import RepoDetails, TuesdayMorningGA
from git_util import GitRepo
from os_util import join_paths


def get_tuesday_morning_version(repo_details: RepoDetails) -> VersionInfo:
    """
    get_tuesday_morning_version accepts repo_details as an argument
    and opens the file defined in the TuesdayMorningGA TARGET_FILE
    class attribute (similar to files in upgrade_groups()).

    Depending on whether the file exists in the repo,
    either the target version or `None` will be returned.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = GitRepo(path=tmp_dir, repo_name=repo_details.name, branch_name=repo_details.branch)
        target_ga_file_path = join_paths(repo.path, "deployment-metadata", TuesdayMorningGA.TARGET_FILE)
        with open(target_ga_file_path, "r") as target_ga_file:
            return VersionInfo.parse(target_ga_file.read().strip())
