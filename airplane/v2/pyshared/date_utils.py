import datetime

DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = f'{DATE_FORMAT} %I:%M %p'


def to_date_str(date: datetime.date) -> str:
    return date.strftime(DATE_FORMAT)


def parse_date_str(date_string: str) -> datetime.date:
    return datetime.datetime.strptime(date_string, DATE_FORMAT)


def parse_datetime_str(datetime_string: str) -> datetime.datetime:
    return datetime.datetime.strptime(datetime_string, DATETIME_FORMAT)


def get_now() -> datetime.datetime:
    return datetime.datetime.now()


def get_today() -> datetime.date:
    return datetime.date.today()


def get_today_str() -> str:
    return to_date_str(get_today())


def get_tomorrow() -> datetime.date:
    return get_today() + datetime.timedelta(days=1)


def get_tomorrow_str() -> str:
    return to_date_str(get_tomorrow())


def is_past_date(target_date: datetime.date) -> bool:
    return target_date < datetime.datetime.now()


def is_within_current_hour(target_datetime: datetime.datetime) -> bool:
    return get_now().date() == target_datetime.date() and get_now().hour == target_datetime.hour
