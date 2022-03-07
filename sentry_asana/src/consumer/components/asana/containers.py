# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
# pylint: disable=no-member
# mypy: ignore-errors
import asyncio
from typing import Dict, Callable
import asana
from dependency_injector import containers, providers
from . import service

asana_pat: Callable[[Dict], str] = lambda keys: keys['ASANA_PAT']


class AsanaContainer(containers.DeclarativeContainer):
    """Asana Container"""

    config = providers.Configuration(strict=True)
    logger = providers.Dependency()
    serializer = providers.Dependency()
    keys = providers.Dependency()

    development = providers.Selector(
        config.development,
        true=providers.Factory(bool, True),
        false=providers.Factory(bool, False),
    )

    asana_client = providers.Singleton(
        asana.Client.access_token,
        providers.Resource(asana_pat, keys)
    )

    asana_service = providers.Singleton(
        service.AsanaService,
        loop=asyncio.get_running_loop,
        development=development,
        dev_asana_sentry_project=config.dev_asana_sentry_project,
        release_testing_portfolio=config.release_testing_portfolio,
        logger=logger,
        client=asana_client,
        serializer=serializer,
    )
