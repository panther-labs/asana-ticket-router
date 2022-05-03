from v2.pyshared.os_util import join_paths


def get_deployment_group_dir(repo_path: str = "") -> str:
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
    return join_paths(get_deployment_group_dir(repo_path), f"{group_name}.yml")
