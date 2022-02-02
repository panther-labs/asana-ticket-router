# Copyright (C) 2022 Panther Labs Inc
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
    sprint_portfolio_id: str
    # Development sprintboards made for testing Sentry -> Asana
    sprint_portfolio_id_dev: str


INGESTION = EngTeam(team_id='1199906290951709',
                    backlog_id='1200908948600021',
                    sprint_portfolio_id='1201675315243992',
                    sprint_portfolio_id_dev='1201700591175697')
DETECTIONS = EngTeam(team_id='1199906290951721',
                     backlog_id='1200908948600035',
                     sprint_portfolio_id='1201675315243996',
                     sprint_portfolio_id_dev='1201700591175694')
INVESTIGATIONS = EngTeam(team_id='1199906290951706',
                         backlog_id='1200908948600028',
                         sprint_portfolio_id='1201675315244000',
                         sprint_portfolio_id_dev='1201700591175689')
SECURITY_IT_COMPLIANCE = EngTeam(team_id='1200813282274945',
                                 backlog_id='1200908948600049',
                                 sprint_portfolio_id='1201680804234039',
                                 sprint_portfolio_id_dev='1201700591175712')
PRODUCTIVITY = EngTeam(team_id='1201305154831711',
                       backlog_id='1201267919523628',
                       sprint_portfolio_id='1201680804234034',
                       sprint_portfolio_id_dev='1201700591175700')
QUALITY = EngTeam(team_id='1201305154831713',
                  backlog_id='1201267919523635',
                  sprint_portfolio_id='1201680804234029',
                  sprint_portfolio_id_dev='1201700591175703')
OBSERVABILITY_PERF = EngTeam(team_id='1201305154831712',
                             backlog_id='1201267919523642',
                             sprint_portfolio_id='1201680804234024',
                             sprint_portfolio_id_dev='1201700591175706')
DATA_PLATFORM = EngTeam(team_id='1201305154831715',
                        backlog_id='1201282881828563',
                        sprint_portfolio_id='1201680779826585',
                        sprint_portfolio_id_dev='1201700591175709')
CORE_PRODUCT = EngTeam(team_id='1201305154831714',
                       backlog_id='1201267919523621',
                       sprint_portfolio_id='1201675315244004',
                       sprint_portfolio_id_dev='1201700591175670')

ALL = [
    INGESTION,
    DETECTIONS,
    INVESTIGATIONS,
    SECURITY_IT_COMPLIANCE,
    PRODUCTIVITY,
    QUALITY,
    OBSERVABILITY_PERF,
    DATA_PLATFORM,
    CORE_PRODUCT
]
