from sys import path

import pytest

path.append("./")

from app import get_target_semver
from deployment_info import DeploymentGroup, DeploymentSchedule, GA, RC, TuesdayMorningGA, \
    UpgradeVersions, is_downgrade
from semver import VersionInfo


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
