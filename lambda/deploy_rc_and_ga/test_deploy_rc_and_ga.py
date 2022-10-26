import pytest

from app import get_target_semver
from deployment_info import DeploymentGroup, GA, RC, TuesdayMorningGA, UpgradeVersions


@pytest.mark.parametrize("version_class, expected_version", [(GA, "1.2.3"), (RC, "4.5.6"), (TuesdayMorningGA, "7.8.9")])
def test_get_target_semver_from_tuesday_morning_ga(version_class, expected_version):
    group = DeploymentGroup("a", getattr(version_class, "VERSION"))
    versions = UpgradeVersions(latest_ga="1.2.3", latest_rc="4.5.6", tuesday_morning_ga="7.8.9")
    assert get_target_semver(group, versions) == expected_version
