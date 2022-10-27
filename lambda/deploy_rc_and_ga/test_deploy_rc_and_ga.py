from sys import path

import pytest

path.append("./")

from app import get_target_semver
from deployment_info import DeploymentGroup, DeploymentSchedule, GA, RC, TuesdayMorningGA, \
    UpgradeVersions, is_downgrade, is_time_to_upgrade, get_time
from semver import VersionInfo
from tuesday_morning_ga import is_time_to_generate_target_ga_file


@pytest.mark.parametrize("version_class, expected_version", [(GA, "1.2.3"), (RC, "4.5.6"), (TuesdayMorningGA, "7.8.9")])
def test_get_target_semver_from_tuesday_morning_ga(version_class, expected_version):
    group = DeploymentGroup("a", getattr(version_class, "VERSION"))
    versions = UpgradeVersions(latest_ga="1.2.3", latest_rc="4.5.6", tuesday_morning_ga="7.8.9")
    assert get_target_semver(group, versions) == expected_version


@pytest.mark.parametrize("hour, day, group",
                         [("07", "Tuesday", ("a",)),
                          ("07", "Wednesday", ("n",)),
                          ("07", "Thursday", ("t",)),
                          ("08", "Tuesday", ()),
                          ("08", "Wednesday", ("o",)),
                          ("08", "Thursday", ("u",)),
                          ("09", "Tuesday", ()),
                          ("09", "Wednesday", ("p",)),
                          ("09", "Thursday", ("v",)),
                          ("10", "Tuesday", ("c",)),
                          ("10", "Wednesday", ("q",)),
                          ("10", "Thursday", ("w",)),
                          ("11", "Tuesday", ("j",)),
                          ("11", "Wednesday", ("r",)),
                          ("11", "Thursday", ("x",)),
                          ("12", "Tuesday", ("k",)),
                          ("12", "Wednesday", ("s",)),
                          ("12", "Thursday", ("y",)),
                          ("13", "Tuesday", ("m",)),
                          ("13", "Wednesday", ()),
                          ("13", "Thursday", ("z",))])
def test_group_deployment_prod_groups_to_upgrade(hour, day, group):
    assert DeploymentSchedule.MAPPING.get(hour).get(day) == group


@pytest.mark.parametrize("current_version, target_version, output",
                         [("1.45.10", "1.45.11", False),
                          ("1.45.11", "1.45.10", True),
                          ("1.45.11", "1.45.11", False)])
def test_deployment_info_is_downgrade(current_version, target_version, output):
    assert is_downgrade(VersionInfo.parse(current_version), VersionInfo.parse(target_version)) == output


@pytest.mark.parametrize("group_name, hour, day, perform_upgrade",
                         [("a", "07", "Tuesday", True),
                          ("a", "08", "Tuesday", False),
                          ("z", "13", "Thursday", True),
                          ("z", "12", "Wednesday", False),
                          ("internal", "11", "Friday", True),
                          ("internal", "07", "Wednesday", True),
                          ("internal", "08", "Monday", True)])
def test_is_time_to_upgrade(group_name, hour, day, perform_upgrade):
    assert is_time_to_upgrade(group_name, hour, day) == perform_upgrade


@pytest.mark.parametrize("hour, day, generate_file", [("07", "Tuesday", True),
                                                      ("07", "Wednesday", False),
                                                      ("07", "Thursday", False),
                                                      ("08", "Tuesday", False),
                                                      ("09", "Tuesday", False),
                                                      ("10", "Tuesday", False),
                                                      ("11", "Tuesday", False),
                                                      ("12", "Tuesday", False),
                                                      ("13", "Tuesday", False)])
def test_tuesday_morning_ga_is_time_to_generate_target_ga_file(hour, day, generate_file):
    assert is_time_to_generate_target_ga_file(hour, day) == generate_file


def test_deployment_info_get_time():
    for value in get_time():
        assert type(value) == str
