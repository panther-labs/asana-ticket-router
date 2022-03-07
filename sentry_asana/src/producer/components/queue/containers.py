# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
# pylint: disable=no-member
# mypy: ignore-errors

import asyncio
import boto3
from dependency_injector import containers, providers
from . import service


class QueueContainer(containers.DeclarativeContainer):
    """Queue Container"""

    config = providers.Configuration(strict=True)
    logger = providers.Dependency()

    sqs_client = providers.Singleton(
        boto3.client,
        service_name="sqs"
    )

    queue_service = providers.Singleton(
        service.QueueService,
        loop=asyncio.get_running_loop,
        logger=logger,
        client=sqs_client,
        queue_url=config.queue_url,
    )
