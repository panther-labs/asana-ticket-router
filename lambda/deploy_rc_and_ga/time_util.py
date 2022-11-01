"""
time_util contains functions related to time
"""

import os
from datetime import datetime

import pendulum
import pytz

os.environ['TZ'] = "America/Los_Angeles"


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
    hour = datetime.now(pytz.timezone('US/Pacific')).strftime('%H')
    day = datetime.now(pytz.timezone('US/Pacific')).strftime('%A')
    print(f"Hour: {hour}, Day: {day}")
    return hour, day
