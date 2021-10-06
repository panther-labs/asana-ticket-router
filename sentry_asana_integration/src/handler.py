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

from .service.asana_service import AsanaService
from .service.secrets_service import SecretKey, SecretsService
from .service.sentry_service import SentryService
from .util.logger import get_logger

log = get_logger()
secrets_manager_client = boto3.client('secretsmanager')
secrets_service = SecretsService(secrets_manager_client)
asana_client = asana.Client.access_token(secrets_service.get_secret_value(SecretKey.ASANA_PAT))
asana_service = AsanaService(asana_client, True)
sentry_service = SentryService(secrets_service)

def handler(event: Dict, _: Dict) -> Dict:
    """The handler function that is run when the Lambda function executes."""
    body = event['body']
    log.info(body)
    client_secret = secrets_service.get_secret_value(SecretKey.SENTRY_CLIENT_SEC)
    expected = hmac.new(
        key=client_secret.encode('utf-8'),
        msg=body.encode('utf-8'),
        digestmod=sha256,
    ).hexdigest()
    if expected != event['headers']['sentry-hook-signature']:
        log.error('Unable to match received signature %s with expected signature %s', event['headers']['sentry-hook-signature'], expected)
        raise ValueError(
            f'Invalid signature received. Expected signature: {expected} - Received signature: {event["headers"]["sentry-hook-signature"]}'
        )

    log.info('Verified signature, now attempting to triage Sentry issue..')
    json_body = json.loads(body)
    new_task_gid = asana_service.create_asana_task_from_sentry_event(json_body['data']['event'])
    log.info('Successfully created Asana task with gid %s', new_task_gid)
    log.info('Attempting to link Sentry issue with Asana task..')
    if sentry_service.link_issue_to_asana_task(json_body['data']['event'], new_task_gid):
        log.info('Linking successful!')

    response = {
        'statusCode': 200,
        'body': json.dumps({'AsanaTaskGid': new_task_gid})
    }

    return response
