from datetime import datetime
import time
import tempfile

from semver import VersionInfo

from deployment_info import DeploymentSchedule, RepoDetails, TuesdayMorningGA, is_downgrade
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
            return target_ga_file.read().strip()


def group_deployment(group_name: str, target_ga_version_path: str, current_version: VersionInfo,
                     target_version: VersionInfo, config_file_path: str, config: str) -> None:
    """
    group_deployment accepts the following arguments:
    - group_name -> the name of the group
    - target_ga_version_path -> the text file containing the target GA version
    - current_version -> the currently deployed semver as defined in the group's YAML file
    - target_version -> the new semver to update to
    - config_file_path -> the location of the group's YAML file
    - config -> the resultant string of the group's YAML config

    For now, this function will use print statements to display what
    would actually happen when this function runs with full functionality
    """
    # Get the tuple of groups to upgrade if the time and day matches the mapping
    # defined on L80
    prod_groups_to_upgrade = DeploymentSchedule.MAPPING.get(time.strftime("%H"),
                                                            {}).get(datetime.today().strftime('%A'), ())
    if group_name in prod_groups_to_upgrade:
        print(f"Found {group_name} in `time_group_mapping`.")
        print(f"Would have run upgrade for {group_name} using new logic.")
        if (group_name == "a") and not is_downgrade(current_version, target_version):
            # generate_target_ga_file(path, target_version)
            print(f"Would generate file {target_ga_version_path} with version {target_version}")
        print(f"Would set config[\"version\"] to {target_version}")
        config["Version"] = f"v{target_version}"
        print(config["Version"])
        # with open(config_file_path, "w") as config_file:
        #    yaml.dump(config, config_file, sort_keys=False)
        print(f"Would dump config to {config_file_path}")
