# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
# pylint: disable=no-member
# mypy: ignore-errors
import asyncio
import requests
from dependency_injector import containers, providers
from . import service


class RequestsContainer(containers.DeclarativeContainer):
    """Sentry Container"""

    logger = providers.Dependency()
    requests_client = providers.Dependency(default=requests)

    requests_service = providers.Singleton(
        service.RequestsService,
        loop=asyncio.get_event_loop,
        logger=logger,
        client=requests_client
    )
