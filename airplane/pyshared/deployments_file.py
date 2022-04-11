from collections.abc import Callable
from enum import Enum
from typing import Dict

from pyshared.git_ops import git_clone, git_add_commit_push
from pyshared.load_py_file import load_py_file_as_module
from pyshared.os_utils import tmp_change_dir


class DeploymentsRepo(Enum):
    HOSTED = "hosted-deployments"
    STAGING = "staging-deployments"


def get_deployment_filepath(fairytale_name, get_generated_filepath=False):
    parent_dir = "deployment-targets" if not get_generated_filepath else "generated"
    return f"deployment-metadata/{parent_dir}/{fairytale_name}.yml"


def gen_cfgs():
    generate_filepath = "automation-scripts/generate.py"
    generate_mod = load_py_file_as_module(py_file_path=generate_filepath)
    generate_mod.generate_configs()


def alter_deployment_file(deployments_repo: DeploymentsRepo, ap_params: Dict[str, str], alter_callable: Callable[str],
                          commit_title: str):
    """Alter a deployment file in some way. The alter_callable is a function that, given the deployment file, will
    alter it."""
    deploy_dir = git_clone(repo=deployments_repo.value,
                           github_setup=True,
                           existing_dir=ap_params.get(deployments_repo.value))
    with tmp_change_dir(change_dir=deploy_dir):
        alter_callable(get_deployment_filepath(fairytale_name=ap_params["fairytale_name"]))
        gen_cfgs()
        git_add_commit_push(files=("deployment-metadata", ),
                            title=commit_title,
                            test_run=ap_params["airplane_test_run"])
