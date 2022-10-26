"""
Lambda function to deploy latest RC and GA versions
"""
import datetime
import os
import string
import tempfile
import time
from functools import cmp_to_key

import boto3
import yaml
from botocore.exceptions import ClientError
from semver import VersionInfo

from git_util import GitRepo
from os_util import get_current_dir, change_dir, join_paths, append_to_system_path, load_py_file_as_module
from time_util import hours_passed_from_now

os.environ['TZ'] = "America/Los_Angeles"


class RC:
    VERSION = "rc"
    BUCKET = "panther-internal-rc-us-west-2"


class GA:
    VERSION = "ga"
    BUCKET = "panther-enterprise-us-west-2"


class TuesdayMorningGA:
    # Leaving the class attribute as "ga" for now
    # This shouldn't be used, so perhaps `None` is better?
    VERSION = "ga"
    BUCKET = "panther-enterprise-us-west-2"
    TARGET_FILE = "target-ga-version.txt"


class DeploymentGroup:

    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version


class RepoDetails:

    def __init__(self, name: str, branch: str, groups: list[DeploymentGroup]):
        self.name = name
        self.branch = branch
        self.groups = groups


class DeploymentDetails:
    groups = [DeploymentGroup(letter, TuesdayMorningGA.VERSION) for letter in string.ascii_lowercase if
              letter not in ("f", "h", "i")] + [DeploymentGroup("internal", RC.VERSION)]

    STAGING = RepoDetails("staging-deployments", "main",
                          [DeploymentGroup("staging", RC.VERSION),
                           DeploymentGroup("ga", GA.VERSION)])
    HOSTED = RepoDetails("hosted-deployments", "master", groups)
    DEMO = RepoDetails("hosted-deployments", "master", [DeploymentGroup("demo", GA.VERSION)])


class DeploymentSchedule:
    """
    The DepoloymentSchedule class defines a mapping between times
    (as hours in the "America/Los_Angeles" time zone) and the groups
    to be updated during that hour.

    The mapping is expressed as a nested dictionary with the hours as
    top-level keys with the days of the week as nested keys and the
    groups for each day as the values.
    """

    MAPPING = {
        "07": {
            "Tuesday": ("a",),
            "Wednesday": ("n",),
            "Thursday": ("t",)
        },
        "08": {
            "Tuesday": (),
            "Wednesday": ("o",),
            "Thursday": ("u",),
        },
        "09": {
            "Tuesday": (),
            "Wednesday": ("p",),
            "Thursday": ("v",),
        },
        "10": {
            "Tuesday": ("c",),
            "Wednesday": ("q",),
            "Thursday": ("w",),
        },
        "11": {
            "Tuesday": ("j",),
            "Wednesday": ("r",),
            "Thursday": ("x",),
        },
        "12": {
            "Tuesday": ("k",),
            "Wednesday": ("s",),
            "Thursday": ("y",),
        },
        "13": {
            "Tuesday": ("m",),
            "Wednesday": (),
            "Thursday": ("z",),
        },
    }


def get_available_versions(bucket_name: str) -> list[VersionInfo]:
    """
    :return: List of available versions in descending order
    """
    available_versions = []
    client = boto3.client('s3')
    paginator = client.get_paginator('list_objects')
    result = paginator.paginate(Bucket=bucket_name, Delimiter='/', Prefix="v")
    for prefix in result.search('CommonPrefixes'):
        version = prefix.get('Prefix').removeprefix("v").removesuffix("/")
        parsed_version = VersionInfo.parse(version)
        available_versions.append(parsed_version)
    available_versions.sort(key=cmp_to_key(lambda v1, v2: v1.compare(v2)), reverse=True)
    return available_versions


def is_ga_version(version: VersionInfo) -> bool:
    return version.prerelease is None


def is_published(version: VersionInfo, bucket_name: str) -> bool:
    client = boto3.client('s3')
    try:
        client.get_object(Bucket=bucket_name, Key=f'v{version}/panther.yml')
        return True
    except ClientError:
        print(f"Version 'v{version}' is not published yet.")
        return False


def get_version_age_in_hours(version: VersionInfo, bucket_name: str) -> int:
    client = boto3.client('s3')
    response = client.get_object(Bucket=bucket_name, Key=f'v{version}/panther.yml')
    return hours_passed_from_now(response["LastModified"])


def get_latest_published_rc(bucket_name: str) -> VersionInfo or None:
    available_versions = get_available_versions(bucket_name)
    for version in available_versions:
        if not is_ga_version(version) and is_published(version, bucket_name):
            print(f"Latest published RC: v{version}")
            return version


def get_latest_published_ga(bucket_name: str) -> VersionInfo or None:
    available_versions = get_available_versions(bucket_name)
    for version in available_versions:
        if is_ga_version(version) and is_published(version, bucket_name):
            print(f"Latest published GA: v{version}")
            return version


def get_stable_ga(bucket_name: str, min_version_age_in_hours: int) -> VersionInfo or None:
    available_versions = get_available_versions(bucket_name)
    for version in available_versions:
        if is_ga_version(version) and is_published(version, bucket_name):
            version_age_in_hours = get_version_age_in_hours(version, bucket_name)
            if version_age_in_hours < min_version_age_in_hours:
                print(f"Skipping GA version 'v{version}' as it's only {version_age_in_hours} hours old")
            else:
                print(f"Latest stable GA: v{version} ({version_age_in_hours} hours old)")
                return version


def get_tuesday_morning_version(repo_details: RepoDetails) -> VersionInfo or None:
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
        try:
            with open(target_ga_file_path, "r") as target_ga_file:
                return target_ga_file.read().strip()
        except FileNotFoundError:
            print(f"Target GA File not found at path {target_ga_file_path}")
            return None


def generate_and_lint_configs(repo_path: str) -> None:
    automation_scripts_path = join_paths(repo_path, "automation-scripts")
    append_to_system_path(automation_scripts_path)

    # generate.py
    print("Generating configs")
    generate_configs_path = join_paths(automation_scripts_path, "generate.py")
    module = load_py_file_as_module(generate_configs_path)
    module.generate_configs()

    # lint.py
    print("Linting configs")
    lint_configs_path = join_paths(automation_scripts_path, "lint.py")
    module = load_py_file_as_module(lint_configs_path)
    module.run_checks()


def is_downgrade(current_version: VersionInfo, target_version: VersionInfo) -> bool:
    return target_version.compare(current_version) == -1


def generate_target_ga_file(path: str, target_version: VersionInfo) -> None:
    """
    Generate the target GA file with the specified target version using w+
    as the mode in the event the file does not exist.
    """
    with open(path, "w+") as target_ga_version_file:
        target_ga_version_file.write(target_version)


def group_deployment(group_name: str, target_ga_version_path: str, current_version: VersionInfo,
                     target_version: VersionInfo,
                     config_file_path: str, config: str) -> None:
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


def upgrade_groups(repo_details: RepoDetails, rc: VersionInfo, ga: VersionInfo,
                   tuesday_morning_ga: VersionInfo) -> None:
    current_dir = get_current_dir()
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = GitRepo(path=tmp_dir, repo_name=repo_details.name, branch_name=repo_details.branch)
        # Form the target_ga_file_path like the other paths in this function
        # Leaving this assignment here since it relies on `repo.path`
        target_ga_file_path = join_paths(repo.path, "deployment-metadata", TuesdayMorningGA.TARGET_FILE)
        skip_push = True
        change_dir(repo.path)
        for group in repo_details.groups:
            print(f"Checking deployment group '{group.name}'")
            config_file_path = join_paths(repo.path, "deployment-metadata", "deployment-groups", f"{group.name}.yml")
            with open(config_file_path, "r") as config_file:
                # YML100: Use of unsafe yaml load. Allows instantiation of arbitrary objects. Consider yaml.safe_load().
                # Should we consider updating this?
                config = yaml.load(config_file, Loader=yaml.FullLoader)

            current_semver = VersionInfo.parse(config["Version"].removeprefix("v"))

            # If the group is an instance of the TuesdayMorningGA class and the value
            # of `tuesday_morning_ga` is not None, use that version
            # If the group is an instance of the TuesdayMorningGA class and the value
            # of `tuesday_morning_ga` is None, continue
            # Otherwise, default to the original logic if the group is not an instance
            # of the TuesdayMorningGA class
            if isinstance(group, TuesdayMorningGA) and tuesday_morning_ga is not None:
                target_semver = tuesday_morning_ga
            elif isinstance(group, TuesdayMorningGA) and tuesday_morning_ga is None:
                continue
            elif not isinstance(group, TuesdayMorningGA):
                skip_push = False
                target_semver = rc if group.version == RC.VERSION else ga

            if is_downgrade(current_semver, target_semver):
                raise Exception(
                    f"Attempting to downgrade from 'v{current_semver}' to 'v{target_semver}'. File: {config_file_path}")

            group_deployment(group.name, target_ga_file_path, current_semver, target_semver, config_file_path, config)

            config["Version"] = f"v{target_semver}"
            with open(config_file_path, "w") as config_file:
                yaml.dump(config, config_file, sort_keys=False)

        generate_and_lint_configs(repo.path)
        filepaths_to_add = [
            join_paths(repo.path, "deployment-metadata", "deployment-groups"),
            join_paths(repo.path, "deployment-metadata", "generated"),
            join_paths(repo.path, "deployment-metadata", TuesdayMorningGA.TARGET_FILE)
        ]
        if not skip_push:
            repo.add_commit_and_push(title="Upgrade to newest RC and GA versions", filepaths=filepaths_to_add)

    change_dir(current_dir)


def lambda_handler(event, _):
    latest_rc = get_latest_published_rc(RC.BUCKET)

    # Utilize a separate helper function to read the target GA version from the text file if the file exists
    tuesday_morning_ga = get_tuesday_morning_version(repo_details=DeploymentDetails.HOSTED)

    if event.get("is_demo_deployment", False):
        latest_ga = get_stable_ga(GA.BUCKET, min_version_age_in_hours=48)

        upgrade_groups(repo_details=DeploymentDetails.DEMO, rc=latest_rc, ga=latest_ga)
    else:
        latest_ga = get_latest_published_ga(GA.BUCKET)

        # If the latest GA is higher (newer) than the latest RC, use it, otherwise, keep RC as is
        if latest_ga.compare(latest_rc) == 1:
            print(f"Using latest GA 'v{latest_ga}' as RC version")
            latest_rc = latest_ga

        upgrade_groups(repo_details=DeploymentDetails.HOSTED, rc=latest_rc, ga=latest_ga,
                       tuesday_morning_ga=tuesday_morning_ga)
        upgrade_groups(repo_details=DeploymentDetails.STAGING, rc=latest_rc, ga=latest_ga,
                       tuesday_morning_ga=tuesday_morning_ga)

    event["latest_rc"] = str(latest_rc)
    event["latest_ga"] = str(latest_ga)
    return event
