# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.

import json
import asyncio
import traceback
from typing import Dict, List, Union
from functools import partial
import asana
import boto3
import requests
from consumer.util.logger import get_logger
from consumer.service.secrets_service import SecretKey, SecretsService
from consumer.service.asana_service import AsanaService
from consumer.service.sentry_service import SentryService, SentryClient

log = get_logger()
secrets_service = SecretsService(boto3.client('secretsmanager'))
asana_client = asana.Client.access_token(
    secrets_service.get_secret_value(SecretKey.ASANA_PAT))
# Set this header to silence warnings (we're opting in to the new API changes)
asana_client.headers = {'Asana-Enable': 'new_user_task_lists'}
asana_service = AsanaService(asana_client, True)
sentry_client = SentryClient(secrets_service, requests)
sentry_service = SentryService(sentry_client)


def handler(event: Dict, context: Dict) -> Dict:
    """AWS Lambda entry point"""
    return asyncio.run(main(event, context))


async def main(event: Dict, _context: Dict) -> Dict:
    """Main async program"""
    log.debug('GOT EVENT: %s', event)

    # Extract our records to process
    records: List[Dict] = event.get('Records', [])
    log.debug('GOT RECORDS: %s', records)

    # Create a list of async partials to execute
    tasks = list(map(process, records))
    log.debug('GOT TASKS: %s', tasks)

    # Await on all of them to complete
    status_tuples = await asyncio.gather(
        *tasks
    )

    # Expand iterator to list
    statuses = list(status_tuples)
    log.debug('GOT STATUSES: %s', statuses)

    # Filter list of status to get only failed
    failed = list(filter(lambda status: status.get(
        'success', False) is False, statuses))

    if len(failed) > 0:
        log.warning('GOT FAILED: %s', failed)

    # Map to get the structure AWS Expects:
    # https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html
    response = {
        'batchItemFailures': list(map(lambda status: {
            'itemIdentifier': status['message_id']
        }, failed)),
    }

    log.debug('GOT RESPONSE: %s', response)
    # By returning only the failed status messages to AWS, the messages
    # will get put back into SQS to be tried again instead of the entire batch of
    # messages
    return response


async def process(record: Dict) -> Dict[str, Union[bool, str]]:
    """Process a Sentry event and create an Asana Task"""
    body: str = record['body']
    message_id: str = record['messageId']  # SQS camelCase
    try:
        # Parse the event data and extract the issue_id.
        sentry_event: Dict = json.loads(body)
        data: Dict = sentry_event['data']
        event: Dict = data['event']
        issue_url: str = event.get('issue_url', '')
        issue_id = issue_url.strip('/').split('/').pop()
        log.info('Processing sentry issue_id: %s', issue_id)
        if not issue_id:
            return {
                'success': False,
                'message': 'Could not extract the sentry issue id from the event payload!',
                'message_id': message_id
            }

        # Then, fetch the sentry issue and return the linked asana task
        # This will always point to the last created task for a given sentry issue
        log.info('Fetching asana link (if any)')
        loop = asyncio.get_event_loop()
        asana_link = await loop.run_in_executor(
            None,
            partial(
                sentry_service.get_sentry_asana_link,
                issue_id
            )
        )

        # If we have an asana task associated, we fetch that task and check to see
        # if the body contains a root task payload embedded in the description.
        root_asana_link = None
        if asana_link:
            log.info('Asana link found, now fetching root asana link...')
            task_gid = asana_link.strip('/').split('/').pop()
            root_asana_link = await loop.run_in_executor(
                None,
                partial(
                    asana_service.extract_root_asana_link,
                    task_gid
                )
            )

        # If 'Root Asana Task' is not present, the parent task is the root task
        if root_asana_link is None:
            root_asana_link = asana_link

        # Next, create a new asana task
        #
        # We want to provide the following context to users:
        # - Add a link to the previous asana task in the task body
        # - Add a link to the first (root) asana task link in the task body
        log.info('Creating asana task...')
        new_task_gid = await loop.run_in_executor(
            None,
            partial(
                asana_service.create_asana_task_from_sentry_event,
                event,
                asana_link, root_asana_link
            )
        )

        # Finally, link the newly created asana task back to the sentry issue
        log.info('Linking Sentry issue with Asana task...')
        success = await loop.run_in_executor(
            None,
            partial(
                sentry_service.add_asana_link_to_issue,
                issue_id,
                new_task_gid
            )
        )
        if success is True:
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
