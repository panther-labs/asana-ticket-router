# Copyright (C) 2020 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.

import logging
import os

DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

LOG_FORMAT = "[%(levelname)s]\t[%(asctime)s.%(msecs)03dZ]\t[%(aws_request_id)s]\t" \
             "[%(pathname)s:%(funcName)s:%(lineno)d]\t%(message)s"


class LambdaFormatter(logging.Formatter):
    """Custom formatter for utilizing a common log format both locally and on AWS Lambda"""

    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, 'aws_request_id'):
            record.aws_request_id = '_local_'  # type: ignore[attr-defined]
        return super().format(record)


class LoggingSetup:
    """Manages logging configuration"""

    def __init__(self) -> None:
        # get_logger performs the configuration only once and always returns the same handler
        self._configured = False

    def get_logger(self) -> logging.Logger:
        """Retrieves a pre-configured logger instance"""

        logger = logging.getLogger()

        # If the logger has already been configured return the instance directly
        if self._configured:
            return logger

        level = 'DEBUG' if DEBUG else 'INFO'
        logger.setLevel(level)

        if len(logger.handlers) == 0:
            handler = logging.StreamHandler()
            logger.addHandler(handler)
            handler.setFormatter(LambdaFormatter(fmt=LOG_FORMAT))
        else:
            # AWS Lambda has its own handler preconfigured
            aws_handler: logging.Handler = logger.handlers[0]

            # Formatter.datefmt is dynamically defined in the constructor
            aws_datetime_format = aws_handler.formatter.datefmt  # type: ignore
            formatter = LambdaFormatter(fmt=LOG_FORMAT, datefmt=aws_datetime_format)
            if isinstance(aws_handler, logging.StreamHandler):
                raise RuntimeError(f"expected custom handler class (likely LambdaLoggerHandler), "
                                   f"found {type(aws_handler)} instead")
            aws_handler.setFormatter(formatter)

        # Verify that the logger works on startup
        logger.debug(
            "logger initialized successfully: total handlers=%d, first handler class: %s", len(logger.handlers),
            logger.handlers[0].__class__.__name__
        )
        self._configured = True
        return logger


_logging_setup = LoggingSetup()
get_logger = _logging_setup.get_logger
