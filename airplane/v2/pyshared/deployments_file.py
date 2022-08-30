import subprocess
import sys

from v2.consts.github_repos import GithubRepo
from v2.pyshared.date_utils import Timezone, get_now_str
from v2.pyshared.airplane_logger import logger
from v2.pyshared.os_util import join_paths, load_py_file_as_module, tmp_change_dir
from v2.pyshared.yaml_utils import change_yaml_file


def get_generate_configs_path(repo_path: str = "") -> str:
    """
    :param repo_path: Absolute path of the repo
    :return: Absolute or relative path of the generate.py script
    """
    return join_paths(get_automation_scripts_dir(repo_path), "generate.py")


def get_github_repo_from_organization(organization: str) -> str:
    """
    Get the repo that contains deployment files for a given organization
    :param organization: Either hosted or staging
    :return: The string name of a GitHub repo
    """
    org = organization.lower()
    repo = {"hosted": GithubRepo.HOSTED_DEPLOYMENTS, "root": GithubRepo.STAGING_DEPLOYMENTS}.get(org, None)

    if repo is None:
        raise ValueError(f"No git repo found for organization name {organization}")
    return repo


def manually_deploy_customer(fairytale_name: str, repo_path: str = "."):
    edit_customer_deployment_file(fairytale_name=fairytale_name,
                                  cfg={"ManualDeploy": get_now_str(Timezone.UTC)},
                                  repo_path=repo_path)
    generate_configs(repo_path=repo_path)


def get_lint_path(repo_path: str = "") -> str:
    """
    :param repo_path: Absolute path of the repo
    :return: Absolute or relative path of the generate.py script
    """
    return join_paths(get_automation_scripts_dir(repo_path), "lint.py")


def get_deployment_metadata_dir(repo_path: str = "") -> str:
    """
    :param repo_path: Absolute path of the repo
    :return: Absolute or relative path of the deployment-metadata directory
    """
    return join_paths(repo_path, "deployment-metadata")


def get_automation_scripts_dir(repo_path: str = "") -> str:
    """
    :param repo_path: Absolute path of the repo
    :return: Absolute or relative path of the automation-scripts directory
    """
    return join_paths(repo_path, "automation-scripts")


def get_deployment_groups_dir(repo_path: str = "") -> str:
    """
    :param repo_path: Absolute path of the repo
    :return: Absolute or relative path of the deployment groups directory
    """
    return join_paths(get_deployment_metadata_dir(repo_path), "deployment-groups")


def get_deployment_group_filepath(group_name: str, repo_path: str = "") -> str:
    """
    :param group_name: Deployment group name
    :param repo_path: Absolute path of the repo
    :return: Absolute or relative path of the deployment group config file
    """
    return join_paths(get_deployment_groups_dir(repo_path), f"{group_name}.yml")


def get_customer_deployment_filepath(fairytale_name: str, repo_path: str = "", get_generated_filepath: bool = False)\
        -> str:
    """
    Get a customer's deployment filepath, which contains settings for its deployment.
    :param fairytale_name: Alias for the customer
    :param repo_path: Absolute path of the repo
    :param get_generated_filepath: If True, get the generated config rather than the deployment-targets config
    :return: Absolute or relative path of the customer's deployment config file
    """
    parent_dir = "deployment-targets" if not get_generated_filepath else "generated"
    return join_paths(get_deployment_metadata_dir(repo_path), parent_dir, f"{fairytale_name}.yml")


def edit_customer_deployment_file(fairytale_name: str, cfg: dict, repo_path: str = "") -> None:
    """
    Edit a customer's deployment settings.
    :param fairytale_name: Alias for the customer
    :param cfg: Dictionary of attributes to set or modify for the customer
    :param repo_path: Absolute path of the repo
    """
    with change_yaml_file(cfg_filepath=get_customer_deployment_filepath(fairytale_name=fairytale_name,
                                                                        repo_path=repo_path)) as yaml_cfg:
        yaml_cfg.update(cfg)


def generate_configs(repo_path: str = ".") -> None:
    """
    Run 'generate.py' script in the specified repo
    :param repo_path: Absolute path of the repo
    :return: None
    """
    with tmp_change_dir(repo_path):
        _add_auto_scripts_to_path(repo_path)
        generate_configs_path = get_generate_configs_path(repo_path)
        module = load_py_file_as_module(filepath=generate_configs_path)
        module.generate_configs()


def lint_configs(repo_path: str = ".") -> None:
    """
    Run 'lint.py' script in the specified repo
    :param repo_path: Absolute path of the repo
    :return: None
    """
    with tmp_change_dir(repo_path):
        _add_auto_scripts_to_path(repo_path)
        module = load_py_file_as_module(filepath=get_lint_path(repo_path))
        module.run_checks()


def create_customer_file(repo_path: str, customer_cfg: dict, gen_cfg: bool = True, lint: bool = True) -> str:
    """
    Create a deployment file for a customer.
    :param repo_path: Absolute path of the repo
    :param customer_cfg: Configuration to go into the customer's deployment file
    :param gen_cfg: Set to true to create the generated deployment file
    :param lint: Set to true to lint the deployment files
    :return: The fairytale name of the customer
    """
    pip_install_auto_scripts_requirements(repo_path)
    auto_scripts = get_automation_scripts_dir(repo_path)
    with tmp_change_dir(repo_path):
        _add_auto_scripts_to_path(repo_path)
        create_customer_config = load_py_file_as_module(filepath=join_paths(auto_scripts, "create_customer_config.py"))
        fairytale_name = create_customer_config.create_customer_metadata(customer_cfg=customer_cfg)
        if gen_cfg:
            generate_configs(repo_path)
        if lint:
            lint_configs(repo_path)

        return fairytale_name


def pip_install_auto_scripts_requirements(repo_path: str = ".") -> None:
    """
    Install requirements needed to run hosted deployment automation scripts
    :param repo_path: Absolute path of the repo
    :return: None
    """
    logger.info(f"pip installing automation-scripts requirements for {repo_path}")
    reqs = join_paths(get_automation_scripts_dir(repo_path), "requirements.txt")
    subprocess.check_call(f"{sys.executable} -m pip install -r {reqs}", shell=True, stdout=subprocess.DEVNULL)


def _add_auto_scripts_to_path(repo_path: str) -> None:
    """
    Add the automated-scripts directory to Python path.
    :param repo_path: Absolute path of the repo
    :return: None
    """
    path = get_automation_scripts_dir(repo_path)
    if path not in sys.path:
        sys.path.append(path)
