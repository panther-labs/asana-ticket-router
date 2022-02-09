# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
# pylint: disable=no-member
# mypy: ignore-errors
import logging
import logging.config
from dependency_injector import containers, providers
from . import service


class LoggerContainer(containers.DeclarativeContainer):
    """Logger Container"""

    config = providers.Configuration(strict=True)
    logger = providers.Singleton(logging.getLogger)

    log_level = providers.Selector(
        config.common.debug,
        true=providers.Factory(int, logging.DEBUG),
        false=providers.Factory(int, logging.INFO)
    )

    logger_service = providers.Singleton(
        service.LoggerService,
        logger=logger
    )

    configure_logger = providers.Selector(
        config.common.is_lambda,
        true=providers.Callable(
            logger().setLevel,
            log_level
        ),
        false=providers.Callable(
            logging.config.dictConfig,
            config=config.logging
        )
    )
