# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
# pylint: disable=no-member
# mypy: ignore-errors
import asyncio
from typing import Dict
import boto3
from dependency_injector import containers, providers
from . import service


async def init(secretsmanager: service.SecretsManagerService) -> Dict[str, str]:
    """Initialize the secrets manager"""
    return await secretsmanager.get_secret_string()


class SecretsManagerContainer(containers.DeclarativeContainer):
    """Secrets Container"""

    config = providers.Configuration(strict=True)
    logger = providers.Dependency()
    serializer = providers.Dependency()

    secretsmanager_client = providers.Singleton(
        boto3.client,
        service_name="secretsmanager"
    )

    secretsmanager_service = providers.Singleton(
        service.SecretsManagerService,
        loop=asyncio.get_event_loop,
        logger=logger,
        client=secretsmanager_client,
        secret_name=config.secret_name,
        serializer=serializer
    )

    keys = providers.Resource(
        init,
        secretsmanager_service
    )
