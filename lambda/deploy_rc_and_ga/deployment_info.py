import string
from dataclasses import dataclass
from datetime import datetime

from semver import VersionInfo


class RC:
    VERSION = "rc"
    BUCKET = "panther-internal-rc-us-west-2"


class GA:
    VERSION = "ga"
    BUCKET = "panther-enterprise-us-west-2"


@dataclass
class UpgradeVersions:
    latest_ga: VersionInfo
    latest_rc: VersionInfo
    tuesday_morning_ga: VersionInfo


class TuesdayMorningGA:
    VERSION = "tuesday-morning-ga"
    BUCKET = "panther-enterprise-us-west-2"
    TARGET_FILE = "target-ga-version.txt"


class DeploymentGroup:

    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version


class RepoDetails:

    def __init__(self, name: str, branch: str, groups: list[DeploymentGroup]):
        self.name = name
        self.branch = branch
        self.groups = groups


class DeploymentDetails:
    groups = [
                 DeploymentGroup(letter, TuesdayMorningGA.VERSION)
                 for letter in string.ascii_lowercase if letter not in ("f", "h", "i")
             ] + [DeploymentGroup("internal", RC.VERSION)]

    STAGING = RepoDetails("staging-deployments", "main",
                          [DeploymentGroup("staging", RC.VERSION),
                           DeploymentGroup("ga", GA.VERSION)])
    HOSTED = RepoDetails("hosted-deployments", "master", groups)
    DEMO = RepoDetails("hosted-deployments", "master", [DeploymentGroup("demo", GA.VERSION)])


class DeploymentSchedule:
    """
    The DepoloymentSchedule class defines a mapping between times
    (as hours in the "America/Los_Angeles" time zone) and the groups
    to be updated during that hour.

    The mapping is expressed as a nested dictionary with the hours as
    top-level keys with the days of the week as nested keys and the
    groups for each day as the values.
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


def get_time() -> tuple[str, str]:
    return datetime.today().strftime('%H'), datetime.today().strftime('%A')


def is_downgrade(current_version: VersionInfo, target_version: VersionInfo) -> bool:
    return target_version.compare(current_version) == -1


def is_time_to_upgrade(scheduled_groups: list[tuple[str]], group_name: str, hour: str, day: str) -> bool:
    if any(group_name in group for group in scheduled_groups):
        return True if group_name in DeploymentSchedule.MAPPING.get(hour, {}).get(day, ()) else False
    return True
