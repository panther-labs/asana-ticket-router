# Copyright (C) 2020 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
from enum import Enum


class AsanaPriority(Enum):
    """Enum that represents possible enum values for the 'Priority' field in an Asana task."""
    HIGH = '1159524604627933'
    MEDIUM = '1159524604627934'
    LOW = '1159524604627935'
