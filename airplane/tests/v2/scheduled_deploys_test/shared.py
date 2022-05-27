import pathlib

import git
import pytest
import ruamel.yaml

from v2.consts.depoyment_groups import HostedDeploymentGroup
from v2.pyshared.date_utils import get_today_str, to_datetime_str, get_now, Timezone
from v2.pyshared.yaml_utils import change_yaml_file, load_yaml_cfg, get_top_level_comments
from v2.tasks.scheduled_deploys.shared import update_group_deployment_schedule, contains_deployment_schedule


@pytest.fixture
def valid_date() -> str:
    return get_today_str()


@pytest.fixture
def valid_time() -> str:
    return "11:59 PM (PDT)"


@pytest.fixture
def valid_datetime(valid_date, valid_time) -> str:
    return f"{valid_date} {valid_time}"


@pytest.fixture
def past_time() -> str:
    return "01:00 AM (PDT)"


@pytest.fixture
def past_datetime() -> str:
    # 15 mins ago
    return to_datetime_str(get_now(tz=Timezone.PDT).subtract(minutes=15))


@pytest.fixture
def future_datetime() -> str:
    # 15 mins ahead
    return to_datetime_str(get_now(tz=Timezone.PDT).add(minutes=15))


@pytest.fixture
def base_version() -> str:
    return "v1.34.10"


@pytest.fixture
def valid_new_version() -> str:
    return "v1.34.11"


@pytest.fixture
def downgrade_version() -> str:
    return "v1.34.9"


@pytest.fixture
def invalid_bump() -> str:
    return "v1.36.9"


def _create_deployment_file(group: str, version: str, parent_dir: pathlib.Path):
    content = f"""
    GroupId: {group}
    Version: {version}
    TopLevelParameters:
      EnableDeployV2: true
    """
    file_path = parent_dir / f"{group}.yml"
    file_path.write_text(content)


def get_deployment_group_file_path(repo_path: pathlib.Path, group_name: str) -> str:
    return str(repo_path / "deployment-metadata" / "deployment-groups" / f"{group_name}.yml")


@pytest.fixture
def hosted_deployments_repo(tmp_path: pytest.fixture, base_version: pytest.fixture) -> pathlib.Path:
    """
    Creates a temporary directory with deployment files. Serves as the hosted deployments repo mock.
    :param tmp_path: Python's 'tmp_path' fixture
    :param base_version: Default deployment version mock/fixture
    :return: Absolute path of the hosted deployments repo mock
    """
    git.Repo.init(tmp_path)
    parent_dir = tmp_path / "deployment-metadata" / "deployment-groups"
    parent_dir.mkdir(exist_ok=True, parents=True)
    for group in HostedDeploymentGroup.get_values():
        _create_deployment_file(group, base_version, parent_dir)
    return tmp_path


def read_deployment_group_file(repo_path: pathlib.Path, group: str) -> ruamel.yaml.CommentedMap:
    deployment_group_file_path = get_deployment_group_file_path(repo_path, group)
    return load_yaml_cfg(deployment_group_file_path)


def add_group_deployment_schedule(repo_path: pathlib.Path, group: str, version: str, time: str) -> None:
    deployment_group_file_path = get_deployment_group_file_path(repo_path, group)
    with change_yaml_file(deployment_group_file_path) as cfg_yaml:
        update_group_deployment_schedule(cfg_yaml, version, time)


def is_deployment_schedule_removed(repo_path: pathlib.Path, group: str) -> bool:
    cfg_yaml = read_deployment_group_file(repo_path, group)
    return not contains_deployment_schedule(cfg_yaml)


def is_deployment_file_updated(old: ruamel.yaml.CommentedMap, new: ruamel.yaml.CommentedMap) -> bool:
    old_comments = get_top_level_comments(old)
    new_comments = get_top_level_comments(new)
    return old_comments != new_comments or old.get("Version") != new.get("Version")


def assert_group_was_updated(repo_path: pathlib.Path, group: str, group_cfg: ruamel.yaml.CommentedMap):
    new_group_cfg = read_deployment_group_file(repo_path, group)
    assert is_deployment_file_updated(old=group_cfg, new=new_group_cfg), \
        f"Group '{group}' deployment file was expected to be updated."


def assert_group_was_not_updated(repo_path: pathlib.Path, group: str, group_cfg: ruamel.yaml.CommentedMap):
    new_group_cfg = read_deployment_group_file(repo_path, group)
    assert not is_deployment_file_updated(old=group_cfg, new=new_group_cfg), \
        f"Group '{group}' deployment file was expected to not be updated."
