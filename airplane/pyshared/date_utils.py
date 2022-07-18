import datetime

DATE_FORMAT = '%Y-%m-%d'

def generate_utc_timestamp():
    d = datetime.datetime.now(tz=datetime.timezone.utc)
    return d.strftime('%Y-%m-%dT%H:%M:%SZ')

def generate_utc_expiry_timestamp(expiry_hours):
    d = datetime.datetime.now(tz=datetime.timezone.utc)
    d = d + datetime.timedelta(hours=expiry_hours)
    return d.strftime('%Y-%m-%dT%H:%M:%SZ')

def to_date_str(date: datetime.date) -> str:
    return date.strftime(DATE_FORMAT)


def parse_date_str(date_string: str) -> datetime.date:
    return datetime.datetime.strptime(date_string, DATE_FORMAT)


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
