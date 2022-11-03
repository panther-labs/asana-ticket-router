"""
tuesday_morning_ga contains functionality around
reading and generating the tuesday-ga-version.txt file
"""

import tempfile

from semver import VersionInfo

from deployment_info import RepoDetails, TuesdayMorningGA
from deployment_info import UpgradeVersions
from git_util import GitRepo
from os_util import join_paths
from time_util import DeployTime


def get_tuesday_morning_version(repo_details: RepoDetails) -> VersionInfo:
    """
    get_tuesday_morning_version accepts repo_details as an argument
    and opens the file defined in the TuesdayMorningGA TARGET_FILE
    class attribute (similar to files in upgrade_groups())
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = GitRepo(path=tmp_dir, repo_name=repo_details.name, branch_name=repo_details.branch)
        target_ga_file_path = join_paths(
            repo.path, "deployment-metadata", TuesdayMorningGA.TARGET_FILE
        )
        with open(target_ga_file_path, "r", encoding="utf-8") as target_ga_file:
            return VersionInfo.parse(target_ga_file.read().strip())


def is_time_to_generate_target_ga_file(time: DeployTime) -> bool:
    """
    is_time_generate_target_ga_file checks if the target-ga-version.txt
    file should be updated or not
    """
    return time.hour == "07" and time.day == "Tuesday"


def generate_target_ga_file(repo_details: RepoDetails, version: UpgradeVersions) -> None:
    """
    generate_target_ga_file creates a temporary directory, clones the specified GitHub repo,
    opens the target-ga-version.txt file, writes the updated GA version to the file, and adds
    the updated file for committing
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = GitRepo(path=tmp_dir, repo_name=repo_details.name, branch_name=repo_details.branch)
        target_ga_file_path = join_paths(
            repo.path, "deployment-metadata", TuesdayMorningGA.TARGET_FILE
        )
        commit_title = f"Update target-ga-version.txt to {str(version)}"
        with open(target_ga_file_path, "w", encoding="utf-8") as target_ga_version_file:
            target_ga_version_file.write(str(version))
        repo.add_commit_and_push(title=commit_title, filepaths=[target_ga_file_path])
