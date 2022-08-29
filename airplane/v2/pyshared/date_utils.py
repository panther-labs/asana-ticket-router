import pendulum

_WEEK_DAY_FORMAT = 'dddd'
_DATE_FORMAT = 'YYYY-MM-DD'
_TIME_FORMAT = 'hh:mm A'
_TIME_WITH_TZ_NAME_FORMAT = f'{_TIME_FORMAT} (zz)'
_DATETIME_FORMAT = f"{_DATE_FORMAT} {_TIME_FORMAT}"
_DATETIME_WITH_TZ_NAME_FORMAT = f"{_DATE_FORMAT} {_TIME_WITH_TZ_NAME_FORMAT}"


class Timezone:
    LOCAL = "local"
    UTC = "UTC"
    PDT = "America/Los_Angeles"


def to_date_str(date_obj: pendulum.Date) -> str:
    return date_obj.format(_DATE_FORMAT)


def to_time_str(datetime_obj: pendulum.DateTime) -> str:
    return datetime_obj.format(_TIME_WITH_TZ_NAME_FORMAT)


def to_datetime_str(datetime_obj: pendulum.DateTime) -> str:
    return datetime_obj.format(_DATETIME_WITH_TZ_NAME_FORMAT)


def parse_date_str(date_string: str, tz: str = Timezone.LOCAL) -> pendulum.DateTime:
    return pendulum.from_format(date_string, _DATE_FORMAT, tz=tz)


def parse_datetime_str(datetime_string: str, tz: str = Timezone.LOCAL) -> pendulum.DateTime:
    return pendulum.from_format(datetime_string, _DATETIME_FORMAT, tz=tz)


def get_now(tz: str = Timezone.LOCAL) -> pendulum.DateTime:
    return pendulum.now(tz)


def get_now_str(tz: str = Timezone.LOCAL):
    return to_time_str(get_now(tz))


def get_today(tz: str = Timezone.LOCAL) -> pendulum.Date:
    return pendulum.today(tz)


def get_day_of_week_name(datetime_obj: pendulum.DateTime) -> str:
    return datetime_obj.format(_WEEK_DAY_FORMAT)


def get_today_str(tz: str = Timezone.LOCAL) -> str:
    return to_date_str(get_today(tz))


def get_tomorrow(tz: str = Timezone.LOCAL) -> pendulum.Date:
    return get_today(tz).add(days=1)


def get_tomorrow_str(tz: str = Timezone.LOCAL) -> str:
    return to_date_str(get_tomorrow(tz))


def is_within_past_hour(target_datetime: pendulum.DateTime) -> bool:
    target_tz = target_datetime.tz.name
    hour_ago = get_now(target_tz).subtract(hours=1)
    return get_now(target_tz) > target_datetime > hour_ago


def get_human_readable_difference(target_datetime: pendulum.DateTime, tz: str = Timezone.LOCAL) -> str:
    return get_now(tz).diff_for_humans(other=target_datetime, absolute=True)
