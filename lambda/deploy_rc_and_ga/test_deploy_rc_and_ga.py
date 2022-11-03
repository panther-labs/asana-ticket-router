"""
test_deploy_rc_and_ga tests various functionality found
in the modules used for the Deploy RC and GA Lambda
"""
from sys import path

path.append("./")  # pylint: disable=C0413

import pytest
import yaml
from semver import VersionInfo

from app import get_target_semver
from deployment_info import DeploymentGroup, DeploymentSchedule, GA, RC, TuesdayMorningGA, \
    UpgradeVersions, is_downgrade, is_time_to_upgrade
from tuesday_morning_ga import is_time_to_generate_target_ga_file
from time_util import DeployTime


def get_group_list() -> list[tuple[str]]:
    """
    get_group_list returns a list of scheduled groups
    """
    return [group for days in DeploymentSchedule.MAPPING.values() for group in days.values()]


@pytest.mark.parametrize(
    "version_class, expected_version", [(GA, "1.2.3"), (RC, "4.5.6"), (TuesdayMorningGA, "7.8.9")]
)
def test_get_target_semver_from_tuesday_morning_ga(version_class, expected_version):
    """
    test_get_target_semver_from_tuesday_morning_ga checks if the returned
    version matches the expected version for a given group
    """
    group = DeploymentGroup("a", getattr(version_class, "VERSION"))
    versions = UpgradeVersions(latest_ga="1.2.3", latest_rc="4.5.6", tuesday_morning_ga="7.8.9")
    assert get_target_semver(group, versions) == expected_version


@pytest.mark.parametrize(
    "hour, day, group", [
        ("07", "Tuesday", ("a",)), ("07", "Wednesday", ("n",)), ("07", "Thursday", ("t",)),
        ("08", "Tuesday", ()), ("08", "Wednesday", ("o",)), ("08", "Thursday", ("u",)),
        ("09", "Tuesday", ()), ("09", "Wednesday", ("p",)), ("09", "Thursday", ("v",)),
        ("10", "Tuesday", ("c",)), ("10", "Wednesday", ("q",)), ("10", "Thursday", ("w",)),
        ("11", "Tuesday", ("j",)), ("11", "Wednesday", ("r",)), ("11", "Thursday", ("x",)),
        ("12", "Tuesday", ("k",)), ("12", "Wednesday", ("s",)), ("12", "Thursday", ("y",)),
        ("13", "Tuesday", ("m",)), ("13", "Wednesday", ()), ("13", "Thursday", ("z",)),
        ("10", "Tuesday", ("c",))
    ]
)
def test_group_deployment_prod_groups_to_upgrade(hour, day, group):
    """
    test_group_deployment_prod_groups_to_upgrade tests if the group
    returned from the mapping based on the hour and day corresponds
    to the expected group
    """
    assert DeploymentSchedule.MAPPING.get(hour).get(day) == group


@pytest.mark.parametrize(
    "current_version, target_version, output",
    [("1.45.10", "1.45.11", False), ("1.45.11", "1.45.10", True), ("1.45.11", "1.45.11", False)]
)
def test_deployment_info_is_downgrade(current_version, target_version, output):
    """
    test_deployment_info_is_downgrade tests if the is_downgrade function returns
    the expected value based on a current and target version
    """
    assert is_downgrade(
        VersionInfo.parse(current_version), VersionInfo.parse(target_version)
    ) == output


@pytest.mark.parametrize(
    "group_name, hour, day, perform_upgrade", [
        ("a", "07", "Tuesday", True), ("a", "08", "Tuesday", False), ("z", "13", "Thursday", True),
        ("z", "12", "Wednesday", False), ("internal", "11", "Friday", True),
        ("internal", "07", "Wednesday", True), ("internal", "08", "Monday", True),
        ("staging", "07", "Wednesday", True), ("demo", "11", "Thursday", True)
    ]
)
def test_is_time_to_upgrade(group_name, hour, day, perform_upgrade):
    """
    test_is_time_to_upgrade verifies if a given group name is allowed
    to upgrade given group name, hour, and day of the week
    """
    time = DeployTime()
    time.hour = hour
    time.day = day

    # Store the normal exclusions
    default_exclusions = DeploymentSchedule.EXCLUSIONS

    # Use an empty list for this test
    # This avoids test failures on a day we want to exclude
    # since this tests focuses on the base behavior
    DeploymentSchedule.EXCLUSIONS = []

    assert is_time_to_upgrade(get_group_list(), group_name, time) == perform_upgrade

    # Restore original exclusions
    DeploymentSchedule.EXCLUSIONS = default_exclusions


@pytest.mark.parametrize(
    "hour, day, generate_file", [
        ("07", "Tuesday", True), ("07", "Wednesday", False), ("07", "Thursday", False),
        ("08", "Tuesday", False), ("09", "Tuesday", False), ("10", "Tuesday", False),
        ("11", "Tuesday", False), ("12", "Tuesday", False), ("13", "Tuesday", False)
    ]
)
def test_tuesday_morning_ga_is_time_to_generate_target_ga_file(hour, day, generate_file):
    """
    test_tuesday_morning_ga_is_time_to_generate_target_ga_file tests whether the
    target-ga-version.txt file should be updated given an hour and day of the week
    """
    time = DeployTime()
    time.hour = hour
    time.day = day
    assert is_time_to_generate_target_ga_file(time) == generate_file


def test_deploy_time_class():
    """
    test_deploy_time_class ensures the DeployTime
    attribute values are strings
    """
    time = DeployTime()
    for value in time.__dict__.values():
        assert isinstance(value, str)


def test_yaml_safe_load():
    """
    test_yaml_safe_load ensures that the YAML objects parsed by safe_load are identical
    to those parsed by the original load_all method
    """
    with open("mock_config.yml", "r", encoding="utf-8") as safe_mock_yaml:
        safe_yaml_doc = list(yaml.safe_load_all(safe_mock_yaml))
    with open("mock_config.yml", "r", encoding="utf-8") as unsafe_mock_yaml:
        unsafe_yaml_doc = list(yaml.load_all(unsafe_mock_yaml, Loader=yaml.FullLoader))

    for (safe, unsafe) in zip(safe_yaml_doc, unsafe_yaml_doc):
        assert safe == unsafe


@pytest.mark.parametrize(
    "group_name, hour, day, perform_upgrade", [
        ("a", "07", "Tuesday", False),
        ("a", "08", "Tuesday", False),
        ("z", "13", "Thursday", False),
        ("z", "12", "Wednesday", False),
        ("internal", "11", "Friday", False),
        ("internal", "07", "Wednesday", False),
        ("internal", "08", "Monday", False),
        ("staging", "07", "Wednesday", False),
        ("demo", "11", "Thursday", False),
    ]
)
def test_deployment_exclusion_is_time_to_upgrade(group_name, hour, day, perform_upgrade):
    """
    test_deployment_exclusion_is_time_to_upgrade ensures that deployments will not
    happen if the given date is an excluded date
    """
    time = DeployTime()
    time.hour = hour
    time.day = day

    for date in DeploymentSchedule.EXCLUSIONS:
        time.date = date
        assert is_time_to_upgrade(get_group_list(), group_name, time) == perform_upgrade
