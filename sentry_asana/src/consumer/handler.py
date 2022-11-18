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
from typing import Dict, Any, List, Union, Callable, Optional, Tuple
from dependency_injector.wiring import Provide, inject
from common.components.logger.service import LoggerService
from common.components.metrics.service import MetricSink
from common.components.serializer.service import SerializerService
from common.components.entities.service import TeamService, EngTeam
from common.components.entities import heuristics
from common.constants import AlertType

from consumer.components.datadog.service import (
    DatadogService,
    make_datadog_asana_event,
    tag_list_to_dict,
    extract_datadog_fields,
)
from consumer.components.sentry.service import SentryService, extract_sentry_fields
from consumer.components.requests.containers import RequestsContainer
from consumer.components.asana.service import AsanaService, AsanaFields
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
    metrics: MetricSink = Provide[ApplicationContainer.metrics_container.metrics_sink],
) -> Dict[str, Union[bool, str]]:

    """Inspect the payload and process as Sentry or Datadog Alert Event"""
    log = logger.get()
    message_id = record['messageId']
    try:
        message_attributes: Dict = record['messageAttributes']
        alert_type: str = message_attributes.get('AlertType', {}).get('stringValue', '')
        try:
            alert = AlertType[alert_type]
        except KeyError:
            alert = AlertType.UNKNOWN_ALERT

        metrics.increment_event_count(
            alert, 'consumer', alert != AlertType.UNKNOWN_ALERT
        )

        if alert == AlertType.SENTRY:
            return await process_sentry_alert(record)

        if alert == AlertType.DATADOG:
            return await process_datadog_alert(record)

        log.error(
            f'Failed to identify alert type and link alert ({message_id}) with asana task.'
        )
        raise ValueError(
            f'AlertType not SENTRY or DATADOG, found "{alert_type}" instead.'
        )

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
    metrics: MetricSink = Provide[
        ApplicationContainer.metrics_container.container.metrics_sink
    ],
) -> Dict[str, Union[bool, str]]:
    """Process a Datadog event and create an Asana Task"""

    log = logger.get()

    body: str = record['body']
    message_id: str = record['messageId']
    try:
        datadog_event: Dict = serializer.parse(body)

        alert_transition = datadog_event.get('alert_transition', '').lower()
        if alert_transition not in ['triggered']:
            msg = f'Datadog notification not a triggering event, got {alert_transition} instead. Ignoring.'
            log.info(msg)
            return {
                'success': True,
                'message': msg,
                'message_id': message_id,
            }

        datadog_event_details: Dict = await datadog.get_event_details(datadog_event)
        event_details_tags = datadog_event_details.get('event', {}).get('tags', {})
        event_details_tags_dict = tag_list_to_dict(event_details_tags)

        team, results = query_entities_by_tags(entities, event_details_tags_dict)

        asana_fields: AsanaFields = extract_datadog_fields(datadog_event, team, results)

        log.info(
            f'Generated the following AsanaFields Object from the Datadog Payload: {asana_fields}'
        )
        log.info(
            f'Got the following fields back from get_event_details call: {datadog_event_details}'
        )

        asana_fields.tags['monitor_id'] = datadog_event_details.get('event', {}).get(
            'monitor_id'
        )

        new_task_gid, task_body = await create_asana_task(asana_fields, None, None)
        # We expect create_asana_task to raise on error, so failed ticket filings will not be counted.
        metrics.increment_ticket_count(team.Name, AlertType.DATADOG.name)

        # And link it in the event stream for this monitor.
        asana_url = f'https://app.asana.com/0/0/{new_task_gid}'
        await datadog.post_event_details(
            make_datadog_asana_event(datadog_event_details.get('event', {}), asana_url)
        )

        log.info(
            f'Created the following Asana task for alert: {asana_url}\n\n {task_body}'
        )

        return {
            'success': True,
            'message': f'Processed alert from datadog and created asana task: {asana_url}',
            'message_id': message_id,
        }
    except Exception as err:
        raise err


@inject
async def process_sentry_alert(  # pylint: disable=too-many-arguments,too-many-locals
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
    metrics: MetricSink = Provide[
        ApplicationContainer.metrics_container.container.metrics_sink
    ],
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

        # Adding some logic to skip over Javascript errors due to scanning so we don't deliver
        # another 500 tickets to Adoptions - 11/2/2022 #inc-unknown-sentry-errors
        event_title = event['title']
        if "ReferenceError" in event_title and "is not defined" in event_title:
            msg = f'Skipping over processing of Sentry {issue_id}: {event_title} to reduce spam after scanning incident'
            log.info(msg)
            return {
                'success': True,
                'message': msg,
                'message_id': message_id,
            }

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
        team, results = query_entities_by_tags(entities, dict(tags))

        asana_fields: AsanaFields = extract_sentry_fields(
            event, team, routing_data=results
        )

        new_task_gid, task_body = await create_asana_task(asana_fields, None, None)
        # We expect create_asana_task to raise on error, so failed ticket filings will not be counted.
        metrics.increment_ticket_count(team.Name, AlertType.SENTRY.name)

        # Finally, link the newly created asana task back to the sentry issue
        response = await sentry.add_link(issue_id, new_task_gid)
        if response is not None:
            log.info(
                f'Successfully linked Sentry issue {issue_id} with Asana task {new_task_gid}\n\n\n {task_body}'
            )
            return {
                'success': True,
                'message': f'asana task created ({new_task_gid})',
                'message_id': message_id,
            }

        log.error(
            f'Failed to link Sentry issue ({issue_id}) with Asana task ({new_task_gid})'
        )
        return {
            'success': False,
            'message': f'Failed to link sentry issue ({issue_id}) with asana task ({new_task_gid})',
            'message_id': message_id,
        }
    except Exception as err:
        raise err


@inject
def query_entities_by_tags(
    entities: TeamService,
    tags: Dict,
    logger: LoggerService = Provide[
        ApplicationContainer.logger_container.logger_service
    ],
) -> Tuple[EngTeam, str]:
    """Looks up team ownership based on the tags associated with the triggering event."""
    log = logger.get()
    try:
        team, results = heuristics.get_team(entities, tags)
        results = f'Routed to {team.Name} because we matched {results}'
    except heuristics.TeamNotFound:
        team = entities.default_team()
        log.info(f'Unable to find a team to match tags {tags}, using {team.Name}')
        results = f'Routed to {team.Name} because we did not find any matching teams.'
    log.info(f'Got {team} for tags: {tags}, with matchers: {results}')

    return team, results


@inject
async def create_asana_task(
    asana_fields: AsanaFields,
    root_asana_link: Optional[str],
    asana_link: Optional[str],
    asana: AsanaService = Provide[ApplicationContainer.asana_container.asana_service],
) -> Tuple[str, dict]:
    """Constructs task body and notes and files Asana task"""
    task_note = asana.create_task_note(asana_fields, root_asana_link, asana_link)
    task_body = await asana.create_task_body(asana_fields, task_note)

    # Create a new asana task
    new_task_gid = await asana.create_task(task_body)

    return new_task_gid, task_body
