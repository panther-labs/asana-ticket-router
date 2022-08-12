# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
# pylint: disable=no-member
import asyncio
from functools import partial
import traceback
from typing import Dict, Any, List, Union, Callable
from dependency_injector.wiring import Provide, inject
from common.components.logger.service import LoggerService
from common.components.serializer.service import SerializerService
from common.components.entities.service import TeamService
from common.components.entities import heuristics
from common.constants import AlertType
from consumer.components.datadog.service import DatadogService
from consumer.components.sentry.service import SentryService
from consumer.components.requests.containers import RequestsContainer
from consumer.components.asana.service import AsanaService
from consumer.components.asana.service import AsanaFields
from consumer.components.application import ApplicationContainer


# Initialize in global state so Lambda can use on hot invocations
app = ApplicationContainer()
app.config.from_yaml('consumer/config.yml', required=True, envs_required=True)
app.logger_container.configure_logger()


def handler(*args: Any, **kwargs: Any) -> Dict:
    """AWS Lambda entry point"""
    app.wire(modules=[__name__])
    wrapped = use_session(callback=partial(main, *args, **kwargs))
    return asyncio.run(wrapped)


@inject
async def use_session(
    callback: Callable,
    requests_container: RequestsContainer = Provide[
        ApplicationContainer.requests_container
    ],
) -> Dict[Any, Any]:
    """Uses an HTTP Session via context"""
    # Initialize a new singleton request service
    requests_service = requests_container.requests_service()
    # Use a session context. This mutates the service, but the other dependencies on the service
    # need to be updated. Therefore, we override the service and reset the singleton which propagates
    # automatically to the other containers.
    async with requests_service.with_session():
        requests_container.requests_service.override(requests_service)
        requests_container.requests_service.reset()
        return await callback()


@inject
async def main(
    event: Dict,
    _context: Any,
    logger: LoggerService = Provide[
        ApplicationContainer.logger_container.logger_service
    ],
) -> Dict:
    """Main async program"""
    log = logger.get()

    # Extract the SQS records to process
    records: List[Dict] = event.get('Records', [])
    log.info('Number of records to process: %d', len(records))
    tasks = list(map(process, records))
    status_tuples = await asyncio.gather(*tasks)
    statuses = list(status_tuples)

    # Filter list of status to get only failed
    failed = list(
        filter(lambda status: status.get('success', False) is False, statuses)
    )

    if len(failed) > 0:
        log.warning('Failed to process records: %s', failed)

    # Map to get the structure AWS Expects:
    # https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html
    response = {
        'batchItemFailures': list(
            map(lambda status: {'itemIdentifier': status['message_id']}, failed)
        ),
    }

    log.info('SQS response: %s', response)
    # By returning only the failed status messages to AWS, the messages
    # will get put back into SQS to be tried again instead of the entire batch of
    # messages
    return response


@inject
async def process(
    record: Dict,
    logger: LoggerService = Provide[
        ApplicationContainer.logger_container.logger_service
    ],
) -> Dict[str, Union[bool, str]]:

    """Inspect the payload and process as Sentry or Datadog Alert Event"""
    log = logger.get()
    message_id = record['messageId']
    try:
        message_attributes: Dict = record['messageAttributes']
        alert_type: str = message_attributes.get('AlertType', {}).get('stringValue', '')
        if alert_type not in [AlertType.SENTRY.name, AlertType.DATADOG.name]:
            raise ValueError(
                f'AlertType not SENTRY or DATADOG, found "{alert_type}" instead.'
            )

        if alert_type == AlertType.SENTRY.name:
            return await process_sentry_alert(record)

        if alert_type == AlertType.DATADOG.name:
            return await process_datadog_alert(record)

        log.error(
            f'Failed to identify alert type and link alert ({message_id}) with asana task.'
        )
        return {
            'success': False,
            'message': f'Failed to identify alert type and link alert ({message_id}) with asana task.',
            'message_id': message_id,
        }

    # Catch all other exceptions and return a bad status to retry the record.
    # pylint: disable=broad-except
    except Exception as err:
        # NOTE: Logging an 'exception' doesn't cause CloudWatch alarm to alert.
        #
        # This is intentional as we don't want to be notified for ANY exception.
        # Failed alerts will be retried and put in a DLQ where we WILL get alerted
        # and the log statements will help with debugging.
        log.exception(err)
        return {
            'success': False,
            'message': f'{str(err)}\n{traceback.format_exc()}',
            'message_id': message_id,
        }


@inject
async def process_datadog_alert(  # pylint: disable=too-many-arguments
    record: Dict,
    logger: LoggerService = Provide[
        ApplicationContainer.logger_container.logger_service
    ],
    serializer: SerializerService = Provide[
        ApplicationContainer.serializer_container.serializer_service
    ],
    entities: TeamService = Provide[
        ApplicationContainer.entities_container.teams_service
    ],
    datadog: DatadogService = Provide[
        ApplicationContainer.datadog_container.container.datadog_service
    ],
    asana: AsanaService = Provide[ApplicationContainer.asana_container.asana_service],
) -> Dict[str, Union[bool, str]]:
    """Process a Datadog event and create an Asana Task"""

    log = logger.get()

    body: str = record['body']
    message_id: str = record['messageId']
    try:
        datadog_event: Dict = serializer.parse(body)
        log.info(f'Parsed the following Datadog Event: {datadog_event}')

        # Next, create a new asana task
        datadog_event_details: Dict = await datadog.get_event_details(datadog_event)
        try:
            team, results = heuristics.get_team(entities, datadog_event_details)
            results = f"Routed to {team} because we matched {results.Matches}"
        except heuristics.DefaultTeamException:
            team = entities.default_team()
            log.info(
                f"Unable to find a team to match {datadog_event_details}, using {team}"
            )
            results = f"Routed to {team} because we did not find any matching teams."
        log.info(
            f"Got {team} for sentry issue: {datadog_event_details}, with matchers: {results.Matches}"
        )
        asana_fields: AsanaFields = await asana.extract_datadog_fields(
            datadog_event, team, results
        )
        log.info(
            f'Generated the following AsanaFields Object from the Datadog Payload: {asana_fields}'
        )
        log.info(
            f'Got the following fields back from get_event_details call: {datadog_event_details}'
        )

        return {
            'success': True,
            'message': 'Processed an alert from Datadog and did absolutely nothing.',
            'message_id': message_id,
        }
    except Exception as err:
        raise err


@inject
async def process_sentry_alert(  # pylint: disable=too-many-arguments
    record: Dict,
    logger: LoggerService = Provide[
        ApplicationContainer.logger_container.logger_service
    ],
    serializer: SerializerService = Provide[
        ApplicationContainer.serializer_container.serializer_service
    ],
    entities: TeamService = Provide[
        ApplicationContainer.entities_container.teams_service
    ],
    sentry: SentryService = Provide[
        ApplicationContainer.sentry_container.sentry_service
    ],
    asana: AsanaService = Provide[ApplicationContainer.asana_container.asana_service],
) -> Dict[str, Union[bool, str]]:
    """Process a Sentry event and create an Asana Task"""

    log = logger.get()

    body: str = record['body']
    message_id: str = record['messageId']
    try:

        sentry_event: Dict = serializer.parse(body)

        data: Dict = sentry_event['data']
        event: Dict = data['event']
        issue_id: str = event['issue_id']
        log.info('Processing sentry issue_id: %s', issue_id)

        # Then, fetch the sentry issue and return the linked asana task
        # This will always point to the last created task for a given sentry issue
        log.info('Fetching asana link (if any)')
        asana_link = await sentry.get_sentry_asana_link(issue_id)

        # If we have an asana task associated, we fetch that task and check to see
        # if the body contains a root task payload embedded in the description.
        root_asana_link = None
        if asana_link:
            log.info('Asana link found, now fetching root asana link...')
            task_gid = asana_link.strip('/').split('/').pop()
            root_asana_link = await asana.extract_root_asana_link(task_gid)

        # If 'Root Asana Task' is not present, the parent task is the root task
        if root_asana_link is None:
            log.info('No root asana link detected, assigning link')
            root_asana_link = asana_link

        # Next, create a new asana task
        tags = event.get('tags', [])
        try:
            team, results = heuristics.get_team(entities, dict(tags))
            results = f"Routed to {team} because we matched {results.Matches}"
        except heuristics.DefaultTeamException:
            team = entities.default_team()
            log.info(f"Unable to find a team to match {issue_id}, using {team}")
            results = f"Routed to {team} because we did not find any matching teams."
        log.info(
            f"Got {team} for sentry issue: {issue_id}, with matchers: {results.Matches}"
        )
        asana_fields: AsanaFields = await asana.extract_sentry_fields(
            event, team, routing_data=results
        )
        new_task_gid = await asana.create_task(
            asana_fields, root_asana_link, asana_link
        )
        # Asana create note to add reason.

        # Finally, link the newly created asana task back to the sentry issue
        response = await sentry.add_link(issue_id, new_task_gid)
        if response is not None:
            log.info('Linking success!')
            return {
                'success': True,
                'message': f'asana task created ({new_task_gid})',
                'message_id': message_id,
            }

        log.error(
            f'Failed to link sentry issue ({issue_id}) with asana task ({new_task_gid})'
        )
        return {
            'success': False,
            'message': f'Failed to link sentry issue ({issue_id}) with asana task ({new_task_gid})',
            'message_id': message_id,
        }
    except Exception as err:
        raise err
