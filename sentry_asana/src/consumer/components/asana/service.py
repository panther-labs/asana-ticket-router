# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
from asyncio import AbstractEventLoop
import asyncio
from datetime import datetime, timedelta
import re
from typing import Callable, Dict, List, Optional
from functools import partial
from logging import Logger
from urllib import parse
from dateutil import parser
from asana import Client
from asana.error import ForbiddenError, NotFoundError
from common.constants import AlertType
from common.components.serializer.service import SerializerService
from common.components.entities.service import EngTeam
from consumer.components.asana.entities import (
    RUNBOOK_URL,
    PRIORITY,
    AsanaFields,
    CUSTOMFIELD,
    SELF_HOSTED_ACCOUNTS_IDS,
)


# pylint: disable=too-many-instance-attributes
class AsanaService:
    """Asana Service"""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        loop: Callable[[], AbstractEventLoop],
        development: bool,
        dev_asana_sentry_project: str,
        release_testing_portfolio: str,
        logger: Logger,
        client: Client,
        serializer: SerializerService,
        # By default if nothing matches send it to observability Sprint board.
        default_asana_portfolio_id: str = '1201675315244004',
    ):
        self._loop = loop
        self._development = development
        self._dev_asana_sentry_project = dev_asana_sentry_project
        self._release_testing_portfolio = release_testing_portfolio
        self._logger = logger
        self._serializer = serializer
        self._client = client
        # Tell Asana to use the latest API changes (opt in, silence warning)
        self._client.headers = {
            'Asana-Enable': 'new_user_task_lists,new_project_templates'
        }
        self._parser = re.compile(
            r"(Root Asana Task: )(https:\/\/app.asana.com\/\d+\/\d+\/\d+)"
        )
        self.default_asana_portfolio_id = default_asana_portfolio_id

    async def _get_projects_in_portfolio(self, portfolio_gid: str) -> List[Dict]:
        """Dispatch a call to find a Sentry issue details by its issue_id"""
        self._logger.info('Getting projects in portfolio')
        return await self._loop().run_in_executor(
            None,
            partial(
                self._client.portfolios.get_items,
                portfolio_gid,
                opt_fields=['name', 'resource_type', 'created_at', 'archived'],
            ),
        )

    async def _find_asana_task(self, task_gid: str) -> Optional[Dict]:
        """Dispatch a call to find an Asana task by task_gid

        If a task has been deleted (Forbidden), returns None
        """
        self._logger.info('Finding asana task')
        try:
            return await self._loop().run_in_executor(
                None, partial(self._client.tasks.find_by_id, task_gid)
            )
        except ForbiddenError as err:
            self._logger.warning('Task is Private (most likely deleted): %s', err)
            return None
        except NotFoundError as err:
            self._logger.warning('Task not found: %s', err)
            return None

    async def _create_asana_task(self, task_body: Dict) -> Dict:
        """Dispatch a call to create a new Asana task"""
        self._logger.info("Creating asana task")
        return await self._loop().run_in_executor(
            None, partial(self._client.tasks.create_task, task_body)
        )

    async def create_task(
        self,
        task_body: Dict,
    ) -> str:
        """Extracts relevant info from the Sentry event & creates an Asana task"""
        response = await self._create_asana_task(task_body)
        return response['gid']

    async def extract_datadog_fields(
        self, datadog_event: Dict, team: EngTeam, routing_data: str
    ) -> AsanaFields:
        """Extract relevent fields from the datadog event"""
        self._logger.debug('Extracting fields')
        url = datadog_event['link']

        tags = {}
        for tag in datadog_event['tags'].split(','):
            key: str = tag
            value: str = ''

            if ':' in tag:
                key = tag.split(':')[0]
                value = tag.split(':')[1]

            tags[key] = value

        aws_region = tags.get('region', 'Unknown')
        aws_account_id = tags.get('aws_account', 'Unknown')
        customer = tags.get('customer_name', 'Unknown')
        display_name = parse.quote(customer)
        event_datetime = datetime.fromtimestamp(
            int(datadog_event['date']) / 1000
        ).strftime('%Y-%m-%dT%H:%M:%S')
        title = datadog_event['title']
        datadog_priority = datadog_event.get('priority', 'Unknown').lower()
        priority = self._get_task_priority(datadog_priority, AlertType.DATADOG)
        environment = tags.get('env', 'Unknown').lower()
        project_gids = await self._get_project_ids(environment, priority, team)
        runbook_url = RUNBOOK_URL
        return AsanaFields(
            assigned_team=team,
            aws_account_id=aws_account_id,
            aws_region=aws_region,
            customer=customer,
            display_name=display_name,
            environment=environment,
            event_datetime=event_datetime,
            priority=priority,
            project_gids=project_gids,
            runbook_url=runbook_url,
            tags=tags,
            title=title,
            url=url,
            routing_data=routing_data,
        )

    async def extract_sentry_fields(
        self, sentry_event: Dict, team: EngTeam, routing_data: str
    ) -> AsanaFields:
        """Extract relevent fields from the sentry event"""
        self._logger.debug('Extracting fields')
        issue_id = sentry_event['issue_id']
        url = f'https://sentry.io/organizations/panther-labs/issues/{issue_id}'
        tags = dict(sentry_event['tags'])
        aws_region = tags['aws_region']
        aws_account_id = tags['aws_account_id']
        customer = tags.get('customer_name', 'Unknown')
        display_name = parse.quote(customer)
        event_datetime = sentry_event['datetime'].lower()
        title = sentry_event['title']
        level = sentry_event['level'].lower()
        priority = self._get_task_priority(level, AlertType.SENTRY)
        environment = sentry_event['environment'].lower()
        project_gids = await self._get_project_ids(environment, priority, team)
        runbook_url = RUNBOOK_URL
        return AsanaFields(
            assigned_team=team,
            aws_account_id=aws_account_id,
            aws_region=aws_region,
            customer=customer,
            display_name=display_name,
            environment=environment,
            event_datetime=event_datetime,
            priority=priority,
            project_gids=project_gids,
            runbook_url=runbook_url,
            tags=tags,
            title=title,
            url=url,
            routing_data=routing_data,
        )

    def create_task_note(
        self,
        fields: AsanaFields,
        root_asana_link: Optional[str],
        prev_asana_link: Optional[str],
    ) -> str:
        """Create the note for the asana task"""
        self._logger.debug('Creating asana task notes')
        note = (
            f'Sentry Issue URL: {fields.url}\n\n'
            f'Event Datetime: {fields.event_datetime}\n\n'
            f'Customer Impacted: {fields.customer}\n\n'
            f'Environment: {fields.environment}\n\n'
            f'Runbook: {fields.runbook_url}\n\n'
        )

        # if a customer is not self-hosted, add a switch role link
        if fields.aws_account_id not in SELF_HOSTED_ACCOUNTS_IDS:
            note = note + (
                f'AWS Switch Role Link: https://{fields.aws_region}.signin.aws.amazon.com/switchrole'
                f'?roleName=PantherSupportRole-{fields.aws_region}'
                f'&account={fields.aws_account_id}'
                f'&displayName={fields.display_name}%20Support\n\n'
            )

        # If we have a Lambda request id from the Sentry event, construct a link to the trace for that request in Datadog.
        if 'zap_lambdaRequestId' in fields.tags.keys():
            event_time = parser.parse(fields.event_datetime)
            # Lets widen the query window a bit to account for any potential Sentry event time vs Datadog event time shenanigans.
            one_hour_before = event_time + timedelta(hours=-1)
            one_hour_before_ts = int(one_hour_before.timestamp() * 1000.0)

            request_id = fields.tags['zap_lambdaRequestId']

            datadog_query_url = (
                f'https://app.datadoghq.com/apm/traces?'
                f'query=@account_id:{fields.aws_account_id}%20@request_id:{request_id}'
                f'&start={one_hour_before_ts}&historicalData=true'
            )

            note = note + f'Datadog Trace Link: {datadog_query_url}\n\n'

        # If we had a root task link, set it in the payload
        if root_asana_link:
            note = f'Root Asana Task: {root_asana_link}\n\n' + note
        # If we had a previous task link, set it in the payload
        if prev_asana_link:
            note = f'Previous Asana Task: {prev_asana_link}\n\n' + note
        if fields.routing_data:
            note = note + f'Routing Information: {fields.routing_data}\n\n'

        return ''.join(note)

    async def extract_root_asana_link(self, task_gid: str) -> Optional[str]:
        """Extract root asana link from an asana task"""
        task = await self._find_asana_task(task_gid)
        if task is None:
            return None

        notes = task.get('notes', None)
        if not notes:
            self._logger.error('Could not find notes in task: %s', task_gid)
            return None

        match = self._parser.search(notes)
        if not match:
            self._logger.warning('No root asana task link found')
            return None

        prev_link = match.group(2)
        return prev_link

    async def _get_project_ids(
        self, environment: str, priority: PRIORITY, owning_team: EngTeam
    ) -> List[str]:
        """Returns a list of project ids to attach to an Asana task"""
        self._logger.debug("Getting relevant project ids")
        # If we are in local dev mode for sentry-asana, or
        # if the issue is from local development (panther-enterprise),
        # we use sandbox project boards
        if self._development or environment == 'dev':
            # TODO: I'm going to just hardcode our sandbox board in here for now, but we should have a dev teams.yaml for this?
            return await self._get_dev_project_ids(owning_team.AsanaSandboxPortfolioId)

        # If release testing, use team's current sprint and add to current release project
        if environment == 'staging':
            return await self._get_staging_project_ids(
                owning_team.AsanaSprintPortfolioId
            )

        # If a production 'warning', add to backlog
        if priority.name != PRIORITY.HIGH.name:
            return [owning_team.AsanaBacklogId]

        # If a production 'high', add to current sprint
        return await self._get_production_project_ids(
            owning_team.AsanaSprintPortfolioId
        )

    async def _get_dev_project_ids(self, portfolio_id: str) -> List[str]:
        """Get relevant development project ids"""
        self._logger.debug("Getting latest dev project ids")
        sprint_id = await self._get_latest_project_id(portfolio_id)
        project_ids = [sprint_id]
        # Always append dev project
        project_ids.append(self._dev_asana_sentry_project)
        return [i for i in project_ids if i is not None]

    async def _get_staging_project_ids(self, portfolio_id: str) -> List[str]:
        """Get relevant staging project ids"""
        self._logger.debug("Getting latest staging project ids")
        ids = await asyncio.gather(
            self._get_latest_project_id(portfolio_id),
            self._get_latest_project_id(self._release_testing_portfolio),
        )
        project_ids = list(ids)
        filtered = [i for i in project_ids if i is not None]

        # Ensure we have at least 1 project to assign
        if len(filtered) == 0:
            filtered.append(self.default_asana_portfolio_id)
        return filtered

    async def _get_production_project_ids(self, portfolio_id: str) -> List[str]:
        """Get relevant production project ids"""
        self._logger.debug("Getting latest production project ids")
        sprint_id = await self._get_latest_project_id(portfolio_id)
        project_ids = [sprint_id]
        filtered = [i for i in project_ids if i is not None]
        # Ensure we have at least 1 project to assign
        if len(filtered) == 0:
            filtered.append(self.default_asana_portfolio_id)
        return filtered

    async def _get_latest_project_id(self, portfolio_id: str) -> Optional[str]:
        """Get the latest project in a portfolio and returns its id"""
        self._logger.debug("Getting latest project id")
        projects = await self._get_projects_in_portfolio(portfolio_id)

        # Expand itr to a list
        projects = list(projects)
        if len(projects) == 0:
            return None

        # Filter unwanted results
        filtered_projects = filter(
            lambda proj: proj['archived'] is False
            and proj['resource_type'] == 'project',
            projects,
        )

        # Sort by created_at
        sorted_projects = sorted(
            filtered_projects,
            key=lambda proj: datetime.strptime(
                proj['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ'
            ),
        )

        # Safely return the last item in the iterator (most recent)
        latest_project = next(reversed(sorted_projects), None)
        if latest_project is None:
            return None
        return latest_project['gid']

    def create_task_body(self, fields: AsanaFields, notes: str) -> Dict:
        """Create an asana tasks details"""
        self._logger.debug("Building asana task body")
        return {
            'name': fields.title,
            'projects': fields.project_gids,
            'custom_fields': {
                CUSTOMFIELD.ESTIMATE.value: 0.1,  # Days
                CUSTOMFIELD.PRIORITY.value: fields.priority.value,
                CUSTOMFIELD.REPORTER.value: CUSTOMFIELD.SENTRY_IO.value,
                CUSTOMFIELD.EPD_TASK_TYPE.value: CUSTOMFIELD.ON_CALL.value,
                CUSTOMFIELD.TEAM.value: fields.assigned_team.AsanaTeamId,
                CUSTOMFIELD.OUTCOME_FIELD.value: CUSTOMFIELD.OUTCOME_TYPE_KTLO.value,
            },
            'notes': notes,
        }

    @staticmethod
    def _get_task_priority(level: str, alert_type: AlertType) -> PRIORITY:
        """Returns a PRIORITY Enum based on the Sentry or Datadog event level provided."""

        if alert_type.name == AlertType.SENTRY.name:
            if level == 'warning':
                return PRIORITY.MEDIUM

        if alert_type.name == AlertType.DATADOG.name:
            if level in ['p5', 'p4', 'p3']:
                return PRIORITY.MEDIUM

        return PRIORITY.HIGH
