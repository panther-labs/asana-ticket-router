import os
from typing import Dict
from collections.abc import Callable

from pyshared.airplane_utils import AirplaneTask, is_test_run
from pyshared.git_ops import git_clone, git_add_commit_push
from pyshared.load_py_file import load_py_file_as_module
from pyshared.os_utils import tmp_change_dir


class DeploymentsRepo:
    HOSTED = "hosted-deployments"
    STAGING = "staging-deployments"


def get_deployment_filepath(fairytale_name: str, repo_dir: str = "", get_generated_filepath: bool = False) -> str:
    parent_dir = "deployment-targets" if not get_generated_filepath else "generated"
    return os.path.join(repo_dir, "deployment-metadata", parent_dir, f"{fairytale_name}.yml")


def get_deployment_groups_dir(repo_dir: str = ""):
    return os.path.join(repo_dir, "deployment-metadata", "deployment-groups")


def get_deployment_targets_dir(repo_dir: str = ""):
    return os.path.join(repo_dir, "deployment-metadata", "deployment-targets")


def get_deployment_group_filepath(group_name: str, repo_dir: str = ""):
    return os.path.join(os.path.join(get_deployment_groups_dir(repo_dir=repo_dir), f"{group_name}.yml"))


def get_deployment_group_choices(repo_dir: str = ""):
    return [group.removesuffix(".yml") for group in os.listdir(get_deployment_groups_dir(repo_dir=repo_dir))]


def gen_cfgs():
    generate_filepath = "automation-scripts/generate.py"
    generate_mod = load_py_file_as_module(py_file_path=generate_filepath)
    generate_mod.generate_configs()


def alter_deployment_file(deployments_repo: str,
                          ap_params: Dict[str, str],
                          alter_callable: Callable[str],
                          commit_title: str,
                          apply_to_generated_file: bool = False):
    """Alter a deployment file in some way. The alter_callable is a function that, given the deployment file, will
    alter it."""
    deploy_dir = git_clone(repo=deployments_repo, github_setup=True, existing_dir=ap_params.get(deployments_repo))
    with tmp_change_dir(change_dir=deploy_dir):
        alter_callable(get_deployment_filepath(fairytale_name=ap_params["fairytale_name"]))
        if apply_to_generated_file:
            alter_callable(
                get_deployment_filepath(fairytale_name=ap_params["fairytale_name"], get_generated_filepath=True))
        gen_cfgs()

        git_add_commit_push(files=("deployment-metadata",), title=commit_title, test_run=is_test_run(ap_params))
