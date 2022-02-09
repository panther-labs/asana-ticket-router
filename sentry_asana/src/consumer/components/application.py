# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
# pylint: disable=no-member
# mypy: ignore-errors
from dependency_injector import containers, providers
from common.components.logger.containers import LoggerContainer
from common.components.secrets.containers import SecretsManagerContainer
from common.components.serializer.containers import SerializerContainer
from .asana.containers import AsanaContainer
from .sentry.containers import SentryContainer


class ApplicationContainer(containers.DeclarativeContainer):
    """Consumer Application Container"""

    config = providers.Configuration(strict=True)

    # Logger
    logger_container = providers.Container(
        LoggerContainer,
        config=config
    )

    # JSON serializer
    serializer_container = providers.Container(
        SerializerContainer,
    )

    # SecretsManager
    secretsmanager_container = providers.Container(
        SecretsManagerContainer,
        logger=logger_container.logger,
        serializer=serializer_container.serializer_service,
        config=config.services.secrets,
    )

    # Sentry
    sentry_container = providers.Container(
        SentryContainer,
        logger=logger_container.logger,
        serializer=serializer_container.serializer_service,
        keys=secretsmanager_container.keys
    )

    # Asana
    asana_container = providers.Container(
        AsanaContainer,
        config=config.common,
        logger=logger_container.logger,
        serializer=serializer_container.serializer_service,
        keys=secretsmanager_container.keys
    )
