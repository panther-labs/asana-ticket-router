# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
import logging
import logging.config
from logging import Logger
from dependency_injector import containers, providers
from . import service

# pylint: disable=no-member
# mypy: ignore-errors


def config_log(logger: Logger, level: int) -> None:
    """Configures a given logger to a logging level"""
    logger.setLevel(level)


class LoggerContainer(containers.DeclarativeContainer):
    """Logger Container"""

    config = providers.Configuration(strict=True)
    logger = providers.Singleton(
        logging.getLogger
    )

    log_level = providers.Selector(
        config.common.debug,
        true=providers.Factory(int, logging.DEBUG),
        false=providers.Factory(int, logging.INFO)
    )
    configure_logger = providers.Selector(
        config.common.is_lambda,
        true=providers.Callable(
            config_log,
            logger,
            log_level
        ),
        false=providers.Callable(
            logging.config.dictConfig,
            config=config.logging
        )
    )

    logger_service = providers.Singleton(
        service.LoggerService,
        logger=logger
    )
