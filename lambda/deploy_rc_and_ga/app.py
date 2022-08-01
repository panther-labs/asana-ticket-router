"""
Lambda function to deploy latest RC and GA versions
"""
import os
import sys
import tempfile
import importlib.util
from functools import cmp_to_key

import yaml
import boto3
from botocore.exceptions import ClientError
from semver import VersionInfo

from git_util import git_clone, git_add_commit_and_push


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
    STAGING = RepoDetails(
        "staging-deployments",
        "main",
        [
            DeploymentGroup("staging", RC.VERSION),
            DeploymentGroup("ga", GA.VERSION)
        ]
    )
    HOSTED = RepoDetails(
        "hosted-deployments",
        "master",
        [
            DeploymentGroup("internal", RC.VERSION),
            DeploymentGroup("alpha", GA.VERSION),
            DeploymentGroup("demo", GA.VERSION)
        ]
    )


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


def get_latest_published_rc(bucket_name: str) -> VersionInfo or None:
    available_versions = get_available_versions(bucket_name)
    for version in available_versions:
        if not is_ga_version(version) and is_published(version, bucket_name):
            return version


def get_latest_published_ga(bucket_name: str) -> VersionInfo or None:
    available_versions = get_available_versions(bucket_name)
    for version in available_versions:
        if is_ga_version(version) and is_published(version, bucket_name):
            return version


def load_py_file_as_module(filepath: str):
    """
    :param filepath: Absolute filepath
    :return: Python module object
    """
    spec = importlib.util.spec_from_file_location("module.name", filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generate_and_lint_configs(repo_path: str) -> None:
    automation_scripts_path = os.path.join(repo_path, "automation-scripts")
    if automation_scripts_path not in sys.path:
        sys.path.append(automation_scripts_path)

    # generate.py
    print("Generating configs")
    generate_configs_path = os.path.join(automation_scripts_path, "generate.py")
    module = load_py_file_as_module(filepath=generate_configs_path)
    module.generate_configs()

    # lint.py
    print("Linting configs")
    lint_configs_path = os.path.join(automation_scripts_path, "lint.py")
    module = load_py_file_as_module(filepath=lint_configs_path)
    module.run_checks()


def is_downgrade(current_version: VersionInfo, target_version: VersionInfo) -> bool:
    return target_version.compare(current_version) == -1


def upgrade_groups(repo_details: RepoDetails,
                   rc_version: VersionInfo,
                   ga_version: VersionInfo,
                   is_demo_deployment: bool) -> None:
    cur_dir = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = git_clone(target_dir=tmp_dir, repo_name=repo_details.name, branch_name=repo_details.branch)
        os.chdir(repo_path)

        for group in repo_details.groups:
            if group.name == "demo" and not is_demo_deployment:
                print("Skipping 'demo' group deployment")
                continue

            print(f"Checking deployment group '{group.name}'")
            config_file_path = f"deployment-metadata/deployment-groups/{group.name}.yml"
            with open(config_file_path, "r") as config_file:
                config = yaml.load(config_file, Loader=yaml.FullLoader)

            current_semver = VersionInfo.parse(config["Version"].removeprefix("v"))
            target_semver = rc_version if group.version == RC.VERSION else ga_version

            if is_downgrade(current_semver, target_semver):
                raise Exception(
                    f"Attempting to downgrade from 'v{current_semver}' to 'v{target_semver}'. File: {repo_details.name}/{config_file_path}")

            config["Version"] = f"v{target_semver}"
            with open(config_file_path, "w") as config_file:
                yaml.dump(config, config_file, sort_keys=False)

        generate_and_lint_configs(repo_path)
        git_add_commit_and_push(title="Upgrade to newest RC and GA versions")

    os.chdir(cur_dir)


def lambda_handler(event, _):
    latest_rc = get_latest_published_rc(RC.BUCKET)
    print(f"Latest RC: {latest_rc}")

    latest_ga = get_latest_published_ga(GA.BUCKET)
    print(f"Latest GA: {latest_ga}")

    # If the latest GA is higher (newer) than the latest RC, use it, otherwise, keep RC as is
    if latest_ga.compare(latest_rc) == 1:
        print(f"Using latest GA '{latest_ga}' as RC version")
        latest_rc = latest_ga

    is_demo_deployment = event.get("is_demo_deployment", False)
    upgrade_groups(DeploymentDetails.HOSTED, latest_rc, latest_ga, is_demo_deployment)
    upgrade_groups(DeploymentDetails.STAGING, latest_rc, latest_ga, is_demo_deployment)

    event["latest_rc"] = str(latest_rc)
    event["latest_ga"] = str(latest_ga)
    return event
