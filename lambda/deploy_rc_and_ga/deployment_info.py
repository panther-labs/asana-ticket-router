"""
deployment_info consolidates classes around versions,
repositories, deployment groups, schedules, and
validation logic
"""

import string
from dataclasses import dataclass

from semver import VersionInfo


class RC:  # pylint: disable=R0903
    """
    RC contains attributes for RC versions and where releases are stored
    """
    VERSION = "rc"
    BUCKET = "panther-internal-rc-us-west-2"


class GA:  # pylint: disable=R0903
    """
    GA contains attributes for GA versions and where releases are stored
    """
    VERSION = "ga"
    BUCKET = "panther-enterprise-us-west-2"


@dataclass
class UpgradeVersions:  # pylint: disable=R0903
    """
    UpgradeVersions stores the latest_ga, latest_rc, and tuesday_morning_ga versions
    """
    latest_ga: VersionInfo
    latest_rc: VersionInfo
    tuesday_morning_ga: VersionInfo


class TuesdayMorningGA:  # pylint: disable=R0903
    """
    TuesdayMorningGA contains attributes for the GA version deployed every Tuesday morning
    """
    VERSION = "tuesday-morning-ga"
    BUCKET = "panther-enterprise-us-west-2"
    TARGET_FILE = "target-ga-version.txt"


class DeploymentGroup:  # pylint: disable=R0903
    """
    DeploymentGroup stores a name and version for a given group
    """

    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version


class RepoDetails:  # pylint: disable=R0903
    """
    RepoDetails stores a name, branch, and list of deployment groups
    for a GitHub repository
    """

    def __init__(self, name: str, branch: str, groups: list[DeploymentGroup]):
        self.name = name
        self.branch = branch
        self.groups = groups


class DeploymentDetails:  # pylint: disable=R0903
    """
    DeploymentDetails contains attributes that define GitHub repositories
    and deployment groups contained within each repository
    """
    groups = [
        DeploymentGroup(letter, TuesdayMorningGA.VERSION)
        for letter in string.ascii_lowercase
        if letter not in ("f", "h", "i")
    ] + [DeploymentGroup("internal", RC.VERSION)]

    STAGING = RepoDetails(
        "staging-deployments", "main",
        [DeploymentGroup("staging", RC.VERSION),
         DeploymentGroup("ga", GA.VERSION)]
    )
    HOSTED = RepoDetails("hosted-deployments", "master", groups)
    DEMO = RepoDetails("hosted-deployments", "master", [DeploymentGroup("demo", GA.VERSION)])


class DeploymentSchedule:  # pylint: disable=R0903
    """
    The DepoloymentSchedule class defines a mapping between times
    (as hours in the "America/Los_Angeles" time zone) and the groups
    to be updated during that hour

    The mapping is expressed as a nested dictionary with the hours as
    top-level keys with the days of the week as nested keys and the
    groups for each day as the values
    """

    MAPPING = {
        "07": {
            "Tuesday": ("a",),
            "Wednesday": ("n",),
            "Thursday": ("t",)
        },
        "08": {
            "Tuesday": (),
            "Wednesday": ("o",),
            "Thursday": ("u",),
        },
        "09": {
            "Tuesday": (),
            "Wednesday": ("p",),
            "Thursday": ("v",),
        },
        "10": {
            "Tuesday": ("c",),
            "Wednesday": ("q",),
            "Thursday": ("w",),
        },
        "11": {
            "Tuesday": ("j",),
            "Wednesday": ("r",),
            "Thursday": ("x",),
        },
        "12": {
            "Tuesday": ("k",),
            "Wednesday": ("s",),
            "Thursday": ("y",),
        },
        "13": {
            "Tuesday": ("m",),
            "Wednesday": (),
            "Thursday": ("z",),
        },
    }


def is_downgrade(current_version: VersionInfo, target_version: VersionInfo) -> bool:
    """
    is_downgrade checks if the target version is lower than the current version
    """
    return target_version.compare(current_version) == -1


def is_time_to_upgrade(
    scheduled_groups: list[tuple[str]], group_name: str, hour: str, day: str
) -> bool:
    """
    is_time_to_upgrade checks if a group is a scheduled group and if the group
    can be upgraded based on the current hour and day of the week
    """
    if any(group_name in group for group in scheduled_groups):
        return group_name in DeploymentSchedule.MAPPING.get(hour, {}).get(day, ())
    return True
