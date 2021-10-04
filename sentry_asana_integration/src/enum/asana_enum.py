# Copyright (C) 2020 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.

from enum import Enum


class AsanaTeam(Enum):
    """Enum that represents possible enum values for the 'Team' field in an Asana task."""
    INGESTION = '1199906290951709'
    DETECTIONS = '1199906290951721'
    INVESTIGATIONS = '1199906290951706'
    CORE_PLATFORM = '1199906290951724'
    SECURITY_IT_COMPLIANCE = '1200813282274945'

class AsanaPriority(Enum):
    """Enum that represents possible enum values for the 'Priority' field in an Asana task."""
    HIGH = '1159524604627933'
    MEDIUM = '1159524604627934'
    LOW = '1159524604627935'

class AsanaTeamBacklogProject(Enum):
    """Enum that represents the gids of each engineering teams backlog."""
    INGESTION = '1200908948600021'
    DETECTIONS = '1200908948600035'
    INVESTIGATIONS = '1200908948600028'
    CORE_PLATFORM = '1200908948600042'
    SECURITY_IT_COMPLIANCE = '1200908948600049'
