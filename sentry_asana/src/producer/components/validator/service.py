# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
from asyncio import AbstractEventLoop
from typing import Callable, Any
from hmac import HMAC
from logging import Logger
from functools import partial


class ValidatorService:
    """Validator Service"""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        loop: Callable[[], AbstractEventLoop],
        logger: Logger,
        development: bool,
        hmac: Callable[..., HMAC],
        # returns private instance, so we have to use Any
        digest: Callable[..., Any],
        key: str
    ) -> None:
        self._loop = loop
        self._logger = logger
        self._development = development
        self._hmac = hmac
        self._digest = digest
        self._key = key

    async def validate(self, message: str, signature: str) -> bool:
        """Get the secret specified by the environment"""
        if self._development is True:
            self._logger.warning(
                "Development mode enabled, skipping signature validation")
            return True

        hashed = await self.hash(message)
        self._logger.debug("Validating signature %s == %s", signature, hashed)
        return signature == hashed

    async def hash(self, message: str) -> str:
        """Hash a message with a given key"""
        hashed = await self._loop().run_in_executor(
            None,
            partial(
                self._hmac,
                key=self._key.encode('utf-8'),
                msg=message.encode('utf-8'),
                digestmod=self._digest
            )
        )
        return hashed.hexdigest()
