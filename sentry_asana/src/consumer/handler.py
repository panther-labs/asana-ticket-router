# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
# pylint: disable=no-member
import asyncio
import traceback
from typing import Dict, Any, List, Union
from dependency_injector.wiring import Provide, inject
from common.components.logger.service import LoggerService
from common.components.serializer.service import SerializerService
from consumer.components.sentry.service import SentryService
from consumer.components.asana.service import AsanaService
from consumer.components.application import ApplicationContainer

# Initialize in global state so Lambda can use on hot invocations
app = ApplicationContainer()
app.config.from_yaml(
    'consumer/config.yml',
    required=True,
    envs_required=True
)
app.logger_container.configure_logger()


def handler(event: Dict, _context: Any) -> Dict[str, int]:
    """AWS Lambda entry point"""
    app.wire(modules=[__name__])
    return asyncio.run(main(event, _context))


@inject
async def main(
    event: Dict,
    _context: Any,
    logger: LoggerService = Provide[ApplicationContainer.logger_container.logger_service],
) -> Dict:
    """Main async program"""
    log = logger.get()

    # Extract the SQS records to process
    records: List[Dict] = event.get('Records', [])
    tasks = list(map(process, records))
    status_tuples = await asyncio.gather(*tasks)
    statuses = list(status_tuples)

    # Filter list of status to get only failed
    failed = list(filter(lambda status: status.get(
        'success', False) is False, statuses))

    if len(failed) > 0:
        log.warning('Failed to process records: %s', failed)

    # Map to get the structure AWS Expects:
    # https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html
    response = {
        'batchItemFailures': list(map(lambda status: {
            'itemIdentifier': status['message_id']
        }, failed)),
    }

    log.info('SQS response: %s', response)
    # By returning only the failed status messages to AWS, the messages
    # will get put back into SQS to be tried again instead of the entire batch of
    # messages
    return response


@inject
async def process(
    record: Dict,
    logger: LoggerService = Provide[ApplicationContainer.logger_container.logger_service],
    serializer: SerializerService = Provide[ApplicationContainer.serializer_container.serializer_service],
    sentry: SentryService = Provide[ApplicationContainer.sentry_container.sentry_service],
    asana: AsanaService = Provide[ApplicationContainer.asana_container.asana_service]
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
        new_task_gid = await asana.create_task(event, root_asana_link, asana_link)

        # Finally, link the newly created asana task back to the sentry issue
        response = await sentry.add_link(issue_id, new_task_gid)
        if response is not None:
            log.info('Linking success!')
            return {
                'success': True,
                'message': f'Asana task created ({new_task_gid})',
                'message_id': message_id
            }

        log.error('Linking failed!')
        return {
            'success': False,
            'message': f'Failed to link Sentry Issue ({issue_id}) with Asana Task ({new_task_gid})',
            'message_id': message_id
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
            'message_id': message_id
        }
