import pendulum
from ruamel.yaml import comments

from v2.pyshared.date_utils import parse_datetime_str, is_within_past_hour, Timezone
from v2.pyshared.panther_version_util import to_semver, is_valid_bump
from v2.pyshared.yaml_utils import is_comment_in_yaml_file, add_top_level_comment

DEPLOYMENT_VERSION_COMMENT_PLACEHOLDER = "Version:"
DEPLOYMENT_TIME_COMMENT_PLACEHOLDER = "Deployment Time:"
DEPLOYMENT_TIMEZONE_PLACEHOLDER = "(PDT)"


def generate_deployment_schedule_str(deployment_version: str, deployment_time: str):
    return f"{DEPLOYMENT_VERSION_COMMENT_PLACEHOLDER} {deployment_version}\n" \
           f"{DEPLOYMENT_TIME_COMMENT_PLACEHOLDER} {deployment_time}"


def get_deployment_time(comment: str) -> str or None:
    if comment.startswith(DEPLOYMENT_TIME_COMMENT_PLACEHOLDER):
        return comment.removeprefix(DEPLOYMENT_TIME_COMMENT_PLACEHOLDER).strip()


def get_deployment_version(comment: str) -> str or None:
    if comment.startswith(DEPLOYMENT_VERSION_COMMENT_PLACEHOLDER):
        return comment.removeprefix(DEPLOYMENT_VERSION_COMMENT_PLACEHOLDER).strip()


def remove_timezone_placeholder(deployment_time: str) -> str:
    return deployment_time.removesuffix(DEPLOYMENT_TIMEZONE_PLACEHOLDER).strip()


def parse_deployment_schedule(comments: list[str]) -> tuple[str, str]:
    deployment_time = ""
    deployment_version = ""
    for comment in comments:
        if not deployment_time:
            deployment_time = get_deployment_time(comment)
        if not deployment_version:
            deployment_version = get_deployment_version(comment)
    if not deployment_time:
        raise ValueError(f"Unable to get the deployment time from following comments: {comments}")
    if not deployment_version:
        raise ValueError(f"Unable to get the deployment version from following comments: {comments}")
    return deployment_time, deployment_version


def parse_deployment_time(deployment_time: str) -> pendulum.DateTime:
    deployment_time = remove_timezone_placeholder(deployment_time)
    return parse_datetime_str(deployment_time, tz=Timezone.PDT)


def is_due_deployment(deployment_time: str) -> bool:
    parsed_deployment_time = parse_deployment_time(deployment_time)
    return is_within_past_hour(parsed_deployment_time)


def update_group_deployment_schedule(deployment_group_yaml: comments.CommentedMap, version: str, time: str) -> None:
    deployment_schedule_str = generate_deployment_schedule_str(version, time)
    add_top_level_comment(deployment_schedule_str, deployment_group_yaml)


def contains_deployment_schedule(deployment_group_yaml: comments.CommentedMap) -> bool:
    """
    Check if top-level comments contain the deployment schedule
    :param deployment_group_yaml: Deployment group config file
    :return: bool
    """
    return is_comment_in_yaml_file(DEPLOYMENT_VERSION_COMMENT_PLACEHOLDER, deployment_group_yaml) \
           and is_comment_in_yaml_file(DEPLOYMENT_TIME_COMMENT_PLACEHOLDER, deployment_group_yaml)


def validate_deployment_time(group: str, deployment_time: str):
    parsed_deployment_time = parse_deployment_time(deployment_time)
    if parsed_deployment_time.is_past():
        raise AttributeError(f"Group '{group}': {deployment_time} is a past time.")


def validate_deployment_version(group: str, old_version: str, new_version: str) -> None:
    old_semver = to_semver(old_version)
    new_semver = to_semver(new_version)
    if not is_valid_bump(old_semver, new_semver):
        raise AttributeError(f"Group '{group}': new version '{new_version}' is not a valid bump from '{old_version}'.")
