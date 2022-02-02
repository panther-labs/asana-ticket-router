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
        digest: Callable[..., Any]
    ) -> None:
        self.loop = loop
        self.logger = logger
        self.development = development
        self.hmac = hmac
        self.digest = digest

    async def validate(self, message: str, signature: str, key: str) -> bool:
        """Get the secret specified by the environment"""
        if self.development is True:
            self.logger.info(
                "Development mode enabled, skipping signature validation")
            return True

        hashed = await self.hash(message, key)
        self.logger.debug("Validating signature %s == %s", signature, hashed)
        return signature == hashed

    async def hash(self, message: str, key: str) -> str:
        """Hash a message with a given key"""
        hashed = await self.loop().run_in_executor(
            None,
            partial(
                self.hmac,
                key=key.encode('utf-8'),
                msg=message.encode('utf-8'),
                digestmod=self.digest
            )
        )
        return hashed.hexdigest()
