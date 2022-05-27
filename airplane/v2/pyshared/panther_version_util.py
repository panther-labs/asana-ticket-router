import semver


def _trim_v_prefix(version: str):
    return version[1:] if version.startswith('v') else version


def to_semver(version: str) -> semver.VersionInfo:
    semver_str = _trim_v_prefix(version)
    return semver.VersionInfo.parse(semver_str)


def is_valid_bump(old_version: semver.VersionInfo, new_version: semver.VersionInfo) -> bool:
    is_newer_version = new_version > old_version
    # Major version is one greater and minor is 0
    is_valid_major = new_version.major == old_version.bump_major().major and new_version.minor == 0
    # Minor version is the same or one greater
    is_valid_minor = new_version.minor in [old_version.minor, old_version.bump_minor().minor]
    return is_newer_version and (is_valid_major or is_valid_minor)
