# Copyright (C) 2020 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.

import hmac
import json
from hashlib import sha256
from typing import Dict

import asana
import boto3
import requests

from .service.asana_service import AsanaService
from .service.secrets_service import SecretKey, SecretsService
from .service.sentry_service import SentryService, SentryClient
from .util.logger import get_logger

# Get logger singleton
log = get_logger()

# Init our secrets service
secrets_service = SecretsService(boto3.client('secretsmanager'))

# Init our asana services
asana_client = asana.Client.access_token(
    secrets_service.get_secret_value(SecretKey.ASANA_PAT))
# Set this header to silence warnings (we're opting in to the new API changes)
asana_client.headers = {'Asana-Enable': 'new_user_task_lists'}
asana_service = AsanaService(asana_client, True)

# Init our sentry services
sentry_client = SentryClient(secrets_service, requests)
sentry_service = SentryService(sentry_client)


def handler(event: Dict, _: Dict) -> Dict:
    """The handler function that is run when the Lambda function executes."""
    body = event['body']
    client_secret = secrets_service.get_secret_value(
        SecretKey.SENTRY_CLIENT_SEC)
    expected = hmac.new(
        key=client_secret.encode('utf-8'),
        msg=body.encode('utf-8'),
        digestmod=sha256,
    ).hexdigest()
    if expected != event['headers']['sentry-hook-signature']:
        log.error('Unable to match received signature %s with expected signature %s',
                  event['headers']['sentry-hook-signature'], expected)
        raise ValueError(
            f'Invalid signature received. Expected signature: {expected} - Received signature: {event["headers"]["sentry-hook-signature"]}'
        )

    json_body = json.loads(body)

    # Parse the event data and extract the issue_id.
    issue_url = json_body.get('data', {}).get('event', {}).get('issue_url', '')
    issue_id = issue_url.strip('/').split('/').pop()
    if not issue_id:
        raise ValueError(
            'Could not extract the sentry issue id from the event payload!'
        )

    # Then, fetch the sentry issue and return the linked asana task
    # This will always point to the last created task for a given sentry issue
    log.info('Fetching asana link...')
    asana_link = sentry_service.get_sentry_asana_link(issue_id)

    # If we have an asana task associated, we fetch that task and check to see
    # if the body contains a root task payload embedded in the description.
    root_asana_link = None
    if asana_link:
        task_gid = asana_link.strip('/').split('/').pop()
        log.info('Asana link found, now fetching root asana link...')
        root_asana_link = asana_service.extract_root_asana_link(task_gid)

    # If 'Root Asana Task' is not present, the parent task is the root task
    if root_asana_link is None:
        root_asana_link = asana_link

    # Next, create a new asana task
    #
    # We want to provide the following context to users:
    # - Add a link to the previous asana task in the task body
    # - Add a link to the first (root) asana task link in the task body
    log.info('Creating asana task...')
    new_task_gid = asana_service.create_asana_task_from_sentry_event(
        json_body['data']['event'], asana_link, root_asana_link)

    # Finally, link the newly created asana task back to the sentry issue
    log.info('Linking Sentry issue with Asana task...')
    success = sentry_service.add_asana_link_to_issue(issue_id, new_task_gid)
    if success:
        log.info('Linking success!')
    else:
        log.error('Linking failed!')

    response = {
        'statusCode': 200,
        'body': json.dumps({'AsanaTaskGid': new_task_gid})
    }

    return response
