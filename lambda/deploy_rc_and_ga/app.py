"""
Lambda function to deploy latest RC and GA versions
"""
import tempfile
from functools import cmp_to_key

import yaml
import boto3
from botocore.exceptions import ClientError
from semver import VersionInfo

from os_util import get_current_dir, change_dir, join_paths, append_to_system_path, load_py_file_as_module
from git_util import GitRepo
from time_util import hours_passed_from_now


class RC:
    VERSION = "rc"
    BUCKET = "panther-internal-rc-us-west-2"


class GA:
    VERSION = "ga"
    BUCKET = "panther-enterprise-us-west-2"


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
    STAGING = RepoDetails("staging-deployments", "main",
                          [DeploymentGroup("staging", RC.VERSION),
                           DeploymentGroup("ga", GA.VERSION)])
    HOSTED = RepoDetails("hosted-deployments", "master", [
        DeploymentGroup("internal", RC.VERSION),
    ])
    DEMO = RepoDetails("hosted-deployments", "master", [DeploymentGroup("demo", GA.VERSION)])


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


def upgrade_groups(repo_details: RepoDetails, rc: VersionInfo, ga: VersionInfo) -> None:
    current_dir = get_current_dir()
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = GitRepo(path=tmp_dir, repo_name=repo_details.name, branch_name=repo_details.branch)
        change_dir(repo.path)
        for group in repo_details.groups:
            print(f"Checking deployment group '{group.name}'")
            config_file_path = join_paths(repo.path, "deployment-metadata", "deployment-groups", f"{group.name}.yml")
            with open(config_file_path, "r") as config_file:
                config = yaml.load(config_file, Loader=yaml.FullLoader)

            current_semver = VersionInfo.parse(config["Version"].removeprefix("v"))
            target_semver = rc if group.version == RC.VERSION else ga

            if is_downgrade(current_semver, target_semver):
                raise Exception(
                    f"Attempting to downgrade from 'v{current_semver}' to 'v{target_semver}'. File: {config_file_path}")

            config["Version"] = f"v{target_semver}"
            with open(config_file_path, "w") as config_file:
                yaml.dump(config, config_file, sort_keys=False)

        generate_and_lint_configs(repo.path)
        filepaths_to_add = [
            join_paths(repo.path, "deployment-metadata", "deployment-groups"),
            join_paths(repo.path, "deployment-metadata", "generated")
        ]
        repo.add_commit_and_push(title="Upgrade to newest RC and GA versions", filepaths=filepaths_to_add)
    change_dir(current_dir)


def lambda_handler(event, _):
    latest_rc = get_latest_published_rc(RC.BUCKET)

    if event.get("is_demo_deployment", False):
        latest_ga = get_stable_ga(GA.BUCKET, min_version_age_in_hours=48)

        upgrade_groups(repo_details=DeploymentDetails.DEMO, rc=latest_rc, ga=latest_ga)
    else:
        latest_ga = get_latest_published_ga(GA.BUCKET)

        # If the latest GA is higher (newer) than the latest RC, use it, otherwise, keep RC as is
        if latest_ga.compare(latest_rc) == 1:
            print(f"Using latest GA 'v{latest_ga}' as RC version")
            latest_rc = latest_ga

        upgrade_groups(repo_details=DeploymentDetails.HOSTED, rc=latest_rc, ga=latest_ga)
        upgrade_groups(repo_details=DeploymentDetails.STAGING, rc=latest_rc, ga=latest_ga)

    event["latest_rc"] = str(latest_rc)
    event["latest_ga"] = str(latest_ga)
    return event
