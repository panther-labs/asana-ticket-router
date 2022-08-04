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
import hmac
from hashlib import sha256
from dependency_injector import containers, providers
from . import service

sentry_client_secret: Callable[[Dict],
                               str] = lambda keys: keys['SENTRY_CLIENT_SECRET']

datadog_secret_token: Callable[[Dict],
                               str] = lambda keys: keys['DATADOG_SECRET_TOKEN']


class ValidatorContainer(containers.DeclarativeContainer):
    """Validator Container"""

    config = providers.Configuration(strict=True)
    logger = providers.Dependency()
    keys = providers.Dependency()

    development = providers.Selector(
        config.development,
        true=providers.Factory(bool, True),
        false=providers.Factory(bool, False),
    )

    validator_service = providers.Singleton(
        service.ValidatorService,
        loop=asyncio.get_running_loop,
        logger=logger,
        development=development,
        hmac=hmac.new,
        digest=sha256,
        sentry_key=providers.Resource(sentry_client_secret, keys),
        datadog_key=providers.Resource(datadog_secret_token, keys)
    )
