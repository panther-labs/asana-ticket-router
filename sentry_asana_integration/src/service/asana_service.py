# Copyright (C) 2020 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.

import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from asana import Client as AsanaClient
from asana import error as AsanaError

from ..enum import teams
from ..enum.priority import AsanaPriority
from ..util.logger import get_logger

# A list of hardcoded Account IDs for our self hosted customers, as extracted via
# https://github.com/panther-labs/aws-management-cloudformation/blob/master/panther-public/enterprise-accounts.yml
SELF_HOSTED_ACCOUNTS_IDS = [
    '880172401261',  # Grail,

    '346666025108',  # Infoblox IT,
    '405093580753',  # Infoblox dev,
    '718190095844',  # Infoblox prod,

    '971535947767',  # Coinbase dev
    '817873525313',  # Coinbase prod
]

# Pulumi config setting will be "1" or "0" string, but account for full string
devEnv = os.environ.get('DEVELOPMENT', '').lower()
IS_LOCAL_DEV = False
if devEnv in ['1', 'true']:
    IS_LOCAL_DEV = True


def filter_projects(project_name: str) -> bool:
    """Filters a list of asana projects from common unwanted projects
    """
    if 'template' not in project_name and 'complete' not in project_name and 'closed' not in project_name:
        return True
    return False


class AsanaService:
    """Service class that interacts with Asana API/entities.

    Attributes:
        _asana_client: A Client object from the Asana package, a wrapper class used to make
          API calls to Asana.
        _logger: A reference to a Logger object.
        _current_eng_sprint_project_ids: The Asana ID of the Asana project representing the current
          eng sprint.
        _current_release_testing_project_id: The Asana ID of the Asana project representing the current
          release testing sprint.
    """

    # These teams are responsible for the initial triage of any issues reported by their services, but it does not
    # necessarily mean that they officially "own" the service - they can delegate as needed.
    _SERVER_TEAM_MAPPING = {
        # Team: Detection
        'panther-alert-delivery-api': teams.DETECTIONS,
        'panther-analysis-api': teams.DETECTIONS,
        'panther-aws-event-processor': teams.DETECTIONS,
        'panther-cloudsecurity-datalake-forwarder': teams.DETECTIONS,
        'panther-compliance-api': teams.DETECTIONS,
        'panther-layer-manager': teams.DETECTIONS,
        'panther-log-alert-forwarder': teams.DETECTIONS,
        'panther-outputs-api': teams.DETECTIONS,
        'panther-policy-engine': teams.DETECTIONS,
        'panther-resource-processor': teams.DETECTIONS,
        'panther-resources-api': teams.DETECTIONS,
        'panther-snapshot-pollers': teams.DETECTIONS,
        'panther-snapshot-scheduler': teams.DETECTIONS,

        # Team: Ingestion
        'panther-alerts-api': teams.INGESTION,
        'panther-cloud-puller': teams.INGESTION,
        'panther-data-archiver': teams.INGESTION,
        'panther-holding-tank': teams.INGESTION,
        'panther-log-processor': teams.INGESTION,
        'panther-log-puller': teams.INGESTION,
        'panther-log-router': teams.INGESTION,
        'panther-logtypes-api': teams.INGESTION,
        'panther-message-forwarder': teams.INGESTION,
        'panther-rules-engine': teams.INGESTION,
        'panther-source-api': teams.INGESTION,
        'panther-system-status': teams.INGESTION,

        # Team: Investigation
        'panther-athena-admin-api': teams.INVESTIGATIONS,
        'panther-athena-api': teams.INVESTIGATIONS,
        'panther-database-workflow': teams.INVESTIGATIONS,
        'panther-datacatalog-compactor': teams.INVESTIGATIONS,
        'panther-datacatalog-compactor-callbacks': teams.INVESTIGATIONS,
        'panther-datacatalog-compactor-reaper': teams.INVESTIGATIONS,
        'panther-datacatalog-updater': teams.INVESTIGATIONS,
        'panther-lookup-tables-api': teams.INVESTIGATIONS,
        'panther-snowflake-admin-api': teams.INVESTIGATIONS,
        'panther-snowflake-api': teams.INVESTIGATIONS,

        # Team: Core Product
        'panther-apitoken-authorizer': teams.CORE_PRODUCT,
        'panther-cfn-custom-resources': teams.CORE_PRODUCT,
        'panther-cn-router': teams.CORE_PRODUCT,
        'panther-graph-api': teams.CORE_PRODUCT,
        'panther-metrics-api': teams.CORE_PRODUCT,
        'panther-ops-tools': teams.CORE_PRODUCT,
        'panther-organization-api': teams.CORE_PRODUCT,
        'panther-pip-layer-builder': teams.CORE_PRODUCT,
        'panther-token-authorizer': teams.CORE_PRODUCT,
        'panther-users-api': teams.CORE_PRODUCT,
    }

    def __init__(self, asana_client: AsanaClient, load_asana_projects: bool = True) -> None:
        self._asana_client = asana_client
        self._logger = get_logger()
        # Store a map of current sprints per team { <team>: <current sprint> }
        self._current_eng_sprint_project_ids: Dict[str, Optional[str]] = {}
        self._current_release_testing_project_id: Optional[str] = None
        # This flag helps keep the mocking/patching down in unit testing
        if load_asana_projects:
            self._load_asana_projects()

    def _get_relevant_projects(self, portfolio_gid: Optional[str]) -> List[Any]:
        """Retrieves all projects inside a specific portfolio and filters non-relevant projects

        Parameters
        ----------
        portfolio_gid : {Gid} The portfolio from which to get the list of items.
        """

        if portfolio_gid is None:
            return []
        projects = self._asana_client.portfolios.get_items(portfolio_gid)
        self._logger.debug('Got projects from portfolio: %s', projects)
        return list(filter(lambda proj: filter_projects(proj['name'].lower()), projects))

    def _load_asana_team_sprint_projects(self) -> None:
        """Retrieves the current eng sprint for each team and stores them in a class attribute
        """
        for team in teams.ALL:
            self._logger.debug(
                'Searching for projects in portfolio: %s', team.sprint_portfolio_id)

            # If we're in local dev, use the development sprints
            projects = []
            if IS_LOCAL_DEV:
                projects = self._get_relevant_projects(
                    team.sprint_portfolio_id_dev)
            else:
                projects = self._get_relevant_projects(
                    team.sprint_portfolio_id)
            self._logger.debug('Got projects for team: %s', projects)
            current_sprint_id = self._get_newest_created_project_id(projects)
            self._logger.debug(
                'Got newest project for team: %s', current_sprint_id)
            self._current_eng_sprint_project_ids[team.team_id] = current_sprint_id

        self._logger.debug('current eng sprints: %s',
                           self._current_eng_sprint_project_ids)

    def _load_asana_release_testing_projects(self, project_gid: str) -> None:
        """Retrieves the current release testing projects and stores them in a class attribute.
        """
        release_testing_projects = self._get_relevant_projects(project_gid)
        self._logger.debug(
            'The following projects are release testing related: %s', release_testing_projects)
        self._current_release_testing_project_id = self._get_newest_created_project_id(
            release_testing_projects)
        self._logger.debug('current release testing sprint project ID: %s',
                           self._current_release_testing_project_id)

    def _load_asana_projects(self) -> None:
        """Initializes class attributes with a set of projects that are used throughout the lifetime of the lambda

        This function is written as such (does not return anything, accesses protected class attributes) to allow
        the class' project_id attributes to be refreshed periodically while reducing the number of places these class
        attributes are modified.
        """
        self._load_asana_team_sprint_projects()
        self._load_asana_release_testing_projects(
            os.environ.get('RELEASE_TESTING_PORTFOLIO', ''))

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
                proj_details = self._asana_client.projects.get_project(
                    proj['gid'])
                self._logger.debug(
                    'get_project(%s) response: %s', proj['gid'], proj_details)
                created_date = None
                if proj_details:
                    created_date = datetime.strptime(
                        proj_details['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
                if created_date and (not newest_proj or not newest_proj_date or newest_proj_date < created_date):
                    newest_proj_date = created_date
                    newest_proj = proj
        return newest_proj['gid']

    def _get_project_ids(self, environment: str, level: str, owning_team: teams.EngTeam) -> List[str]:
        """Retrieves the list of relevant projects for use in creating an Asana task.

        Based on the provided environment parameter, the function returns a list of project ids
        that should be used when creating a task. For dev events, the function returns the ID of
        the designated project for dev events.

        Args:
            environment: A string representing the deployment environment of the entity from which the
              Sentry event originated (i.e. dev, staging, prod).
            level: A string representing the level of the Sentry event. A distinction is made between
              'warning' vs everything else (assumed to be of greater urgency than warning).
            owning_team: The team responsible for triaging this event.

        Returns:
            A list containing the ids (string) of each relevant project
        """
        project_ids: List[str] = []

        # If running in local dev, only do the following
        if IS_LOCAL_DEV:
            # These should be development sprintboards defined by the env flag
            current_sprint_id = self._current_eng_sprint_project_ids.get(
                owning_team.team_id)
            if current_sprint_id is not None:
                project_ids.append(current_sprint_id)

            # Add to the dev asana project board for easier grouping (and bulk deletion)
            project_ids.append(os.environ.get('DEV_ASANA_SENTRY_PROJECT', ''))
            return project_ids

        # Sentry events can come from a specific environment. Not to be
        # confused with __this__ lambda's environment.
        environment = environment.lower()
        if environment == 'dev':
            # These should be development sprintboards defined by the env flag
            current_sprint_id = self._current_eng_sprint_project_ids.get(
                owning_team.team_id)
            if current_sprint_id is not None:
                project_ids.append(current_sprint_id)

            # Add to the dev asana project board for easier grouping (and bulk deletion)
            project_ids.append(os.environ.get('DEV_ASANA_SENTRY_PROJECT', ''))
            return project_ids
        if environment == 'staging':
            current_sprint_id = self._current_eng_sprint_project_ids.get(
                owning_team.team_id)
            if current_sprint_id is not None:
                project_ids.append(current_sprint_id)
            if self._current_release_testing_project_id:
                project_ids.append(self._current_release_testing_project_id)
            return project_ids
        # at this point, environment == prod
        if level == 'warning':
            project_ids.append(owning_team.backlog_id)
            return project_ids
        current_sprint_id = self._current_eng_sprint_project_ids.get(
            owning_team.team_id)
        if current_sprint_id is not None:
            project_ids.append(current_sprint_id)
        return project_ids

    def extract_root_asana_link(self, task_gid: str) -> Optional[str]:
        """Extract the 'Root Asana Task: ...' link from the specified task (if it exists)

        Args:
            task: The asana task payload returned from the client

        Returns:
            The root asana task link
        """
        try:
            task = self._asana_client.tasks.find_by_id(task_gid)
            if not task:
                self._logger.error('Could not fetch task: %s', task_gid)
                return None
        except AsanaError.AsanaError as ex:
            self._logger.error('Unknown asana error: %s', ex)
            return None
        else:
            notes = task.get('notes', None)
            if not notes:
                self._logger.error(
                    'Could not find notes in task: %s', task_gid)
                return None

            parser = re.compile(
                r"(Root Asana Task: )(https:\/\/app.asana.com\/\d+\/\d+\/\d+)")
            match = parser.search(notes)
            if not match:
                self._logger.debug('No root asana task link found')
                return None

            prev_link = match.group(2)
            if not prev_link:
                self._logger.error('Malformed root asana task link')
                return None

            return prev_link

    # pylint: disable=too-many-branches,too-many-statements
    def create_asana_task_from_sentry_event(
            self,
            sentry_event: Dict[str, Any],
            prev_asana_link: Optional[str],
            root_asana_link: Optional[str]
    ) -> str:
        """Extracts relevant info from the Sentry event & creates an Asana task using the Asana client.

        This method receives the Sentry event information and proceeds to make the relevant calls
        to the various private/protected methods in this class (some of which in turn make calls
        to the Asana API), contruct the dict that contains the info needed to create the Asana
        task in the appropriate project assigned to the appropriate person, and finally call the
        Asana API to create the task.

        Args:
            sentry_event: A dict representing the sentry event; this event can be found from the deserialized body in
              the originating event through the following keys: data -> event.
              See 'tests/test_data/sentry_event_body.json' for an example of the deserialized body.
            prev_asana_link: An optional link pointing to the previous asana task.
            root_asana_link: An optional link pointing to the first (root) asana task created for the sentry issue.

        Returns:
            A string representing the ID (gid in Asana parlance) of the newly created Asana task
        """
        issue_url = sentry_event.get('issue_url', '')
        issue_id = issue_url.strip('/').split('/').pop()
        url = f'https://sentry.io/organizations/panther-labs/issues/{issue_id}'
        customer = 'Unknown'
        server_name = 'Unknown'
        event_type = None
        aws_region = None
        aws_account_id = None
        for tag in sentry_event['tags']:
            key = tag[0]
            value = tag[1]
            if key == 'customer_name':
                customer = value
            elif key == 'server_name':
                server_name = value
            elif key == 'type':
                event_type = value
            elif key == 'aws_region':
                aws_region = value
            elif key == 'aws_account_id':
                aws_account_id = value
        assigned_team = AsanaService._get_owning_team(server_name, event_type)
        task_note = (f'Sentry Issue URL: {url}\n\n'
                     f'Event Datetime: {sentry_event["datetime"]}\n\n'
                     f'Customer Impacted: {customer}\n\n'
                     f'Environment: {sentry_event["environment"].lower()}\n\n')

        # if a customer is not self-hosted, add a switch role link
        if aws_account_id not in SELF_HOSTED_ACCOUNTS_IDS:
            task_note = task_note + (f'AWS Switch Role Link: https://{aws_region}.signin.aws.amazon.com/switchrole'
                                     f'?roleName=PantherSupportRole-{aws_region}'
                                     f'&account={aws_account_id}'
                                     f'&displayName={customer}%20Support\n\n'
                                     )
        # If we had a root task link, set it in the payload
        if root_asana_link:
            task_note = f'Root Asana Task: {root_asana_link}\n\n' + task_note
        # If we had a previous task link, set it in the payload
        if prev_asana_link:
            task_note = f'Previous Asana Task: {prev_asana_link}\n\n' + task_note

        project_gids = self._get_project_ids(sentry_event['environment'].lower(), sentry_event['level'].lower(),
                                             assigned_team)
        if len(project_gids) == 0 or (sentry_event['environment'].lower() == 'staging' and len(project_gids) <= 1):
            project_gids.append(teams.CORE_PRODUCT.backlog_id)
            task_note += 'Unable to find the sprint project; assigning to core product backlog.\n\n'

        task_creation_details = {
            'name': sentry_event['title'],
            'projects': project_gids,
            'custom_fields': {
                '1159524604627932': AsanaService._get_task_priority(sentry_event['level'].lower()).value,
                # Task Type: Investigate (Enum)
                '1199912337121892': '1200218109698442',
                '1199944595440874': 0.1,  # Estimate (d): <number>
                # Reporter: Sentry.io (Enum)
                '1200165681182165': '1200198568911550',
                # Team: <relevant team enum gid>: str> (Enum)
                '1199906290951705': assigned_team.team_id,
                # Impacted: One Customer (Enum)
                '1200216708142306': '1200822942218893'
            },
            'notes': task_note
        }
        self._logger.debug(
            'Attempting to create Asana task with the following fields: %s', task_creation_details)
        try:
            task_creation_result = self._asana_client.tasks.create_task(
                task_creation_details)
            self._logger.debug('Task creation result: %s',
                               task_creation_result)
            if 'gid' not in task_creation_result:
                self._logger.error(
                    'Unable to verify that Asana task was created correctly')
                raise KeyError(
                    'Unable to verify that Asana task was created correctly')
            return task_creation_result['gid']
        except AsanaError.InvalidRequestError as ex:
            self._logger.error(
                'Unable to create the Asana task with custom fields: %s', str(ex))

        task_note += ('Unable to create this task with all custom fields filled out.'
                      ' Please alert a team member from observability about this message.')
        task_creation_details = {
            'name': sentry_event['title'],
            'projects': project_gids,
            'notes': task_note
        }
        self._logger.debug('Attempting to retry Asana task creation with the following minimal set of fields: %s',
                           task_creation_details)
        task_creation_result = self._asana_client.tasks.create_task(
            task_creation_details)
        self._logger.debug('Task creation result: %s', task_creation_result)
        if 'gid' not in task_creation_result:
            self._logger.error(
                'Unable to verify that the second attempt to create the Asana task succeeded')
            raise KeyError(
                'Unable to verify that the second attempt to create the Asana task succeeded')
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

    # Fetch details of the assigned team.
    #
    # There is a service ownership mapping in Asana as well, but we want to avoid the extra API call to look that up.
    @classmethod
    def _get_owning_team(cls, server_name: str, event_type: Optional[str] = None) -> teams.EngTeam:
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
            Team that takes responsibility for the entity with the given 'server_name'.
        """
        if event_type and event_type.lower() == 'web':
            # TODO: team-level routing based on URL: https://app.asana.com/0/1201267919523642/1201079771956134/f
            return teams.CORE_PRODUCT

        return cls._SERVER_TEAM_MAPPING.get(server_name, teams.CORE_PRODUCT)
