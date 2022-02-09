# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
from logging import Logger


class LoggerService:
    """Logger Service"""

    def __init__(self, logger: Logger):
        self._logger = logger

    def get(self) -> Logger:
        """Get a handle to the logger"""
        return self._logger
