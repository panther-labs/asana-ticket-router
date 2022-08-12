# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
import asyncio
from typing import Dict, Any
from dependency_injector.wiring import Provide, inject
from common.components.logger.service import LoggerService
from common.constants import AlertType
from producer.components.queue.service import QueueService
from producer.components.validator.service import ValidatorService
from producer.components.application import ApplicationContainer

# Initialize in global state so Lambda can use on hot invocations
app = ApplicationContainer()
app.config.from_yaml('producer/config.yml', required=True, envs_required=True)
app.logger_container.configure_logger()  # pylint: disable=no-member


def handler(event: Dict, _context: Any) -> Dict[str, int]:
    """AWS Lambda entry point"""
    app.wire(modules=[__name__])  # pylint: disable=no-member
    return asyncio.run(main(event, _context))


@inject
async def main(
    event: Dict,
    _context: Any,
    logger: LoggerService = Provide[
        ApplicationContainer.logger_container.logger_service  # pylint: disable=no-member
    ],
    queue: QueueService = Provide[
        ApplicationContainer.queue_container.queue_service  # pylint: disable=no-member
    ],
    validator: ValidatorService = Provide[
        ApplicationContainer.validator_container.validator_service  # pylint: disable=no-member
    ],
) -> Dict[str, int]:
    """Main async program"""
    log = logger.get()
    # Using Lambda Proxy Integration, the body in the event of lambda
    # is a stringified payload of the original request, not JSON.
    #
    # NOTE: When debugging, make sure you stringify the 'body' payload in
    # the request to the lambda

    body: str = event.get('body', '')
    headers: Dict = event.get('headers', {})

    sentry_signature: str = headers.get('sentry-hook-signature', '')
    datadog_signature: str = headers.get('datadog-secret-token', '')

    alert_type: AlertType = AlertType.UNKNOWN_ALERT
    valid: bool = False
    if sentry_signature:
        alert_type = AlertType.SENTRY
        valid = await validator.validate_sentry(body, sentry_signature)
    elif datadog_signature:
        alert_type = AlertType.DATADOG
        valid = await validator.validate_datadog(datadog_signature)

    if alert_type is AlertType.UNKNOWN_ALERT:
        raise ValueError(
            'Request missing sentry-hook-signature or datadog-secret-token headers.'
        )

    if not valid:
        raise ValueError(f'{alert_type.name} webhook payload signature mismatch')

    response = await queue.put(body, alert_type.name)
    log.info("Success!")
    return response
