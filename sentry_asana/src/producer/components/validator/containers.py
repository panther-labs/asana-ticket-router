# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
# pylint: disable=no-member
# mypy: ignore-errors
import asyncio
import hmac
from hashlib import sha256
from dependency_injector import containers, providers
from . import service


class ValidatorContainer(containers.DeclarativeContainer):
    """Validator Container"""

    config = providers.Configuration(strict=True)
    logger = providers.Dependency()

    development = providers.Selector(
        config.development,  # pylint: disable=no-member
        true=providers.Factory(bool, True),
        false=providers.Factory(bool, False),
    )

    validator_service = providers.Singleton(
        service.ValidatorService,
        loop=asyncio.get_event_loop,
        logger=logger,
        development=development,
        hmac=hmac.new,
        digest=sha256,
    )
