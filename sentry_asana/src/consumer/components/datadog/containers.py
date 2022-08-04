# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
# pylint: disable=no-member
# mypy: ignore-errors
from typing import Awaitable, Callable, Dict

from datadog_api_client import ApiClient, Configuration
from dependency_injector import containers, providers
from . import service

datadog_api_key: Callable[[Dict], str] = lambda keys: keys['DATADOG_API_KEY']

datadog_app_key: Callable[[Dict], str] = lambda keys: keys['DATADOG_APP_KEY']


class DatadogContainer(containers.DeclarativeContainer):
    """Datadog Container"""

    logger = providers.Dependency()
    serializer = providers.Dependency()
    keys = providers.Dependency()

    client = providers.Singleton(
        ApiClient,
        configuration=Configuration()
    )

    datadog_service: Callable[..., Awaitable[service.DatadogService]] = providers.Singleton(
        service.DatadogService,
        logger=logger,
        serializer=serializer,
        client=client,
        datadog_api_key=providers.Resource(datadog_api_key, keys),
        datadog_app_key=providers.Resource(datadog_app_key, keys)
    )
