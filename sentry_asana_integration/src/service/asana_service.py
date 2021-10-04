# Copyright (C) 2020 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.

import fnmatch
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from asana import Client as AsanaClient
from asana import error as AsanaError

from ..enum.asana_enum import AsanaPriority, AsanaTeam, AsanaTeamBacklogProject
from ..util.logger import get_logger

class AsanaService:
    """Service class that interacts with Asana API/entities.

    Attributes:
        _asana_client: A Client object from the Asana package, a wrapper class used to make
          API calls to Asana.
        _logger: A reference to a Logger object.
        _current_eng_sprint_project_id: The Asana ID of the Asana project representing the current
          eng sprint.
        _current_dogfooding_project_id: The Asana ID of the Asana project representing the current
          dogfooding sprint.
        _backlog_project_id: The Asana ID of the Asana project representing the backlog.
    """

    def __init__(self, asana_client: AsanaClient, load_asana_projects: bool=True) -> None:
        self._asana_client = asana_client
        self._logger = get_logger()
        self._current_eng_sprint_project_id: Optional[str] = None
        self._current_dogfooding_project_id: Optional[str] = None
        # Providing a default value to satisfy mypy; essentially, Optional[str] != str
        self._core_platform_backlog_project_id = AsanaTeamBacklogProject.CORE_PLATFORM.value
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
        self._logger.info('get_projects_response: %s', get_projects_response)

        eng_sprint_projects = []
        dogfooding_projects = []
        for proj in get_projects_response:
            if 'sprint' in proj['name'].lower() and 'template' not in proj['name'].lower() and 'closed' not in proj['name'].lower():
                eng_sprint_projects.append(proj)
            elif 'dogfooding:' in proj['name'].lower() and 'template' not in proj['name'].lower() and 'closed' not in proj['name'].lower():
                dogfooding_projects.append(proj)

        self._logger.info('The following projects are sprint related: %s', eng_sprint_projects)
        self._logger.info('The following projects are dogfooding related: %s', dogfooding_projects)

        self._current_eng_sprint_project_id = self._get_newest_created_project_id(eng_sprint_projects)
        self._current_dogfooding_project_id = self._get_newest_created_project_id(dogfooding_projects)

        self._logger.info('current eng sprint project ID: %s', self._current_eng_sprint_project_id)
        self._logger.info('current dogfooding sprint project ID: %s', self._current_dogfooding_project_id)
        self._logger.info('backlog project ID: %s', self._core_platform_backlog_project_id)

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
                self._logger.info('get_project(%s) response: %s', proj['gid'], proj_details)
                created_date = None
                if proj_details:
                    created_date = datetime.strptime(proj_details['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
                if (created_date) and (not newest_proj or not newest_proj_date or newest_proj_date < created_date):
                    newest_proj_date = created_date
                    newest_proj = proj
        return newest_proj['gid']

    def _get_project_ids(self, environment: str, level: str, owning_team: AsanaTeam) -> List[str]:
        """Retrieves the list of relevant projects for use in creating an Asana task.

        Based on the provided environment parameter, the function returns a list of project ids
        that should be used when creating a task. For dev events, the function returns the ID of
        the designated project for dev events.

        Args:
            environment: A string representing the deployment environment of the entity from which the
              Sentry event originated (i.e. dev, staging, prod).
            level: A string representing the level of the Sentry event. A distinction is made between
              'warning' vs everything else (assumed to be of greater urgency than warning).
            owning_team: An AsanaTeam Enum that represents the team that has been deemed responsible for
              triaging this event.

        Returns:
            A list containing the ids (string) of each relevant project
        """
        project_ids: List[str] = []
        if environment.lower() == 'dev':
            # Providing a default value to satisfy mypy; essentially, Optional[str] != str
            # Default value given is the Asana ID for 'Test Project (Sentry-Asana integration work)'
            return [os.environ.get('DEV_ASANA_SENTRY_PROJECT', '1200611106362920')]
        if environment.lower() == 'staging':
            if self._current_eng_sprint_project_id:
                project_ids.append(self._current_eng_sprint_project_id)
            if self._current_dogfooding_project_id:
                project_ids.append(self._current_dogfooding_project_id)
            return project_ids
        # at this point, environment == prod
        if level == 'warning':
            project_ids.append(AsanaService._get_team_backlog_project(owning_team).value)
            return project_ids
        if self._current_eng_sprint_project_id:
            project_ids.append(self._current_eng_sprint_project_id)
        return project_ids

    def create_asana_task_from_sentry_event(self, sentry_event: Dict[str, Any]) -> str:
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
            A string representing the ID (gid in Asana parlance) of the newly created Asana task
        """
        issue_url = sentry_event['issue_url']
        if issue_url[-1] == '/':
            issue_url = issue_url[:len(issue_url) - 1]
        issue_id = issue_url.split('/')[-1]
        url = f'https://sentry.io/organizations/panther-labs/issues/{issue_id}'
        customer = 'Unknown'
        server_name = 'Unknown'
        event_type = None
        for tag in sentry_event['tags']:
            if tag[0] == 'customer_name':
                customer = tag[1]
            elif tag[0] == 'server_name':
                server_name = tag[1]
            elif tag[0] == 'type':
                event_type = tag[1]
        assigned_team = AsanaService._get_owning_team(server_name, event_type)
        task_note = (f'Sentry Issue URL: {url}\n\n'
                        f'Event Datetime: {sentry_event["datetime"]}\n\n'
                        f'Customer Impacted: {customer}\n\n'
                        f'Environment: {sentry_event["environment"].lower()}\n\n')

        project_gids = self._get_project_ids(sentry_event['environment'].lower(), sentry_event['level'].lower(), assigned_team)
        if len(project_gids) == 0 or (sentry_event['environment'].lower() == 'staging' and len(project_gids) <= 1):
            project_gids.append(self._core_platform_backlog_project_id)
            task_note += 'Unable to find the sprint project; assigning to core-platform backlog.\n\n'

        task_creation_details = {
            'name': sentry_event['title'],
            'projects': project_gids,
            'custom_fields': {
                '1159524604627932': AsanaService._get_task_priority(sentry_event['level'].lower()).value,
                '1199912337121892': '1200218109698442', # Task Type: Investigate (Enum)
                '1199944595440874': 0.1,                # Estimate (d): <number>
                '1200165681182165': '1200198568911550', # Reporter: Sentry.io (Enum)
                '1199906290951705': assigned_team.value,# Team: <relevant team enum gid>: str> (Enum)
                '1200216708142306': '1200822942218893'  # Impacted: One Customer (Enum)
            },
            'notes': task_note
        }
        self._logger.info('Attempting to create Asana task with the following fields: %s', task_creation_details)
        try:
            task_creation_result = self._asana_client.tasks.create_task(task_creation_details)
            self._logger.info('Task creation result: %s', task_creation_result)
            if 'gid' not in task_creation_result:
                self._logger.error('Unable to verify that Asana task was created correctly')
                raise KeyError('Unable to verify that Asana task was created correctly')
            return task_creation_result['gid']
        except AsanaError.InvalidRequestError as ex:
            self._logger.error('Unable to create the Asana task with custom fields: %s', str(ex))

        task_note += ('Unable to create this task with all custom fields filled out due to an error with one of the fields values.\n'
                        'Please alert a team member from core-platform about this message.')
        task_creation_details = {
            'name': sentry_event['title'],
            'projects': project_gids,
            'notes': task_note
        }
        self._logger.info('Attempting to retry Asana task creation with the following minimal set of fields: %s', task_creation_details)
        task_creation_result = self._asana_client.tasks.create_task(task_creation_details)
        self._logger.info('Task creation result: %s', task_creation_result)
        if 'gid' not in task_creation_result:
            self._logger.error('Unable to verify that the second attempt to create the Asana task succeeded')
            raise KeyError('Unable to verify that the second attempt to create the Asana task succeeded')
        return task_creation_result['gid']

    @staticmethod
    def _get_task_priority(level: str) -> AsanaPriority:
        """Returns an AsanaPriority Enum based on the Sentry event level provided.

        Args:
            level: A string representing the level of the Sentry event. A distinction is made between
              'warning' vs everything else (assumed to be of greater urgency than warning).

        Returns:
            An AsanaPriority Enum representing the correct enum value for the 'Priority' field in
              the Asana task to be created.
        """
        return AsanaPriority.MEDIUM if level == 'warning' else AsanaPriority.HIGH

    @staticmethod
    def _get_team_backlog_project(team: AsanaTeam) -> AsanaTeamBacklogProject:
        """Returns the backlog project ID based on the AsanaTeam provided.

        Args:
            team: An AsanaTeam Enum representing the team for which the corresponding backlog
              ID is sought.

        Returns:
            An AsanaTeamBacklogProject Enum representing the team backlog ID corresponding to
              the AsanaTeam provided.
        """
        if team == AsanaTeam.INGESTION:
            return AsanaTeamBacklogProject.INGESTION
        if team == AsanaTeam.INVESTIGATIONS:
            return AsanaTeamBacklogProject.INVESTIGATIONS
        if team == AsanaTeam.DETECTIONS:
            return AsanaTeamBacklogProject.DETECTIONS
        if team == AsanaTeam.SECURITY_IT_COMPLIANCE:
            return AsanaTeamBacklogProject.SECURITY_IT_COMPLIANCE
        return AsanaTeamBacklogProject.CORE_PLATFORM

    # This function is used to avoid making the extra API call to Asana (GET request to the 'issue_url' in the sentry event)
    # to fetch the details of the assigned team
    @staticmethod
    def _get_owning_team(server_name: str, event_type: Optional[str] = None) -> AsanaTeam:
        """Given a server name and event type, returns the Asana team that owns it.

        Finds the Asana team that owns a given entity (currently, all these entities are Lambda functions)
        based on its 'server_name' and if present, 'type';
        both params are key/values found in the tags section of each Sentry event.
        The mappings of server_name to Asana team below is based on the assigning logic formerly in Sentry, seen here:
        https://sentry.io/settings/panther-labs/projects/panther-enterprise/ownership/

        Args:
            server_name: A string representing the 'server_name' key/value in the tags of the originating Sentry event.
            event_type: A string representing the 'type' key/value in the tags of the originating Sentry event.

        Returns:
            An AsanaTeam (enum) value representing the team that takes responsibility for the entity with
            the given 'server_name'.
        """
        if event_type and event_type.lower() == 'web':
            return AsanaTeam.CORE_PLATFORM

        server_name_to_team_map = {
            'panther-token-authorizer': AsanaTeam.CORE_PLATFORM, # former 'Web' team responsibilities fall to Core-Platform
            'panther-log-router': AsanaTeam.INGESTION,
            'panther-alert-processor': AsanaTeam.DETECTIONS,
            'panther-alert-forwarder': AsanaTeam.DETECTIONS,
            'panther-aws-event-processor': AsanaTeam.DETECTIONS,
            'panther-compliance-api': AsanaTeam.DETECTIONS,
            'panther-layer-manager': AsanaTeam.DETECTIONS,
            'panther-policy-engine': AsanaTeam.DETECTIONS,
            'panther-resource-processor': AsanaTeam.DETECTIONS,
            'panther-resources-api': AsanaTeam.DETECTIONS,
            'panther-alert-delivery-api': AsanaTeam.CORE_PLATFORM,
            'panther-analysis-api': AsanaTeam.DETECTIONS,
            'panther-cfn-custom-resources': AsanaTeam.CORE_PLATFORM,
            'panther-graph-api': AsanaTeam.CORE_PLATFORM,
            'panther-metrics-api': AsanaTeam.CORE_PLATFORM,
            'panther-organization-api': AsanaTeam.CORE_PLATFORM,
            'panther-outputs-api': AsanaTeam.CORE_PLATFORM,
            'panther-users-api': AsanaTeam.CORE_PLATFORM,
            'panther-alerts-api': AsanaTeam.INGESTION,
            'panther-message-forwarder': AsanaTeam.INGESTION,
            'panther-rules-engine': AsanaTeam.INGESTION,
            'panther-source-api': AsanaTeam.INGESTION,
            'panther-system-status': AsanaTeam.INGESTION
        }
        if server_name in server_name_to_team_map:
            return server_name_to_team_map[server_name]

        generic_server_name_to_team_lookup = [
            ('panther-athena*', AsanaTeam.INVESTIGATIONS),
            ('panther-datacatalog*', AsanaTeam.INVESTIGATIONS),
            ('panther-snowflake*', AsanaTeam.INVESTIGATIONS),
            ('panther-cloudsecurity*', AsanaTeam.DETECTIONS),
            ('panther*remediation*', AsanaTeam.DETECTIONS),
            ('panther-snapshot*', AsanaTeam.DETECTIONS),
            ('panther-cn-*', AsanaTeam.CORE_PLATFORM),
            ('panther-log*', AsanaTeam.INGESTION),
        ]

        for pattern, team in generic_server_name_to_team_lookup:
            if fnmatch.fnmatch(server_name, pattern):
                return team

        return AsanaTeam.CORE_PLATFORM
