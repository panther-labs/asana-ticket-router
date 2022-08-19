# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.

from enum import Enum, auto


class AlertType(Enum):
    """Enum of Alert Types"""

    DATADOG = auto()
    SENTRY = auto()
    UNKNOWN_ALERT = auto()


# Datadog doesn't really support custom source types other than this one?
# https://docs.datadoghq.com/events/guides/new_events_sources/
DATADOG_SOURCE_TYPE = 'my_apps'
