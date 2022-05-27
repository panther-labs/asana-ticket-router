from v2.pyshared.os_util import join_paths, load_py_file_as_module, tmp_change_dir


def get_generate_configs_path(repo_path: str = "") -> str:
    """
    :param repo_path: Absolute path of the repo
    :return: Absolute or relative path of the generate.py script
    """
    return join_paths(repo_path, "automation-scripts", "generate.py")


def get_deployment_groups_dir(repo_path: str = "") -> str:
    """
    :param repo_path: Absolute path of the repo
    :return: Absolute or relative path of the deployment groups directory
    """
    return join_paths(repo_path, "deployment-metadata", "deployment-groups")


def get_deployment_group_filepath(group_name: str, repo_path: str = "") -> str:
    """
    :param group_name: Deployment group name
    :param repo_path: Absolute path of the repo
    :return: Absolute or relative path of the deployment group config file
    """
    return join_paths(get_deployment_groups_dir(repo_path), f"{group_name}.yml")


def generate_configs(repo_path: str) -> None:
    """
    Run 'generate.py' script in the specified repo
    :param repo_path: Absolute path of the repo
    :return: None
    """
    # Need to execute from within the repo due to relative imports in the generate.py
    with tmp_change_dir(repo_path):
        generate_configs_path = get_generate_configs_path(repo_path)
        module = load_py_file_as_module(filepath=generate_configs_path)
        module.generate_configs()
