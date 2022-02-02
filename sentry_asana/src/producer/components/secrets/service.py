# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
from asyncio import AbstractEventLoop
from typing import Optional, Dict, Callable
from logging import Logger
from functools import partial
from mypy_boto3_secretsmanager import SecretsManagerClient
from mypy_boto3_secretsmanager.type_defs import GetSecretValueResponseTypeDef
from ..serializer.service import SerializerService


class SecretsManagerService:
    """SecretsManager Service"""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        loop: Callable[[], AbstractEventLoop],
        logger: Logger,
        client: SecretsManagerClient,
        secret_name: str,
        serializer: SerializerService
    ):
        self.loop = loop
        self.logger = logger
        self.client = client
        self.secret_name = secret_name
        self.serializer = serializer
        self.key: Optional[Dict[str, str]] = None

    async def get_key(self, key: str) -> str:
        """Get the secret key"""
        if self.key is None:
            self.logger.info("Fetching key")
            self.key = await self.get_secret_string()
        else:
            self.logger.info("Returning cached key")
        return self.key[key]

    async def get_secret_string(self) -> Dict[str, str]:
        """Get the SecretString from a secret"""
        self.logger.info("Getting Sentry Client Secret")
        response = await self.get_secret()
        return self.serializer.parse(response['SecretString'])

    async def get_secret(self) -> GetSecretValueResponseTypeDef:
        """Get a secret"""
        self.logger.info("Getting AWS Secret")
        return await self.loop().run_in_executor(
            None,
            partial(
                self.client.get_secret_value,
                SecretId=self.secret_name
            )
        )
