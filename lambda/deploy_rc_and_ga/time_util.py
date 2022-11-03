"""
time_util contains functions related to time
"""

import os
from datetime import datetime

import pendulum
import pytz

os.environ['TZ'] = "America/Los_Angeles"


class DeployTime:  # pylint: disable=R0903
    """
    The DeployTime class contains attributes
    corresponding to the current hour, day of the week,
    and date string
    """

    def __init__(self):
        now = datetime.now(pytz.timezone('US/Pacific'))
        self.hour = now.strftime('%H')
        self.day = now.strftime('%A')
        self.date = now.strftime('%x')


def hours_passed_from_now(datetime_obj: datetime) -> int:
    """
    hours_passed_from_now returns the difference in hours from the provided
    datetime object and "now" in UTC time
    """
    pendulum_datetime = pendulum.instance(datetime_obj)
    return pendulum.now("utc").diff(pendulum_datetime).in_hours()
