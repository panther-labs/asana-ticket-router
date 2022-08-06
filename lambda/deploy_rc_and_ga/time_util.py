import datetime

import pendulum


def hours_passed_from_now(datetime_obj: datetime.datetime):
    pendulum_datetime = pendulum.instance(datetime_obj)
    return pendulum.now("utc").diff(pendulum_datetime).in_hours()
