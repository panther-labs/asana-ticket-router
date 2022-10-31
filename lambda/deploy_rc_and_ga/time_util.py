"""
time_util contains functions related to time
"""

from datetime import datetime

import pendulum


def hours_passed_from_now(datetime_obj: datetime) -> int:
    """
    hours_passed_from_now returns the difference in hours from the provided
    datetime object and "now" in UTC time
    """
    pendulum_datetime = pendulum.instance(datetime_obj)
    return pendulum.now("utc").diff(pendulum_datetime).in_hours()


def get_time() -> tuple[str, str]:
    """
    get_time returns the hour and day of the week
    """
    return datetime.today().strftime('%H'), datetime.today().strftime('%A')
