# Copyright (C) 2020 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.

import fnmatch
import os
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from asana import Client as AsanaClient

from .logging import get_logger


class AsanaTeam(Enum):
    """Enum that defines Panther Labs teams in Asana"""
    ANALYTICS = 'analytics'
    CLOUD_SECURITY = 'cloud-security'
    CORE_INFRA = 'core-infra'
    LOG_PROCESSING = 'log_processing'
    PANTHER_LABS = 'panther-labs'
    WEB = 'web'

class AsanaService:
    """Service class that interacts with Asana API/entities.

    Attributes:
        _asana_client: A Client object from the Asana package, a wrapper class used to make
          API calls to Asana.
        _logger: A reference to a Logger object.
        _team_leads: A dict that maps the Asana teams to the Asana IDs of their team leads.
        _current_eng_sprint_project_id: The Asana ID of the Asana project representing the current
          eng sprint.
        _current_dogfooding_project_id: The Asana ID of the Asana project representing the current
          dogfooding sprint.
        _backlog_project_id: The Asana ID of the Asana project representing the backlog.
    """

    def __init__(self, asana_client: AsanaClient, load_asana_projects: bool=True) -> None:
        self._asana_client = asana_client
        self._logger = get_logger()
        self._team_leads = {
            AsanaTeam.ANALYTICS: '1199948190610665',        # Russell
            AsanaTeam.CLOUD_SECURITY: '1199953549887297',   # Hakmiller
            AsanaTeam.CORE_INFRA: '1199946235851409',       # Angelou
            AsanaTeam.LOG_PROCESSING: '1159526576521903',   # Kostas
            AsanaTeam.PANTHER_LABS: '1199946235851409',     # Angelou (??)
            AsanaTeam.WEB: '1199946339122360'               # Aggelos
        }
        self._current_eng_sprint_project_id: Optional[str] = None
        self._current_dogfooding_project_id: Optional[str] = None
        self._backlog_project_id: Optional[str] = None
        # This flag helps keep the mocking/patching down in unit testing
        if load_asana_projects:
            self._load_asana_projects()

    def _load_asana_projects(self) -> None:
        """Retrieves the current eng sprint, dogfooding, and backlog projects & stores them in class attributes.

        This function is written as such (does not return anything, accesses protected class attributes) to allow
        the class' project_id attributes to be refreshed periodically while reducing the number of places these class
        attributes are modified.
        """
        get_projects_response = self._asana_client.projects.get_projects({
            'workspace': os.environ.get('ASANA_PANTHER_LABS_WORKSPACE_ID'),
            'team': os.environ.get('ASANA_ENGINEERING_TEAM_ID'),
            'archived': False
        })
        eng_sprint_projects = []
        backlog_projects = []
        dogfooding_projects = []
        for proj in get_projects_response:
            if 'eng sprint' in proj['name'].lower() and 'template' not in proj['name'].lower() and 'closed' not in proj['name'].lower():
                eng_sprint_projects.append(proj)
            elif 'backlog' in proj['name'].lower():
                backlog_projects.append(proj)
            elif 'dogfood' in proj['name'].lower() and 'template' not in proj['name'].lower() and 'closed' not in proj['name'].lower():
                dogfooding_projects.append(proj)

        self._current_eng_sprint_project_id = self._get_newest_created_project_id(eng_sprint_projects)
        self._current_dogfooding_project_id = self._get_newest_created_project_id(dogfooding_projects)
        self._backlog_project_id = self._get_newest_created_project_id(backlog_projects)

    def _get_newest_created_project_id(self, projects: List[Any]) -> Optional[str]:
        """Finds the most recently created project from a list of projects.

        Takes in a list of Asana projects & returns the ID of the latest project, or None if no projects were provided.

        Args:
            projects: A List of Asana projects.
              Example:
              [
                  {
                      "gid": "1200693863324521",
                      "name": "Eng Sprint 07/20 - 07/26 (old)",
                      "resource_type": "project"
                  }
              ]

        Returns:
            The 'gid' field (string) of the most recently created Asana project if the list of projects
            was non-empty.

            If the list of projects passed to the function was empty, then the function returns None.
        """
        if len(projects) == 0:
            return None
        newest_proj = projects[0]
        newest_proj_date = None
        if len(projects) > 1:
            for proj in projects:
                proj_details = self._asana_client.projects.get_project(proj['gid'])
                created_date = None
                if proj_details and 'data' in proj_details:
                    created_date = datetime.strptime(proj_details['data']['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
                if (created_date) and (not newest_proj or not newest_proj_date or newest_proj_date < created_date):
                    newest_proj_date = created_date
                    newest_proj = proj
        return newest_proj['gid']

    def _get_project_ids(self, environment: str) -> List[str]:
        """Retrieves the list of relevant projects for use in creating an Asana task.

        Based on the provided environment parameter, the function returns a list of project ids
        that should be used when creating a task. For dev events, the function returns the ID of
        the designated project for dev events.

        Args:
            environment: A string representing the deployment environment of the entity from which the
              Sentry event originated (i.e. dev, staging, prod).

        Returns:
            A list containing the ids (string) of each relevant project
        """
        project_ids: List[str] = []
        # the backup value is the project ID for 'Test Project (Sentry-Asana integration work)'
        if environment.lower() == 'dev':
            return [os.environ.get('DEV_ASANA_SENTRY_PROJECT', '1200611106362920')]
        if self._current_eng_sprint_project_id:
            project_ids.append(self._current_eng_sprint_project_id)
        if environment.lower() == 'staging' and self._current_dogfooding_project_id:
            project_ids.append(self._current_dogfooding_project_id)
        if len(project_ids) < 1:
            if self._backlog_project_id:
                project_ids.append(self._backlog_project_id)
        return project_ids

    def create_asana_task_from_sentry_event(self, sentry_event: Dict[str, Any]) -> None:
        """Extracts relevant info from the Sentry event & creates an Asana task using the Asana client.

        This method receives the Sentry event information and proceeds to make the relevant calls
        to the various private/protected methods in this class (some of which in turn make calls
        to the Asana API), contruct the dict that contains the info needed to create the Asana
        task in the appropriate project assigned to the appropriate person, and finally call the
        Asana API to create the task.

        Args:
            sentry_event: A dict representing the sentry event; this event can be found from the deserialized body in the
              originating event through the following keys: data -> event. See 'tests/test_data/sentry_event_body.json'
              for an example of the deserialized body.

        Returns:
            None
        """
        url = sentry_event['url']
        timestamp = sentry_event['timestamp']
        title = sentry_event['title']
        environment = sentry_event['environment'].lower()
        tags = sentry_event['tags']
        customer = 'Unknown'
        server_name = 'Unknown'
        for tag in tags:
            if tag[0] == 'customer_name':
                customer = tag[1]
            elif tag[0] == 'server_name':
                server_name = tag[1]
        assigned_team = AsanaService._get_owning_team(server_name)
        assignee = self._get_team_lead_id(assigned_team, environment)
        project_gids = self._get_project_ids(environment)
        task_creation_details = {
            'assignee': assignee,
            'name': title,
            'projects': project_gids,
            'notes': f'Sentry Issue URL: {url}\nEvent Timestamp: {timestamp}\nCustomer Impacted: {customer}'
        }
        self._asana_client.tasks.create_task(task_creation_details)

    def _get_team_lead_id(self, team: AsanaTeam, environment: Optional[str]=None) -> str:
        """Given an Asana team, returns the Asana ID of its team lead.

        Args:
            team: An AsanaTeam (enum) value representing a single Asana team.
            environment: Optional; If supplied and the value is 'dev', the designated dev team lead ID will
              be returned.

        Returns:
            A string representing the ID of the team lead for the AsanaTeam in question
        """
        if environment and environment.lower() == 'dev':
            return os.environ.get('DEV_TEAM_LEAD_ID', '1200567447162380') # Current backup value is Yusuf's ID
        return self._team_leads[team]

    # This function is used to avoid making the extra API call to Asana (GET request to the 'issue_url' in the sentry event)
    # to fetch the details of the assigned team
    @staticmethod
    def _get_owning_team(server_name: str) -> AsanaTeam:
        """Given a server name, returns the Asana team that owns it.

        Finds the Asana team that owns a given entity (currently, all these entities are Lambda functions)
        based on its 'server_name' - a tag found in the tags section of each Sentry event. The mappings of
        server_name to Asana team below is based on the Confluence document on 'Service Owners' found here:
        https://panther-labs.atlassian.net/wiki/spaces/OPS/pages/1250492812/Service+Owners.

        Args:
            server_name: A string representing the 'server_name' value found in the originating Sentry event.

        Returns:
            An AsanaTeam (enum) value representing the team that takes responsibility for the entity with
            the given 'server_name'.
        """
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
