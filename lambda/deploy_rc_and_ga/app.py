"""
Lambda function to deploy latest RC and GA versions
"""
import os
import tempfile
from dataclasses import asdict
from functools import cmp_to_key

import boto3
import yaml
from botocore.exceptions import ClientError
from semver import VersionInfo

from deployment_info import GA, RC, DeploymentDetails, RepoDetails, \
    TuesdayMorningGA, UpgradeVersions, is_downgrade, is_time_to_upgrade, get_time, DeploymentSchedule
from git_util import GitRepo
from os_util import get_current_dir, change_dir, join_paths, append_to_system_path, load_py_file_as_module
from time_util import hours_passed_from_now
from tuesday_morning_ga import get_tuesday_morning_version, generate_target_ga_file, is_time_to_generate_target_ga_file

os.environ['TZ'] = "America/Los_Angeles"

hour, day = get_time()
scheduled_groups = [group for days in DeploymentSchedule.MAPPING.values() for group in days.values()]


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


def get_target_semver(group, versions):
    return {
        GA.VERSION: versions.latest_ga,
        RC.VERSION: versions.latest_rc,
        TuesdayMorningGA.VERSION: versions.tuesday_morning_ga
    }[group.version]


def upgrade_groups(repo_details: RepoDetails, versions: UpgradeVersions) -> None:
    current_dir = get_current_dir()
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = GitRepo(path=tmp_dir, repo_name=repo_details.name, branch_name=repo_details.branch)
        change_dir(repo.path)
        for group in repo_details.groups:
            if is_time_to_upgrade(scheduled_groups, group.name, hour, day):
                print(f"Checking deployment group '{group.name}'")
                config_file_path = join_paths(repo.path, "deployment-metadata", "deployment-groups",
                                              f"{group.name}.yml")
                with open(config_file_path, "r") as config_file:
                    # YML100: Use of unsafe yaml load. Allows instantiation of arbitrary objects.
                    # Consider yaml.safe_load().
                    # Should we consider updating this?
                    config = yaml.load(config_file, Loader=yaml.FullLoader)

                current_semver = VersionInfo.parse(config["Version"].removeprefix("v"))
                target_semver = get_target_semver(group, versions)

                if is_downgrade(current_semver, target_semver):
                    raise Exception(
                        f"Attempting to downgrade from 'v{current_semver}' to 'v{target_semver}'. File: {config_file_path}")

                config["Version"] = f"v{target_semver}"
                with open(config_file_path, "w") as config_file:
                    yaml.dump(config, config_file, sort_keys=False)

        generate_and_lint_configs(repo.path)
        filepaths_to_add = [
            join_paths(repo.path, "deployment-metadata", "deployment-groups"),
            join_paths(repo.path, "deployment-metadata", "generated"),
        ]
        repo.add_commit_and_push(title="Upgrade to newest RC and GA versions", filepaths=filepaths_to_add)

    change_dir(current_dir)


def get_versions(is_demo_deployment):
    latest_rc = get_latest_published_rc(RC.BUCKET)
    tuesday_morning_ga = get_tuesday_morning_version(repo_details=DeploymentDetails.HOSTED)

    if is_demo_deployment:
        latest_ga = get_stable_ga(GA.BUCKET, min_version_age_in_hours=48)

    else:
        latest_ga = get_latest_published_ga(GA.BUCKET)

        # If the latest GA is higher (newer) than the latest RC, use it, otherwise, keep RC as is
        if latest_ga.compare(latest_rc) == 1:
            print(f"Using latest GA 'v{latest_ga}' as RC version")
            latest_rc = latest_ga

    return UpgradeVersions(latest_ga=latest_ga, latest_rc=latest_rc, tuesday_morning_ga=tuesday_morning_ga)


def set_version_for_deployment_groups(is_demo_deployment, versions):
    if is_demo_deployment:
        upgrade_groups(repo_details=DeploymentDetails.DEMO, versions=versions)
    else:
        upgrade_groups(repo_details=DeploymentDetails.HOSTED, versions=versions)
        upgrade_groups(repo_details=DeploymentDetails.STAGING, versions=versions)


def update_event(event, versions):
    dict_versions = asdict(versions)
    for version_type in dict_versions:
        event[version_type] = str(dict_versions[version_type])

    return event


def lambda_handler(event, _):
    is_demo_deployment = event.get("is_demo_deployment", False)
    versions = get_versions(is_demo_deployment)
    set_version_for_deployment_groups(is_demo_deployment, versions)
    update_target_ga_file = is_time_to_generate_target_ga_file(hour, day)
    if update_target_ga_file:
        generate_target_ga_file(repo_details=DeploymentDetails.HOSTED, version=versions.tuesday_morning_ga)
    return update_event(event, versions)
