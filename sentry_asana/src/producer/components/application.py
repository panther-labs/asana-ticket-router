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
from common.components.metrics.containers import MetricsContainer
from common.components.secrets.containers import SecretsManagerContainer
from common.components.serializer.containers import SerializerContainer
from .queue.containers import QueueContainer
from .validator.containers import ValidatorContainer


class ApplicationContainer(containers.DeclarativeContainer):
    """Producer Application Container"""

    config = providers.Configuration(strict=True)

    # Logger
    logger_container = providers.Container(LoggerContainer, config=config)

    # JSON serializer
    serializer_container = providers.Container(
        SerializerContainer,
    )

    # SQS
    queue_container = providers.Container(
        QueueContainer, logger=logger_container.logger, config=config.services.sqs
    )

    # SecretsManager
    secretsmanager_container = providers.Container(
        SecretsManagerContainer,
        logger=logger_container.logger,
        serializer=serializer_container.serializer_service,
        config=config.services.secrets,
    )

    # metrics
    metrics_container = providers.Container(MetricsContainer)

    # Payload Validator
    validator_container = providers.Container(
        ValidatorContainer,
        logger=logger_container.logger,
        config=config.common,
        keys=secretsmanager_container.keys,
    )
