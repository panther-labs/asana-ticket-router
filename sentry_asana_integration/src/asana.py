# Copyright (C) 2020 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.

import fnmatch
from enum import Enum
from typing import Any, List, Optional

from .logging import get_logger


class AsanaTeam(Enum):
    """Enum that defines Panther Labs teams in Asana"""
    ANALYTICS = 'analytics'
    CLOUD_SECURITY = 'cloud-security'
    CORE_INFRA = 'core-infra'
    LOG_PROCESSING = 'log_processing'
    PANTHER_LABS = 'panther-labs'
    WEB = 'web'

    @staticmethod
    def list() -> List[str]:
        """Returns all Enum values as a list"""
        return list(map(lambda c: c.value, AsanaTeam))

class AsanaService:
    """Service class that interacts with Asana API/entities"""

    def __init__(self, asana_client: Any) -> None:
        self._asana_client = asana_client
        self._logger = get_logger()
        self.team_leads = {
            AsanaTeam.ANALYTICS: '1199948190610665',        # Russell
            AsanaTeam.CLOUD_SECURITY: '1199953549887297',   # Hakmiller
            AsanaTeam.CORE_INFRA: '1199946235851409',       # Angelou
            AsanaTeam.LOG_PROCESSING: '1159526576521903',   # Kostas
            AsanaTeam.PANTHER_LABS: '1199946235851409',     # Angelou (??)
            AsanaTeam.WEB: '1199946339122360'               # Aggelos
        }

    def get_team_lead_id(self, team: AsanaTeam, environment: Optional[str]=None) -> str:
        """Given an Asana team, returns the Asana ID of its team lead"""
        if environment and environment.lower() == 'dev':
            return '1200567447162380' # Yusuf
        return self.team_leads[team]

    # This function is used to avoid making the extra API call to Asana (GET request to the 'issue_url' in the sentry event)
    # to fetch the details of the assigned team
    @staticmethod
    def get_owning_team(server_name: str) -> AsanaTeam:
        """Given a server name, return the Asana team that owns it"""
        server_name_to_team_map = {
            'panther-log-router': AsanaTeam.ANALYTICS,
            'panther-alert-processor': AsanaTeam.CLOUD_SECURITY,
            'panther-alert-forwarder': AsanaTeam.CLOUD_SECURITY,
            'panther-aws-event-processor': AsanaTeam.CLOUD_SECURITY,
            'panther-compliance-api': AsanaTeam.CLOUD_SECURITY,
            'panther-layer-manager': AsanaTeam.CLOUD_SECURITY,
            'panther-policy-engine': AsanaTeam.CLOUD_SECURITY,
            'panther-resource-processor': AsanaTeam.CLOUD_SECURITY,
            'panther-resources-api': AsanaTeam.CLOUD_SECURITY,
            'panther-alert-delivery-api': AsanaTeam.CORE_INFRA,
            'panther-analysis-api': AsanaTeam.CORE_INFRA,
            'panther-cfn-custom-resources': AsanaTeam.CORE_INFRA,
            'panther-graph-api': AsanaTeam.CORE_INFRA,
            'panther-metrics-api': AsanaTeam.CORE_INFRA,
            'panther-organization-api': AsanaTeam.CORE_INFRA,
            'panther-outputs-api': AsanaTeam.CORE_INFRA,
            'panther-users-api': AsanaTeam.CORE_INFRA,
            'panther-alerts-api': AsanaTeam.LOG_PROCESSING,
            'panther-message-forwarder': AsanaTeam.LOG_PROCESSING,
            'panther-rules-engine': AsanaTeam.LOG_PROCESSING,
            'panther-source-api': AsanaTeam.LOG_PROCESSING,
            'panther-system-status': AsanaTeam.LOG_PROCESSING
        }
        if server_name in server_name_to_team_map:
            return server_name_to_team_map[server_name]

        generic_server_name_to_team_lookup = [
            ('panther-athena*', AsanaTeam.ANALYTICS),
            ('panther-datacatalog*', AsanaTeam.ANALYTICS),
            ('panther-snowflake*', AsanaTeam.ANALYTICS),
            ('panther-cloudsecurity*', AsanaTeam.CLOUD_SECURITY),
            ('panther*remediation*', AsanaTeam.CLOUD_SECURITY),
            ('panther-snapshot*', AsanaTeam.CLOUD_SECURITY),
            ('panther-cn-*', AsanaTeam.CORE_INFRA),
            ('panther-log*', AsanaTeam.LOG_PROCESSING),
        ]

        for pattern, team in generic_server_name_to_team_lookup:
            if fnmatch.fnmatch(server_name, pattern):
                return team

        return AsanaTeam.PANTHER_LABS
