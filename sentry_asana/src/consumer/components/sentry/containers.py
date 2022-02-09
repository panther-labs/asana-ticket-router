# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
# pylint: disable=no-member
# mypy: ignore-errors
from typing import Awaitable, Callable, Dict
from dependency_injector import containers, providers
from . import service
from ..requests.containers import RequestsContainer

sentry_pat: Callable[[Dict], str] = lambda keys: keys['SENTRY_PAT']


class SentryContainer(containers.DeclarativeContainer):
    """Sentry Container"""

    logger = providers.Dependency()
    serializer = providers.Dependency()
    keys = providers.Dependency()

    requests_container = providers.Container(
        RequestsContainer,
        logger=logger,
    )

    sentry_service: Callable[..., Awaitable[service.SentryService]] = providers.Singleton(
        service.SentryService,
        logger=logger,
        client=requests_container.requests_service,
        serializer=serializer,
        bearer=providers.Resource(sentry_pat, keys)
    )
