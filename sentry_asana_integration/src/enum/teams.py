# Copyright (C) 2020 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
from dataclasses import dataclass


@dataclass
class EngTeam:
    """Asana IDs for the team and its associated backlog."""
    team_id: str
    backlog_id: str


INGESTION = EngTeam(team_id='1199906290951709', backlog_id='1200908948600021')
DETECTIONS = EngTeam(team_id='1199906290951721', backlog_id='1200908948600035')
INVESTIGATIONS = EngTeam(team_id='1199906290951706',
                         backlog_id='1200908948600028')
SECURITY_IT_COMPLIANCE = EngTeam(team_id='1200813282274945',
                                 backlog_id='1200908948600049')
PRODUCTIVITY = EngTeam(team_id='1201305154831711',
                       backlog_id='1201267919523628')
QUALITY = EngTeam(team_id='1201305154831713', backlog_id='1201267919523635')
OBSERVABILITY_PERF = EngTeam(team_id='1201305154831712',
                             backlog_id='1201267919523642')
DATA_PLATFORM = EngTeam(team_id='1201305154831715',
                        backlog_id='1201282881828563')
CORE_PRODUCT = EngTeam(team_id='1201305154831714',
                       backlog_id='1201267919523621')
